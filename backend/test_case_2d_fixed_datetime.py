"""
Test script for CASE 2.D: Date + Time + NO Duration

Tests scenarios where user provides:
- A specific DATE (absolute or relative)
- A specific TIME
- NO duration specified

Expected behavior:
- CASE 2.D (suggestions mode) is used
- All suggestions have the EXACT date provided
- All suggestions have the EXACT time provided
- Only DURATION varies (30, 45, 60, 90 minutes, etc.)
- Date and time remain fixed on refresh
- Rest day override applies if date is explicit
"""

from Ai.NLP import parse_free_text
from datetime import datetime


def test_fixed_datetime_case(num: int, text: str, description: str, expected_date: str, expected_time: str):
    """Test that date + time (no duration) scenarios are parsed correctly."""
    print(f"\n{'='*80}")
    print(f"TEST CASE 2.D.{num}")
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
    print(f"  Explicit DateTime Given: {parsed.get('explicitDateTimeGiven')}")
    print(f"  Task Type: {parsed.get('task_type')}")
    print(f"  Priority: {parsed.get('priority')}")
    
    print(f"\n🔍 CRITICAL FIELDS:")
    print(f"  Has Date: {critical.get('has_date')}")
    print(f"  Has Time: {critical.get('has_time')}")
    print(f"  Has Duration: {critical.get('has_duration')}")
    print(f"  All Present: {critical.get('all_present')}")
    
    # Validations
    checks = []
    
    # Should have dueDateTime (date + time are specified)
    if parsed.get("dueDateTime"):
        print(f"\n  ✅ dueDateTime present: {parsed.get('dueDateTime')}")
        checks.append(True)
        
        # Verify date and time match expected
        dt_str = parsed.get("dueDateTime")
        if expected_date in dt_str:
            print(f"  ✅ Date matches: {expected_date}")
            checks.append(True)
        else:
            print(f"  ❌ Date mismatch: expected {expected_date}, got {dt_str}")
            checks.append(False)
        
        if expected_time in dt_str:
            print(f"  ✅ Time matches: {expected_time}")
            checks.append(True)
        else:
            print(f"  ❌ Time mismatch: expected {expected_time}, got {dt_str}")
            checks.append(False)
    else:
        print(f"\n  ❌ dueDateTime should be present for CASE 2.D")
        checks.append(False)
    
    # Should NOT have duration
    if parsed.get("durationMinutes") is None:
        print(f"  ✅ No duration (correct - this is CASE 2.D)")
        checks.append(True)
    else:
        print(f"  ❌ Duration should be None for CASE 2.D")
        checks.append(False)
    
    # Should have explicitDateTimeGiven flag
    if parsed.get("explicitDateTimeGiven"):
        print(f"  ✅ explicitDateTimeGiven flag set")
        checks.append(True)
    else:
        print(f"  ❌ explicitDateTimeGiven flag not set")
        checks.append(False)
    
    # Critical fields check
    if critical.get("has_date") and critical.get("has_time") and not critical.get("has_duration"):
        print(f"  ✅ Critical fields correct (Date=True, Time=True, Duration=False)")
        checks.append(True)
    else:
        print(f"  ❌ Critical fields incorrect")
        checks.append(False)
    
    # Should NOT be direct creation (all_present should be False because duration is missing)
    if not critical.get("all_present"):
        print(f"  ✅ All present = False (correct for CASE 2.D)")
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
    print("CASE 2.D TESTS: Date + Time + NO Duration")
    print("="*80)
    print("These should trigger suggestion mode with fixed date+time")
    print("All suggestions should have:")
    print("  - Exact parsed date (not change on refresh)")
    print("  - Exact parsed time (not drift)")
    print("  - Different durations (30m, 45m, 60m, 90m...)")
    
    results = []
    
    # Test 1: Absolute date + time, no duration
    results.append(test_fixed_datetime_case(
        1,
        "schedule a high-priority meeting on December 3rd 2025 at 18:00",
        "Date=2025-12-03, Time=18:00, No Duration",
        "2025-12-03",
        "18:00"
    ))
    
    # Test 2: Absolute date + time (different format), no duration
    results.append(test_fixed_datetime_case(
        2,
        "schedule a medium-priority study session on January 10th at 09:15",
        "Date=Jan 10, Time=09:15, No Duration",
        "01-10",
        "09:15"
    ))
    
    # Test 3: Relative date + time, no duration
    results.append(test_fixed_datetime_case(
        3,
        "schedule a low-priority workout next Tuesday at 7 in the evening",
        "Date=next Tuesday, Time=19:00, No Duration",
        "2025-12-02",  # Next Tuesday from Nov 27 (Wednesday)
        "19:00"
    ))
    
    # Test 4: Absolute date + time with "at", no duration
    results.append(test_fixed_datetime_case(
        4,
        "create a work meeting on November 25th 2025 at 10 in the morning",
        "Date=2025-11-25, Time=10:00, No Duration",
        "2025-11-25",
        "10:00"
    ))
    
    # Test 5: ISO date format + time, no duration
    results.append(test_fixed_datetime_case(
        5,
        "schedule a training session on 2025-12-20 at 14:30",
        "Date=2025-12-20, Time=14:30, No Duration",
        "2025-12-20",
        "14:30"
    ))
    
    # Test 6: Upcoming Monday + time, no duration
    results.append(test_fixed_datetime_case(
        6,
        "schedule a meeting upcoming Monday at 11 am",
        "Date=upcoming Monday, Time=11:00, No Duration",
        "2025-12-01",  # Upcoming Monday from Nov 27 (Wednesday)
        "11:00"
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
        print("\n🎉 ALL CASE 2.D TESTS PASSED!")
        print("   Date+Time is correctly preserved.")
        print("   Duration is missing.")
        print("   explicitDateTimeGiven flag is set.")
        print("   Critical fields correctly indicate CASE 2.D (suggestions mode).")
        print("\n📝 Note: These tests verify NLP parsing only.")
        print("   Suggestion engine behavior (fixed date+time, varying duration)")
        print("   should be verified through API integration tests or manual testing.")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED. Review output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
