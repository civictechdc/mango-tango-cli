#!/usr/bin/env python3
"""
Performance Test Runner for Chunking Optimization

Provides convenient ways to run performance tests with appropriate configurations
and generate performance reports.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List

import psutil
import pytest


def get_system_info() -> Dict[str, any]:
    """Get system information for test context."""
    memory = psutil.virtual_memory()
    return {
        "total_memory_gb": memory.total / 1024**3,
        "available_memory_gb": memory.available / 1024**3,
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": psutil.cpu_freq().max if psutil.cpu_freq() else None,
        "python_version": sys.version.split()[0],
    }


def print_system_info():
    """Print system information."""
    info = get_system_info()
    print("=== System Information ===")
    print(f"Total RAM: {info['total_memory_gb']:.1f} GB")
    print(f"Available RAM: {info['available_memory_gb']:.1f} GB")
    print(f"CPU Cores: {info['cpu_count']}")
    if info["cpu_freq"]:
        print(f"CPU Frequency: {info['cpu_freq']:.0f} MHz")
    print(f"Python Version: {info['python_version']}")
    print()


def run_validation_tests() -> bool:
    """Run core validation tests (fast)."""
    print("=== Running Core Validation Tests ===")

    args = [
        "testing/performance/test_chunking_optimization.py",
        "-v",
        "--tb=short",
        "-k",
        "not benchmark and not stress and not comprehensive",
    ]

    result = pytest.main(args)
    return result == 0


def run_performance_benchmarks() -> bool:
    """Run performance benchmark tests."""
    print("=== Running Performance Benchmarks ===")

    system_info = get_system_info()
    if system_info["total_memory_gb"] < 8:
        print("WARNING: System has less than 8GB RAM. Some benchmarks may be skipped.")
        print()

    args = [
        "testing/performance/test_performance_benchmarks.py",
        "-v",
        "--tb=short",
        "-s",  # Show output from benchmarks
        "--durations=10",  # Show slowest 10 tests
    ]

    result = pytest.main(args)
    return result == 0


def run_full_suite() -> bool:
    """Run the complete performance test suite."""
    print("=== Running Full Performance Test Suite ===")

    args = ["testing/performance/", "-v", "--tb=short", "-s", "--durations=15"]

    result = pytest.main(args)
    return result == 0


def run_specific_phase(phase: str) -> bool:
    """Run tests for a specific optimization phase."""
    phase_keywords = {
        "1": "memory_detection or auto_detection",
        "2": "adaptive_chunk",
        "3": "fallback",
        "4": "secondary_analyzer or ngram_stats",
        "5": "validation or benchmark",
    }

    if phase not in phase_keywords:
        print(f"Invalid phase: {phase}. Must be 1-5.")
        return False

    print(f"=== Running Phase {phase} Tests ===")

    args = ["testing/performance/", "-v", "--tb=short", "-k", phase_keywords[phase]]

    result = pytest.main(args)
    return result == 0


def run_memory_specific_tests() -> bool:
    """Run tests specific to current system's memory configuration."""
    system_info = get_system_info()
    memory_gb = system_info["total_memory_gb"]

    print(f"=== Running Tests for {memory_gb:.1f}GB System ===")

    if memory_gb >= 32:
        print("High-memory system detected. Running comprehensive tests.")
        test_filter = "not stress"  # Skip stress tests unless explicitly requested
    elif memory_gb >= 16:
        print("Standard-memory system detected. Running standard tests.")
        test_filter = "not stress and not large_dataset"
    elif memory_gb >= 8:
        print("Lower-memory system detected. Running basic tests.")
        test_filter = "not stress and not large_dataset and not comprehensive"
    else:
        print("Constrained-memory system detected. Running minimal tests.")
        test_filter = (
            "not stress and not large_dataset and not comprehensive and not benchmark"
        )

    args = ["testing/performance/", "-v", "--tb=short", "-k", test_filter]

    result = pytest.main(args)
    return result == 0


def generate_performance_report():
    """Generate a performance test report."""
    print("=== Generating Performance Report ===")

    system_info = get_system_info()

    # Run tests with detailed output
    report_file = Path("performance_test_report.txt")

    args = [
        "testing/performance/",
        "-v",
        "--tb=short",
        "-s",
        "--durations=20",
        f"--html=performance_report.html",  # If pytest-html is available
        "--self-contained-html",
    ]

    print(f"Running tests and generating report...")
    start_time = time.time()
    result = pytest.main(args)
    end_time = time.time()

    # Create text report
    with open(report_file, "w") as f:
        f.write("Performance Test Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Test Time: {end_time - start_time:.1f} seconds\n\n")

        f.write("System Information:\n")
        f.write("-" * 20 + "\n")
        for key, value in system_info.items():
            f.write(f"{key}: {value}\n")
        f.write("\n")

        f.write("Test Results:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Overall Result: {'PASSED' if result == 0 else 'FAILED'}\n")
        f.write("\nSee performance_report.html for detailed results (if available).\n")

    print(f"Report saved to: {report_file}")
    if Path("performance_report.html").exists():
        print(f"HTML report saved to: performance_report.html")

    return result == 0


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Run performance tests for chunking optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_performance_tests.py --validate     # Quick validation tests
  python run_performance_tests.py --benchmark    # Performance benchmarks  
  python run_performance_tests.py --full         # Complete test suite
  python run_performance_tests.py --phase 2      # Phase 2 tests only
  python run_performance_tests.py --memory       # Tests for current system
  python run_performance_tests.py --report       # Generate performance report
        """,
    )

    parser.add_argument(
        "--validate", action="store_true", help="Run core validation tests (fast)"
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Run performance benchmark tests"
    )
    parser.add_argument(
        "--full", action="store_true", help="Run complete performance test suite"
    )
    parser.add_argument(
        "--phase",
        choices=["1", "2", "3", "4", "5"],
        help="Run tests for specific optimization phase",
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Run tests appropriate for current system memory",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive performance report",
    )
    parser.add_argument(
        "--info", action="store_true", help="Show system information and exit"
    )

    args = parser.parse_args()

    # Show system info if requested or for any test run
    if args.info:
        print_system_info()
        return 0

    if not any(
        [args.validate, args.benchmark, args.full, args.phase, args.memory, args.report]
    ):
        parser.print_help()
        return 1

    print_system_info()
    success = True

    try:
        if args.validate:
            success &= run_validation_tests()

        if args.benchmark:
            success &= run_performance_benchmarks()

        if args.full:
            success &= run_full_suite()

        if args.phase:
            success &= run_specific_phase(args.phase)

        if args.memory:
            success &= run_memory_specific_tests()

        if args.report:
            success &= generate_performance_report()

    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        return 130
    except Exception as e:
        print(f"\nError running tests: {e}")
        return 1

    print("\n" + "=" * 50)
    if success:
        print("✅ All tests completed successfully!")
        return 0
    else:
        print("❌ Some tests failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
