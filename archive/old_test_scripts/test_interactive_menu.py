#!/usr/bin/env python
"""Test interactive plot menu"""

from dashboard_v2 import SimpleDashboard

# Create dashboard
dash = SimpleDashboard()

# Simulate user workflow from testnotes.md
print("\n=== SIMULATING USER WORKFLOW ===\n")

# Step 1: Filter to w13 at 5mlhr (without 'at' - testing fuzzy matching)
print("1. User types: show w13 5mlhr")
parsed = dash.parse_command("show w13 5mlhr")
print(f"   Parsed as: {parsed}")

if parsed:
    dash.execute_command(parsed)
    print(f"   Session filters: {dash.session_state['current_filters']}")
    print(f"   Prompt: {dash._get_prompt()}")

print("\n2. User types: plot")
print("   Should show interactive menu...")
print()

# This would normally be interactive, so we'll just check if the method exists
if hasattr(dash, '_show_interactive_plot_menu'):
    print("✓ Interactive plot menu method exists")

    # Show what the menu would display
    filters = dash.session_state['current_filters']
    filtered = dash.df.copy()

    if filters.get('device_type'):
        filtered = filtered[filtered['device_type'] == filters['device_type']]
    if filters.get('flowrate'):
        filtered = filtered[filtered['aqueous_flowrate'] == filters['flowrate']]

    devices = sorted(filtered['device_id'].unique())
    has_droplet = len(filtered[filtered['file_type'] == 'csv']) > 0
    has_freq = len(filtered[filtered['file_type'] == 'txt']) > 0

    print(f"  Data context: {len(filtered)} measurements, {len(devices)} devices")
    print(f"  Has droplet data: {has_droplet}")
    print(f"  Has frequency data: {has_freq}")
    print(f"  Devices: {devices}")

    # The actual menu would show:
    print("\n  Menu would show:")
    print("  - DROPLET MEASUREMENTS section")
    print("  - FREQUENCY MEASUREMENTS section")
    print("  - COMBINED PLOTS section")
    print("  - Letter-based options (A, B, C, etc.)")
else:
    print("✗ Interactive plot menu method NOT found")

print("\n=== TEST COMPLETE ===\n")
