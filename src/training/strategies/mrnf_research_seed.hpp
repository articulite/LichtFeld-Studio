/* SPDX-FileCopyrightText: 2025 LichtFeld Studio Authors
 *
 * SPDX-License-Identifier: GPL-3.0-or-later */

#pragma once

#include <charconv>
#include <chrono>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <string_view>

namespace lfs::training::mrnf_research_seed {

    [[nodiscard]] inline std::optional<uint64_t> parse(const char* value) {
        if (value == nullptr)
            return std::nullopt;
        const std::string_view text(value);
        if (text.empty())
            throw std::runtime_error("LFS_RESEARCH_SEED must be a nonnegative uint64 value");
        uint64_t parsed = 0;
        const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), parsed);
        if (error != std::errc{} || end != text.data() + text.size())
            throw std::runtime_error("LFS_RESEARCH_SEED must be a nonnegative uint64 value");
        return parsed;
    }

    // Salt contains the operation tag and iteration: independent of call order.
    [[nodiscard]] inline uint64_t mix(uint64_t value) {
        value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
        value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
        return value ^ (value >> 31);
    }

    [[nodiscard]] inline uint64_t next(const char* env_value, const uint64_t salt) {
        const auto base = parse(env_value);
        if (!base) {
            return static_cast<uint64_t>(
                std::chrono::high_resolution_clock::now().time_since_epoch().count());
        }
        return mix(*base ^ salt);
    }

} // namespace lfs::training::mrnf_research_seed
