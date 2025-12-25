#!/usr/bin/env python
"""Test script for multi-column display functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from r9s.cli_tools.cli import print_options_multi_column

print("=== Test 1: Small list (5 items) - Should use single column ===")
small_list = [f"model-{i}" for i in range(1, 6)]
print_options_multi_column(small_list)

print("\n=== Test 2: Medium list (15 items) - Column-major order ===")
print("Expected: 1-5 in first column, 6-10 in second, 11-15 in third")
medium_list = [f"qwen-model-{i:02d}" for i in range(1, 16)]
print_options_multi_column(medium_list)

print("\n=== Test 3: Large list (30 items) - Column-major order ===")
print("Expected: 1-10 in first column, 11-20 in second, 21-30 in third")
large_list = [f"model-name-{i:02d}" for i in range(1, 31)]
print_options_multi_column(large_list)

print("\n=== Test 4: Very long model names ===")
long_names = [
    f"very-long-model-name-version-{i:02d}-extended" for i in range(1, 16)
]
print_options_multi_column(long_names)

print("\n=== Test 5: 13 items (uneven distribution) ===")
print("Expected: 1-5 in first column, 6-10 in second, 11-13 in third")
uneven_list = [f"model-{i}" for i in range(1, 14)]
print_options_multi_column(uneven_list)

print("\n✅ All tests completed!")
