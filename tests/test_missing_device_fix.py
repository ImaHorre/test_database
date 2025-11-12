"""Test if W13_S2_R2 now appears in device breakdown."""
from dashboard_v2 import SimpleDashboard

dashboard = SimpleDashboard()

print("\n" + "="*70)
print("TEST: show w13 at 5mlhr")
print("Expected: Should now see BOTH W13_S1_R1 and W13_S2_R2")
print("="*70 + "\n")

parsed = dashboard.parse_command("show w13 at 5mlhr")
if parsed:
    dashboard.execute_command(parsed)
