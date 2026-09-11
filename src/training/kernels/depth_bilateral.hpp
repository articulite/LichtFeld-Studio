/* SPDX-FileCopyrightText: 2025 LichtFeld Studio Authors
 *
 * SPDX-License-Identifier: GPL-3.0-or-later */

#pragma once

#include <cuda_runtime.h>

namespace lfs::training::kernels {

    void launch_depth_bilateral_forward(
        const float* __restrict__ rgb,
        const float* __restrict__ depth,
        float* __restrict__ output_rgb,
        float* __restrict__ weight_sums,
        int width,
        int height,
        int radius,
        float sigma_s,
        float sigma_d,
        cudaStream_t stream = nullptr);

    void launch_depth_bilateral_backward(
        const float* __restrict__ grad_output,
        const float* __restrict__ depth,
        const float* __restrict__ weight_sums,
        float* __restrict__ grad_input,
        int width,
        int height,
        int radius,
        float sigma_s,
        float sigma_d,
        cudaStream_t stream = nullptr);

} // namespace lfs::training::kernels
