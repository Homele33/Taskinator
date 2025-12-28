"""
Test script for CASE 2.C: Time + Duration + Range (No Explicit Date)

Tests scenarios where user provides:
- A clear time-of-day (e.g., "at 10 in the morning", "at 18:00")
- A clear duration (e.g., "for one hour", "for 45 minutes")
- A relative temporal range (e.g., "sometime this week", "later this month")
- But NO explicit calendar date

Expected behavior:
- CASE 2.B (suggestions mode) is used
- All suggestions have the exact parsed time-of-day
- All suggestions have the exact parsed duration
- All suggestion dates are strictly inside the derived range
- Range does not drift on refresh
"""

from Ai.NLP import parse_free_text
from datetime import datetime


def test_time_range_case(num: int, text: str, description: str):
    """Test that time + range scenarios are parsed correctly."""
    print(f"\n{'='*80}")
    print(f"TEST CASE 2.C.{num}")
    print(f"{'='*80}")
    print(f"Input: {text}")
    print(f"Expected: {description}")
    print(f"-" * 80)
    
    result = parse_free_text(text)
    parsed = result.get("parsed", {})
    critical = result.get("critical_fields", {})
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  Status: {result.get('status')}")
    print(f"  Date+Time (dueDateTime): {parsed.get('dueDateTime')}")
    print(f"  Duration: {parsed.get('durationMinutes')} minutes")
    print(f"  Window Start: {parsed.get('windowStart')}")
    print(f"  Window End: {parsed.get('windowEnd')}")
    print(f"  Preferred Time: {parsed.get('preferredTimeOfDay')}")
    print(f"  Task Type: {parsed.get('task_type')}")
    print(f"  Priority: {parsed.get('priority')}")
    
    print(f"\n🔍 CRITICAL FIELDS:")
    print(f"  Has Date: {critical.get('has_date')}")
    print(f"  Has Time: {critical.get('has_time')}")
    print(f"  Has Duration: {critical.get('has_duration')}")
    print(f"  All Present: {critical.get('all_present')}")
    
    # Validations
    checks = []
    
    # Should NOT have dueDateTime (not a full datetime)
    if parsed.get("dueDateTime") is None:
        print(f"\n  ✅ No dueDateTime (correct - this is CASE 2.C)")
        checks.append(True)
    else:
        print(f"\n  ❌ dueDateTime should be None for CASE 2.C")
        checks.append(False)
    
    # Should have window
    if parsed.get("windowStart") and parsed.get("windowEnd"):
        print(f"  ✅ Window set for date range")
        checks.append(True)
    else:
        print(f"  ❌ Window not set")
        checks.append(False)
    
    # Should have preferred time
    if parsed.get("preferredTimeOfDay"):
        print(f"  ✅ Preferred time extracted: {parsed.get('preferredTimeOfDay')}")
        checks.append(True)
    else:
        print(f"  ❌ Preferred time not extracted")
        checks.append(False)
    
    # Should have duration
    if parsed.get("durationMinutes"):
        print(f"  ✅ Duration: {parsed.get('durationMinutes')} minutes")
        checks.append(True)
    else:
        print(f"  ❌ Duration not extracted")
        checks.append(False)
    
    # Critical fields check
    if critical.get("has_date") and not critical.get("has_time") and critical.get("has_duration"):
        print(f"  ✅ Critical fields correct (Date=True, Time=False, Duration=True)")
        checks.append(True)
    else:
        print(f"  ❌ Critical fields incorrect")
        checks.append(False)
    
    # Should NOT be direct creation
    if not critical.get("all_present"):
        print(f"  ✅ All present = False (correct for CASE 2.C)")
        checks.append(True)
    else:
        print(f"  ❌ All present should be False")
        checks.append(False)
    
    if all(checks):
        print(f"\n🎉 PASSED")
        return True
    else:
        print(f"\n❌ FAILED")
        return False


def main():
    print("="*80)
    print("CASE 2.C TESTS: Time + Duration + Range (No Explicit Date)")
    print("="*80)
    print("These should trigger suggestion mode with fixed time-of-day")
    print("All suggestions should have:")
    print("  - Exact parsed time (not drift by 30min steps)")
    print("  - Exact parsed duration")
    print("  - Dates only within the parsed range (not beyond)")
    
    results = []
    
    # Test 1: "sometime this week at 10 in the morning for one hour"
    results.append(test_time_range_case(
        1,
        "schedule a medium-priority study session sometime this week at 10 in the morning for one hour.",
        "Window=this week, Time=10:00, Duration=60min"
    ))
    
    # Test 2: "sometime next week at 7 in the evening for 45 minutes"
    results.append(test_time_range_case(
        2,
        "schedule a low-priority running workout sometime next week at 7 in the evening for 45 minutes.",
        "Window=next week, Time=19:00, Duration=45min"
    ))
    
    # Test 3: "later this month at 18:00 for 90 minutes"
    results.append(test_time_range_case(
        3,
        "schedule a high-priority work meeting later this month at 18:00 for 90 minutes.",
        "Window=later this month, Time=18:00, Duration=90min"
    ))
    
    # Test 4: "sometime next month at 6 in the morning for one hour"
    results.append(test_time_range_case(
        4,
        "schedule a medium-priority training session sometime next month at 6 in the morning for one hour.",
        "Window=next month, Time=06:00, Duration=60min"
    ))
    
    # Test 5: "sometime in January at 14:30 for 2 hours"
    results.append(test_time_range_case(
        5,
        "schedule a low-priority personal appointment sometime in January at 14:30 for 2 hours.",
        "Window=January, Time=14:30, Duration=120min"
    ))
    
    # Test 6: "this month at 9 am for 30 minutes"
    results.append(test_time_range_case(
        6,
        "schedule a high-priority meeting this month at 9 am for 30 minutes.",
        "Window=this month, Time=09:00, Duration=30min"
    ))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL CASE 2.C TESTS PASSED!")
        print("   Time-of-day is correctly extracted with date range.")
        print("   Duration is parsed.")
        print("   Critical fields correctly indicate CASE 2.C (suggestions mode).")
        print("\n📝 Note: These tests verify NLP parsing only.")
        print("   Suggestion engine behavior (fixed time, stable range) should be")
        print("   verified through API integration tests or manual testing.")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED. Review output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
