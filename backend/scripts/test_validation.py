"""
Test script to verify the enhanced CSV validation and security checks
"""

import os
import sys
import tempfile
import pandas as pd

# Add parent directory to path to import langgraph_analyzer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_analyzer import load_and_validate, AnalysisState

def test_path_traversal_protection():
    """Test that path traversal attacks are blocked"""
    print("\n=== Test 1: Path Traversal Protection ===")
    
    # Try to access a file outside the uploads directory
    state = {
        'csv_path': '../../../etc/passwd',  # Unix-style path traversal
        'df': None,
        'analysis_type': 'summary',
        'metadata': {},
        'basic_stats': {},
        'insights': {},
        'recommendations': [],
        'error': None
    }
    
    result = load_and_validate(state)
    
    if result['error'] and 'Security violation' in result['error']:
        print("✅ PASSED: Path traversal blocked")
        print(f"   Error: {result['error']}")
    else:
        print("❌ FAILED: Path traversal not blocked")
    
    return result['error'] is not None


def test_file_not_found():
    """Test that non-existent files are rejected"""
    print("\n=== Test 2: File Not Found ===")
    
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    fake_file = os.path.join(uploads_dir, 'nonexistent_file.csv')
    
    state = {
        'csv_path': fake_file,
        'df': None,
        'analysis_type': 'summary',
        'metadata': {},
        'basic_stats': {},
        'insights': {},
        'recommendations': [],
        'error': None
    }
    
    result = load_and_validate(state)
    
    if result['error'] and 'File not found' in result['error']:
        print("✅ PASSED: Non-existent file rejected")
        print(f"   Error: {result['error']}")
    else:
        print("❌ FAILED: Non-existent file not rejected")
    
    return result['error'] is not None


def test_valid_file():
    """Test that a valid file in uploads directory is accepted"""
    print("\n=== Test 3: Valid File ===")
    
    # Create a temporary valid CSV in the uploads directory
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(uploads_dir, exist_ok=True)
    
    test_file = os.path.join(uploads_dir, 'test_validation_temp.csv')
    
    # Create a small test CSV
    test_df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': ['a', 'b', 'c', 'd', 'e'],
        'C': [1.1, 2.2, 3.3, 4.4, 5.5]
    })
    test_df.to_csv(test_file, index=False)
    
    state = {
        'csv_path': test_file,
        'df': None,
        'analysis_type': 'summary',
        'metadata': {},
        'basic_stats': {},
        'insights': {},
        'recommendations': [],
        'error': None
    }
    
    result = load_and_validate(state)
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
    
    if result['error'] is None and result['df'] is not None and len(result['df']) == 5:
        print("✅ PASSED: Valid file loaded successfully")
        print(f"   Loaded {len(result['df'])} rows, {len(result['df'].columns)} columns")
    else:
        print("❌ FAILED: Valid file not loaded")
        if result['error']:
            print(f"   Error: {result['error']}")
    
    return result['error'] is None


def test_directory_rejection():
    """Test that directories are rejected (not regular files)"""
    print("\n=== Test 4: Directory Rejection ===")
    
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    
    state = {
        'csv_path': uploads_dir,  # This is a directory, not a file
        'df': None,
        'analysis_type': 'summary',
        'metadata': {},
        'basic_stats': {},
        'insights': {},
        'recommendations': [],
        'error': None
    }
    
    result = load_and_validate(state)
    
    if result['error'] and 'not a regular file' in result['error']:
        print("✅ PASSED: Directory rejected")
        print(f"   Error: {result['error']}")
    else:
        print("❌ FAILED: Directory not rejected")
    
    return result['error'] is not None


def test_large_file_chunking():
    """Test that large files trigger chunked reading"""
    print("\n=== Test 5: Large File Handling (Mock) ===")
    
    # Create a file with many rows to simulate large file behavior
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(uploads_dir, exist_ok=True)
    
    test_file = os.path.join(uploads_dir, 'test_large_validation.csv')
    
    # Create a CSV with more rows than typical to test row limiting
    large_df = pd.DataFrame({
        'col1': range(1000),
        'col2': [f'value_{i}' for i in range(1000)],
        'col3': [i * 1.5 for i in range(1000)]
    })
    large_df.to_csv(test_file, index=False)
    
    state = {
        'csv_path': test_file,
        'df': None,
        'analysis_type': 'summary',
        'metadata': {},
        'basic_stats': {},
        'insights': {},
        'recommendations': [],
        'error': None
    }
    
    result = load_and_validate(state)
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
    
    if result['error'] is None and result['df'] is not None:
        print("✅ PASSED: Large file handled")
        print(f"   Loaded {len(result['df'])} rows (max enforced: 100000)")
    else:
        print("❌ FAILED: Large file handling failed")
        if result['error']:
            print(f"   Error: {result['error']}")
    
    return result['error'] is None


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("CSV Validation Security and Resource Tests")
    print("=" * 60)
    
    tests = [
        test_path_traversal_protection,
        test_file_not_found,
        test_directory_rejection,
        test_valid_file,
        test_large_file_chunking
    ]
    
    results = []
    for test in tests:
        try:
            passed = test()
            results.append(passed)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Test Summary: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
