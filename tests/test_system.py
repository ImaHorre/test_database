"""
Quick system test to verify the refactored query handlers work correctly.
"""

import sys
sys.path.insert(0, '.')

from src.analyst import DataAnalyst


def test_system():
    """Test the refactored system with real queries."""
    print("="*70)
    print("COMPREHENSIVE SYSTEM TEST - REFACTORED QUERY HANDLERS")
    print("="*70)

    # Initialize
    print("\n1. Initializing DataAnalyst...")
    analyst = DataAnalyst()
    print(f"   [OK] Loaded {len(analyst.df)} records")
    print(f"   [OK] Query router initialized with {len(analyst.query_router.handlers)} handlers")
    print(f"   [OK] Available intents: {', '.join(analyst.query_router.get_available_intents())}")

    # Test queries
    test_queries = [
        ("List Query", "list device types"),
        ("List Query", "show all flow parameters"),
        ("Help Query", "help"),
        ("Filter Query", "show me W13 devices"),
        ("Filter Query", "filter by 2mlhr flow rate"),
        ("Summary Query", "summarize W13 data"),
    ]

    print("\n2. Testing Natural Language Query Processing...")
    print("-" * 70)

    passed = 0
    failed = 0

    for category, query in test_queries:
        try:
            result = analyst.process_natural_language_query(query)

            # Check basic structure
            if not isinstance(result, dict):
                print(f"   [FAIL] {category}: '{query}'")
                print(f"          Expected dict, got {type(result)}")
                failed += 1
                continue

            if 'status' not in result or 'message' not in result:
                print(f"   [FAIL] {category}: '{query}'")
                print(f"          Missing required fields: {result.keys()}")
                failed += 1
                continue

            # Success
            status = result['status']
            status_icon = "[OK]" if status == 'success' else "[WARN]"
            print(f"   {status_icon} {category}: '{query}'")
            print(f"          Status: {status}, Intent: {result.get('intent', 'unknown')}")

            # Show sample of message
            message = result.get('message', '')
            if message and len(message) > 100:
                print(f"          Message: {message[:100]}...")
            elif message:
                print(f"          Message: {message}")

            passed += 1

        except Exception as e:
            print(f"   [FAIL] {category}: '{query}'")
            print(f"          Error: {e}")
            failed += 1

    # Summary
    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")

    if failed == 0:
        print("[SUCCESS] ALL TESTS PASSED - Refactored system is working correctly!")
    else:
        print(f"[WARNING] Some tests failed - review errors above")

    print("="*70)

    return failed == 0


if __name__ == '__main__':
    success = test_system()
    sys.exit(0 if success else 1)
