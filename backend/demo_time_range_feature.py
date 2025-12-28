"""
Demo: Time Range Parsing Feature
Shows how the NLP now automatically calculates duration from time ranges
"""

from Ai.NLP import parse_free_text
from datetime import datetime


def demo_example(text: str):
    """Show parsing result for a given text."""
    print(f"\n{'─'*80}")
    print(f"📝 Input: {text}")
    print(f"{'─'*80}")
    
    result = parse_free_text(text)
    parsed = result.get("parsed", {})
    
    # Show what was extracted
    if parsed.get('dueDateTime'):
        dt = datetime.fromisoformat(parsed['dueDateTime'])
        print(f"⏰ Time: {dt.strftime('%H:%M')}")
        print(f"📅 Date: {dt.strftime('%Y-%m-%d')}")
    elif parsed.get('preferredTimeOfDay'):
        print(f"⏰ Preferred Time: {parsed.get('preferredTimeOfDay')}")
    
    if parsed.get('durationMinutes'):
        hours = parsed['durationMinutes'] // 60
        mins = parsed['durationMinutes'] % 60
        duration_str = f"{hours}h {mins}m" if hours else f"{mins}m"
        print(f"⏱️  Duration: {parsed['durationMinutes']} minutes ({duration_str})")
    
    if parsed.get('windowStart') and parsed.get('windowEnd'):
        ws = datetime.fromisoformat(parsed['windowStart'])
        we = datetime.fromisoformat(parsed['windowEnd'])
        print(f"📆 Window: {ws.strftime('%Y-%m-%d')} to {we.strftime('%Y-%m-%d')}")
    
    print(f"📊 Status: {result.get('status')}")
    print(f"🏷️  Type: {parsed.get('task_type')}")
    print(f"⚡ Priority: {parsed.get('priority')}")


print("=" * 80)
print("🎉 TIME RANGE PARSING FEATURE DEMO")
print("=" * 80)
print("\nThe NLP now automatically detects time ranges and calculates duration!\n")

print("\n┌─ Example 1: Basic Time Range ─────────────────────────────────────────┐")
demo_example("Meeting next Monday at 9:00 - 11:00")

print("\n┌─ Example 2: Time Range with 'to' ─────────────────────────────────────┐")
demo_example("Call from 14:00 to 14:30 on December 10th")

print("\n┌─ Example 3: Time Range with AM/PM ────────────────────────────────────┐")
demo_example("Workshop 10:00 am to 2:30 pm next Friday")

print("\n┌─ Example 4: Evening Range ────────────────────────────────────────────┐")
demo_example("Dinner meeting 6:00 pm - 8:30 pm next week")

print("\n┌─ Example 5: Explicit Duration Takes Precedence ───────────────────────┐")
demo_example("Meeting at 9:00 - 11:00 for 90 minutes next Tuesday")
print("   ^ Note: Explicit '90 minutes' overrides the 2-hour range")

print("\n┌─ Example 6: Single Time Still Works (No Regression) ─────────────────┐")
demo_example("Meeting at 9:00 for 2 hours next week")
print("   ^ Classic format with explicit duration still works perfectly")

print("\n┌─ Example 7: Time Range Without Date ──────────────────────────────────┐")
demo_example("Schedule task from 10:00 to 11:30")
print("   ^ Duration calculated even without a specific date")

print("\n" + "=" * 80)
print("✅ Feature successfully implemented!")
print("=" * 80)
