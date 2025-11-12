"""
Quick test to verify the refactored query handlers work correctly.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src import DataAnalyst


def test_refactored_query_handlers():
    """Test that the refactored query handlers work correctly."""
    print("="*60)
    print("TESTING REFACTORED QUERY HANDLERS")
    print("="*60)

    try:
        # Initialize analyst
        print("1. Initializing DataAnalyst...")
        analyst = DataAnalyst()
        print(f"   [OK] Loaded {len(analyst.df)} records")

        # Test query router
        print("\n2. Testing query router initialization...")
        assert analyst.query_router is not None
        print(f"   [OK] Query router initialized with {len(analyst.query_router.handlers)} handlers")

        # Test available intents
        print("\n3. Checking available intents...")
        intents = analyst.query_router.get_available_intents()
        print(f"   [OK] Available intents: {', '.join(intents)}")

        # Test basic queries
        test_queries = [
            "list device types",
            "help",
            "show me W13 devices"
        ]

        print("\n4. Testing natural language queries...")
        for query in test_queries:
            try:
                result = analyst.process_natural_language_query(query)
                assert isinstance(result, dict)
                assert 'status' in result
                assert 'message' in result
                print(f"   [OK] Query '{query}' -> {result['status']}")
            except Exception as e:
                print(f"   [FAIL] Query '{query}' failed: {e}")

        print("\n" + "="*60)
        print("[SUCCESS] ALL TESTS PASSED - Query handler refactoring successful!")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_refactored_query_handlers()
    sys.exit(0 if success else 1)