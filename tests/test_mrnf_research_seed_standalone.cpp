#include "src/training/strategies/mrnf_research_seed.hpp"
#include <iostream>
#include <limits>

int main() {
    using namespace lfs::training::mrnf_research_seed;
    if (parse(nullptr) || parse("0") != 0 || parse("18446744073709551615") != std::numeric_limits<uint64_t>::max()) return 1;
    for (auto value : {"", "-1", "+1", "1x", " 1", "18446744073709551616"}) {
        bool rejected = false;
        try { (void)parse(value); } catch (const std::runtime_error&) { rejected = true; }
        if (!rejected) return 2;
    }
    auto first = next("42", 200 ^ 0x4d524e465f47524fULL);
    (void)next("43", 201);
    if (first != next("42", 200 ^ 0x4d524e465f47524fULL)) return 3;
    if (first == next("43", 200 ^ 0x4d524e465f47524fULL)) return 4;
    if (first == next("42", 201 ^ 0x4d524e465f47524fULL)) return 5;
    if (first == next("42", 200 ^ 0x4d524e465f4e4f49ULL)) return 6;
    if (!next(nullptr, 0)) return 7;
    std::cout << "seed parser and operation/iteration reproducibility passed\n";
}
