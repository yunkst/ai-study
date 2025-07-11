#!/usr/bin/env python3
"""
Test runner script for the knowledge management system
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def run_unit_tests():
    """Run unit tests"""
    cmd = "python -m pytest tests/test_*.py -m 'not integration' -v"
    return run_command(cmd, "Unit Tests")

def run_integration_tests():
    """Run integration tests"""
    cmd = "python -m pytest tests/test_integration_*.py -m integration -v"
    return run_command(cmd, "Integration Tests")

def run_api_tests():
    """Run API tests"""
    cmd = "python -m pytest tests/test_api_*.py -m api -v"
    return run_command(cmd, "API Tests")

def run_service_tests():
    """Run service tests"""
    cmd = "python -m pytest tests/test_services_*.py -v"
    return run_command(cmd, "Service Tests")

def run_model_tests():
    """Run model tests"""
    cmd = "python -m pytest tests/test_models_*.py -v"
    return run_command(cmd, "Model Tests")

def run_all_tests():
    """Run all tests with coverage"""
    cmd = "python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-report=xml"
    return run_command(cmd, "All Tests with Coverage")

def run_coverage_only():
    """Generate coverage report without running tests"""
    cmd = "python -m coverage report -m"
    return run_command(cmd, "Coverage Report")

def run_performance_tests():
    """Run performance tests"""
    cmd = "python -m pytest tests/ -m performance -v --durations=10"
    return run_command(cmd, "Performance Tests")

def run_specific_test(test_path):
    """Run a specific test file or function"""
    cmd = f"python -m pytest {test_path} -v"
    return run_command(cmd, f"Specific Test: {test_path}")

def generate_test_summary():
    """Generate a comprehensive test summary"""
    print(f"\n{'='*80}")
    print("TEST SUMMARY REPORT")
    print(f"{'='*80}")
    
    # Count test files
    test_files = list(Path("tests").glob("test_*.py"))
    print(f"Total test files: {len(test_files)}")
    
    for test_file in sorted(test_files):
        print(f"  - {test_file.name}")
    
    # Run pytest with collection only to count tests
    try:
        result = subprocess.run(
            "python -m pytest tests/ --collect-only -q",
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            test_count_line = [line for line in lines if 'test' in line and 'collected' in line]
            if test_count_line:
                print(f"\n{test_count_line[-1]}")
    except Exception as e:
        print(f"Could not count tests: {e}")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run tests for Knowledge Management System")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--services", action="store_true", help="Run service tests only")
    parser.add_argument("--models", action="store_true", help="Run model tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report only")
    parser.add_argument("--summary", action="store_true", help="Generate test summary")
    parser.add_argument("--file", type=str, help="Run specific test file")
    parser.add_argument("--function", type=str, help="Run specific test function")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    args = parser.parse_args()
    
    # Change to the backend directory
    os.chdir(Path(__file__).parent)
    
    success = True
    
    if args.summary:
        generate_test_summary()
        return
    
    if args.unit:
        success &= run_unit_tests()
    elif args.integration:
        success &= run_integration_tests()
    elif args.api:
        success &= run_api_tests()
    elif args.services:
        success &= run_service_tests()
    elif args.models:
        success &= run_model_tests()
    elif args.performance:
        success &= run_performance_tests()
    elif args.coverage:
        success &= run_coverage_only()
    elif args.file:
        test_path = args.file
        if args.function:
            test_path += f"::{args.function}"
        success &= run_specific_test(test_path)
    else:
        # Run all tests by default
        print("Running comprehensive test suite...")
        success &= run_all_tests()
        
        if success:
            print(f"\n{'='*60}")
            print("GENERATING DETAILED COVERAGE REPORT")
            print(f"{'='*60}")
            run_coverage_only()
            
            print(f"\n{'='*60}")
            print("TEST EXECUTION COMPLETED SUCCESSFULLY!")
            print(f"{'='*60}")
            print("Coverage reports generated:")
            print("  - Terminal: see above")
            print("  - HTML: htmlcov/index.html")
            print("  - XML: coverage.xml")
        else:
            print(f"\n{'='*60}")
            print("SOME TESTS FAILED!")
            print(f"{'='*60}")
    
    # Generate summary at the end
    if not args.coverage and not args.summary:
        generate_test_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 