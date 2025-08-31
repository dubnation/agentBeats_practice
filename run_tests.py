#!/usr/bin/env python3
"""
Test runner script for AgentBeats Practice project.

This script provides an easy way to run all tests with different options.
"""

import subprocess
import sys
import os


def run_command(command):
    """Run a command and return the result"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main test runner function"""
    print("AgentBeats Practice - Test Runner")
    print("=" * 40)
    
    # Check if pytest is installed
    if not run_command("python -c 'import pytest'"):
        print("pytest not found. Installing test dependencies...")
        if not run_command("pip install -r requirements.txt"):
            print("Failed to install dependencies. Please install manually:")
            print("pip install -r requirements.txt")
            return 1
    
    # Test options
    test_options = {
        "1": ("Basic tests", "pytest test_agent_executor.py -v"),
        "2": ("Tests with coverage", "pytest test_agent_executor.py --cov=agent_executor --cov-report=html"),
        "3": ("Tests with coverage (terminal)", "pytest test_agent_executor.py --cov=agent_executor --cov-report=term"),
        "4": ("Run specific test class", "pytest test_agent_executor.py::TestOllamaModel -v"),
        "5": ("Run all tests in quiet mode", "pytest test_agent_executor.py -q"),
        "6": ("Run tests and generate XML report", "pytest test_agent_executor.py --junit-xml=test-results.xml"),
    }
    
    print("\nAvailable test options:")
    for key, (description, _) in test_options.items():
        print(f"{key}. {description}")
    
    print("\nOther options:")
    print("m. Run manual tests (requires Ollama)")
    print("q. Quit")
    
    choice = input("\nSelect an option: ").strip().lower()
    
    if choice == 'q':
        return 0
    elif choice == 'm':
        print("\nRunning manual tests...")
        return run_command("python test_agent_executor.py")
    elif choice in test_options:
        description, command = test_options[choice]
        print(f"\n{description}...")
        success = run_command(command)
        
        if choice == "2" and success:
            print("\nHTML coverage report generated in htmlcov/ directory")
            print("Open htmlcov/index.html in your browser to view the report")
            
        return 0 if success else 1
    else:
        print("Invalid option selected")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
