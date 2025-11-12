"""
Test DFU plotting through dashboard interface
"""
from dashboard_v2 import SimpleDashboard

def test_dashboard_integration():
    """Test DFU plotting through the dashboard's natural language processor."""

    dashboard = SimpleDashboard()

    # Test the exact query from user requirements
    query = "show me the droplet size across all measured DFUs for each w13 device that was tested at 5mlhr200mbar"

    print("=" * 80)
    print("Testing DFU Query Through Dashboard Interface")
    print("=" * 80)
    print()
    print(f"Query: {query}")
    print()

    # Use the dashboard's execute_natural_language method
    dashboard.execute_natural_language(query)

    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_dashboard_integration()
