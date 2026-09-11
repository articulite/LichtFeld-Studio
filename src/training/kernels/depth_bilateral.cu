/* SPDX-FileCopyrightText: 2025 LichtFeld Studio Authors
 *
 * SPDX-License-Identifier: GPL-3.0-or-later */

#include "depth_bilateral.hpp"
#include "core/cuda_error.hpp"

#include <cmath>
#include <cstdint>
#include <device_launch_parameters.h>

namespace lfs::training::kernels {

    namespace {

        __global__ void depth_bilateral_forward_kernel(
            const float* __restrict__ rgb,
            const float* __restrict__ depth,
            float* __restrict__ output_rgb,
            float* __restrict__ weight_sums,
            const int width,
            const int height,
            const int radius,
            const float inv_two_sigma_s_sq,
            const float inv_two_sigma_d_sq) {

            const int x = blockIdx.x * blockDim.x + threadIdx.x;
            const int y = blockIdx.y * blockDim.y + threadIdx.y;

            if (x >= width || y >= height) {
                return;
            }

            const int idx = y * width + x;
            const int n_pixels = width * height;

            const float center_d = depth[idx];
            const float center_r = rgb[idx];
            const float center_g = rgb[idx + n_pixels];
            const float center_b = rgb[idx + 2 * n_pixels];

            if (center_d <= 1e-6f || !isfinite(center_d)) {
                output_rgb[idx] = center_r;
                output_rgb[idx + n_pixels] = center_g;
                output_rgb[idx + 2 * n_pixels] = center_b;
                if (weight_sums != nullptr) {
                    weight_sums[idx] = 1.0f;
                }
                return;
            }

            float sum_w = 0.0f;
            float sum_r = 0.0f;
            float sum_g = 0.0f;
            float sum_b = 0.0f;

            for (int dy = -radius; dy <= radius; ++dy) {
                const int ny = y + dy;
                if (ny < 0 || ny >= height) {
                    continue;
                }

                for (int dx = -radius; dx <= radius; ++dx) {
                    const int nx = x + dx;
                    if (nx < 0 || nx >= width) {
                        continue;
                    }

                    const int n_idx = ny * width + nx;
                    const float neighbor_d = depth[n_idx];

                    if (neighbor_d <= 1e-6f || !isfinite(neighbor_d)) {
                        continue;
                    }

                    const float dist_sq = static_cast<float>(dx * dx + dy * dy);
                    const float spatial_w = __expf(-dist_sq * inv_two_sigma_s_sq);

                    const float depth_diff = fabsf(center_d - neighbor_d) / center_d;
                    const float depth_w = __expf(-depth_diff * depth_diff * inv_two_sigma_d_sq);

                    const float w = spatial_w * depth_w;

                    sum_w += w;
                    sum_r += w * rgb[n_idx];
                    sum_g += w * rgb[n_idx + n_pixels];
                    sum_b += w * rgb[n_idx + 2 * n_pixels];
                }
            }

            if (sum_w > 1e-8f) {
                const float inv_w = 1.0f / sum_w;
                output_rgb[idx] = sum_r * inv_w;
                output_rgb[idx + n_pixels] = sum_g * inv_w;
                output_rgb[idx + 2 * n_pixels] = sum_b * inv_w;
                if (weight_sums != nullptr) {
                    weight_sums[idx] = sum_w;
                }
            } else {
                output_rgb[idx] = center_r;
                output_rgb[idx + n_pixels] = center_g;
                output_rgb[idx + 2 * n_pixels] = center_b;
                if (weight_sums != nullptr) {
                    weight_sums[idx] = 1.0f;
                }
            }
        }

        __global__ void depth_bilateral_backward_kernel(
            const float* __restrict__ grad_output,
            const float* __restrict__ depth,
            const float* __restrict__ weight_sums,
            float* __restrict__ grad_input,
            const int width,
            const int height,
            const int radius,
            const float inv_two_sigma_s_sq,
            const float inv_two_sigma_d_sq) {

            const int x = blockIdx.x * blockDim.x + threadIdx.x;
            const int y = blockIdx.y * blockDim.y + threadIdx.y;

            if (x >= width || y >= height) {
                return;
            }

            const int q_idx = y * width + x;
            const int n_pixels = width * height;

            const float d_q = depth[q_idx];

            if (d_q <= 1e-6f || !isfinite(d_q)) {
                grad_input[q_idx] = grad_output[q_idx];
                grad_input[q_idx + n_pixels] = grad_output[q_idx + n_pixels];
                grad_input[q_idx + 2 * n_pixels] = grad_output[q_idx + 2 * n_pixels];
                return;
            }

            float grad_r = 0.0f;
            float grad_g = 0.0f;
            float grad_b = 0.0f;

            for (int dy = -radius; dy <= radius; ++dy) {
                const int py = y + dy;
                if (py < 0 || py >= height) {
                    continue;
                }

                for (int dx = -radius; dx <= radius; ++dx) {
                    const int px = x + dx;
                    if (px < 0 || px >= width) {
                        continue;
                    }

                    const int p_idx = py * width + px;
                    const float d_p = depth[p_idx];
                    const float s_p = weight_sums != nullptr ? weight_sums[p_idx] : 1.0f;

                    if (d_p <= 1e-6f || !isfinite(d_p) || s_p <= 1e-8f) {
                        continue;
                    }

                    const float dist_sq = static_cast<float>(dx * dx + dy * dy);
                    const float spatial_w = __expf(-dist_sq * inv_two_sigma_s_sq);

                    const float depth_diff = fabsf(d_p - d_q) / d_p;
                    const float depth_w = __expf(-depth_diff * depth_diff * inv_two_sigma_d_sq);

                    const float w = spatial_w * depth_w;
                    const float coeff = w / s_p;

                    grad_r += coeff * grad_output[p_idx];
                    grad_g += coeff * grad_output[p_idx + n_pixels];
                    grad_b += coeff * grad_output[p_idx + 2 * n_pixels];
                }
            }

            grad_input[q_idx] = grad_r;
            grad_input[q_idx + n_pixels] = grad_g;
            grad_input[q_idx + 2 * n_pixels] = grad_b;
        }

    } // namespace

    void launch_depth_bilateral_forward(
        const float* __restrict__ rgb,
        const float* __restrict__ depth,
        float* __restrict__ output_rgb,
        float* __restrict__ weight_sums,
        const int width,
        const int height,
        const int radius,
        const float sigma_s,
        const float sigma_d,
        cudaStream_t stream) {

        if (width <= 0 || height <= 0) return;

        const float inv_two_sigma_s_sq = 1.0f / (2.0f * sigma_s * sigma_s + 1e-8f);
        const float inv_two_sigma_d_sq = 1.0f / (2.0f * sigma_d * sigma_d + 1e-8f);

        dim3 block(16, 16);
        dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);

        depth_bilateral_forward_kernel<<<grid, block, 0, stream>>>(
            rgb, depth, output_rgb, weight_sums, width, height, radius,
            inv_two_sigma_s_sq, inv_two_sigma_d_sq);
        LFS_CUDA_LAUNCH_CHECK(stream, "depth_bilateral_forward");
    }

    void launch_depth_bilateral_backward(
        const float* __restrict__ grad_output,
        const float* __restrict__ depth,
        const float* __restrict__ weight_sums,
        float* __restrict__ grad_input,
        const int width,
        const int height,
        const int radius,
        const float sigma_s,
        const float sigma_d,
        cudaStream_t stream) {

        if (width <= 0 || height <= 0) return;

        const float inv_two_sigma_s_sq = 1.0f / (2.0f * sigma_s * sigma_s + 1e-8f);
        const float inv_two_sigma_d_sq = 1.0f / (2.0f * sigma_d * sigma_d + 1e-8f);

        dim3 block(16, 16);
        dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);

        depth_bilateral_backward_kernel<<<grid, block, 0, stream>>>(
            grad_output, depth, weight_sums, grad_input, width, height, radius,
            inv_two_sigma_s_sq, inv_two_sigma_d_sq);
        LFS_CUDA_LAUNCH_CHECK(stream, "depth_bilateral_backward");
    }

} // namespace lfs::training::kernels
