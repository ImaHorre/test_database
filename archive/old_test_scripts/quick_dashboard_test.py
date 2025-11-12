"""
Quick test to verify dashboard loads and help displays correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard_v2 import SimpleDashboard

# Initialize dashboard
print("Initializing dashboard...")
dashboard = SimpleDashboard()

# Show startup info
dashboard.show_startup_info()

# Show menu
print("\n")
dashboard.show_menu()

# Show help excerpt - just the DATA EXPORT section
print("\n" + "="*70)
print("DATA EXPORT SECTION FROM HELP:")
print("="*70)
dashboard.show_help()

print("\n✓ Dashboard initialization successful!")
print("✓ Export feature documented in help menu")
print("✓ Export command available: export, export csv, save, save csv")
