#!/usr/bin/env python3
"""
Script to run tests with proper environment setup.
"""
import os
import subprocess
import sys

def main():
    # Set testing environment
    os.environ['TESTING'] = 'true'
    
    # Try to use poetry first, fallback to system python
    try:
        result = subprocess.run([
            'poetry', 'run', 'pytest', 
            'tests/', 
            '-v', 
            '--tb=short'
        ], cwd=os.path.dirname(__file__))
    except FileNotFoundError:
        # Fallback to system python if poetry is not available
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v', 
            '--tb=short'
        ], cwd=os.path.dirname(__file__))
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
