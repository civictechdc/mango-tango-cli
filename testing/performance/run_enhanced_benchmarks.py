#!/usr/bin/env python3
"""
Enhanced Performance Test Runner
Demonstrates the new robust testing approach using pytest-benchmark and resource-based metrics.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_basic_performance_tests():
    """Run basic performance tests with adjusted thresholds."""
    print("🔍 Running basic performance tests with realistic thresholds...")
    cmd = [
        "pytest",
        "testing/performance/test_performance_benchmarks.py",
        "-v",
        "-m",
        "performance",
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Basic performance tests passed!")
    else:
        print("❌ Basic performance tests failed:")
        print(result.stdout)
        print(result.stderr)

    return result.returncode == 0


def run_enhanced_benchmarks():
    """Run enhanced pytest-benchmark tests."""
    print("📊 Running enhanced pytest-benchmark tests...")
    cmd = [
        "pytest",
        "testing/performance/test_enhanced_benchmarks.py",
        "-v",
        "-m",
        "benchmark",
        "--benchmark-enable",
        "--benchmark-verbose",
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Enhanced benchmark tests passed!")
    else:
        print("❌ Enhanced benchmark tests failed:")
        print(result.stdout)
        print(result.stderr)

    return result.returncode == 0


def run_deterministic_tests():
    """Run deterministic resource-based tests."""
    print("⚡ Running deterministic I/O and memory tests...")
    cmd = [
        "pytest",
        "testing/performance/test_enhanced_benchmarks.py::TestEnhancedPerformanceBenchmarks::test_chunk_efficiency_invariant",
        "testing/performance/test_enhanced_benchmarks.py::TestEnhancedPerformanceBenchmarks::test_memory_efficiency_bounds",
        "testing/performance/test_enhanced_benchmarks.py::TestEnhancedPerformanceBenchmarks::test_io_operation_counting_deterministic",
        "-v",
        "-m",
        "",  # Override default marker filtering
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Deterministic tests passed!")
    else:
        print("❌ Deterministic tests failed:")
        print(result.stdout)
        print(result.stderr)

    return result.returncode == 0


def run_property_based_tests():
    """Run property-based scaling tests."""
    print("🧪 Running property-based chunk scaling tests...")
    cmd = [
        "pytest",
        "testing/performance/test_enhanced_benchmarks.py::TestEnhancedPerformanceBenchmarks::test_chunk_size_scaling_properties",
        "-v",
        "-m",
        "",  # Override default marker filtering
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Property-based tests passed!")
    else:
        print("❌ Property-based tests failed:")
        print(result.stdout)
        print(result.stderr)

    return result.returncode == 0


def run_variance_analysis():
    """Run variance analysis tests."""
    print("📈 Running variance analysis tests...")
    cmd = [
        "pytest",
        "testing/performance/test_enhanced_benchmarks.py::TestEnhancedPerformanceBenchmarks::test_chunk_processing_variance_analysis",
        "-v",
        "-m",
        "",  # Override default marker filtering
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Variance analysis tests passed!")
    else:
        print("❌ Variance analysis tests failed:")
        print(result.stdout)
        print(result.stderr)

    return result.returncode == 0


def run_benchmark_comparison():
    """Run benchmark comparison with results saving."""
    print("🏆 Running benchmark comparison tests...")
    cmd = [
        "pytest",
        "testing/performance/test_enhanced_benchmarks.py::TestEnhancedPerformanceBenchmarks::test_chunk_processing_benchmark_small",
        "testing/performance/test_enhanced_benchmarks.py::TestEnhancedPerformanceBenchmarks::test_chunk_processing_benchmark_medium",
        "-v",
        "-m",
        "",  # Override default marker filtering
        "--benchmark-enable",
        "--benchmark-autosave",
        "--benchmark-verbose",
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Benchmark comparison tests passed!")
        print("💾 Benchmark results saved for future comparison")
    else:
        print("❌ Benchmark comparison tests failed:")
        print(result.stdout)
        print(result.stderr)

    return result.returncode == 0


def demonstrate_flaky_test_detection():
    """Demonstrate detection of flaky tests by running multiple times."""
    print("🔄 Demonstrating test reliability by running tests multiple times...")

    # Run deterministic tests multiple times - should always pass
    success_count = 0
    total_runs = 5

    for i in range(total_runs):
        print(f"  Run {i+1}/{total_runs}...")
        cmd = [
            "pytest",
            "testing/performance/test_enhanced_benchmarks.py::TestEnhancedPerformanceBenchmarks::test_chunk_efficiency_invariant",
            "-q",
            "-m",
            "",  # Override default marker filtering
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            success_count += 1

    success_rate = success_count / total_runs * 100
    print(
        f"📊 Deterministic test success rate: {success_rate:.1f}% ({success_count}/{total_runs})"
    )

    if success_rate >= 95:
        print("✅ Tests are reliable (>95% success rate)")
        return True
    else:
        print("❌ Tests are flaky (<95% success rate)")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Enhanced Performance Test Runner")
    parser.add_argument(
        "--basic", action="store_true", help="Run basic performance tests"
    )
    parser.add_argument(
        "--benchmarks", action="store_true", help="Run pytest-benchmark tests"
    )
    parser.add_argument(
        "--deterministic", action="store_true", help="Run deterministic tests"
    )
    parser.add_argument(
        "--property", action="store_true", help="Run property-based tests"
    )
    parser.add_argument("--variance", action="store_true", help="Run variance analysis")
    parser.add_argument(
        "--comparison", action="store_true", help="Run benchmark comparison"
    )
    parser.add_argument(
        "--reliability", action="store_true", help="Test reliability demonstration"
    )
    parser.add_argument("--all", action="store_true", help="Run all test categories")

    args = parser.parse_args()

    if not any(
        [
            args.basic,
            args.benchmarks,
            args.deterministic,
            args.property,
            args.variance,
            args.comparison,
            args.reliability,
            args.all,
        ]
    ):
        args.all = True  # Default to running all tests

    print("🚀 Enhanced Performance Testing Suite")
    print("=" * 50)

    results = []

    if args.all or args.basic:
        results.append(("Basic Performance Tests", run_basic_performance_tests()))

    if args.all or args.deterministic:
        results.append(("Deterministic Tests", run_deterministic_tests()))

    if args.all or args.property:
        results.append(("Property-Based Tests", run_property_based_tests()))

    if args.all or args.variance:
        results.append(("Variance Analysis", run_variance_analysis()))

    if args.all or args.benchmarks:
        results.append(("Enhanced Benchmarks", run_enhanced_benchmarks()))

    if args.all or args.comparison:
        results.append(("Benchmark Comparison", run_benchmark_comparison()))

    if args.all or args.reliability:
        results.append(
            ("Reliability Demonstration", demonstrate_flaky_test_detection())
        )

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed_tests}/{total_tests} test categories passed")

    if passed_tests == total_tests:
        print("🎉 All enhanced performance tests are working correctly!")
        print("\n💡 Key Benefits Demonstrated:")
        print("  • Eliminated flaky time-based failures")
        print("  • Statistical rigor with pytest-benchmark")
        print("  • Deterministic resource-based metrics")
        print("  • Property-based testing for edge cases")
        print("  • Variance analysis for reliability validation")
        return 0
    else:
        print("⚠️  Some test categories failed - see details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
