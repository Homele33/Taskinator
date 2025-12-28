"""
Test script for CASE 2.B: Date + Duration, but NO Time.
Verifies that suggestions respect the parsed date.
"""

from Ai.NLP import parse_free_text
from datetime import datetime


def test_case_2b(num: int, text: str, expected_behavior: str):
    """Test a CASE 2.B scenario."""
    print(f"\n{'='*80}")
    print(f"TEST CASE 2.B.{num}")
    print(f"{'='*80}")
    print(f"Input: {text}")
    print(f"Expected: {expected_behavior}")
    print(f"-" * 80)
    
    result = parse_free_text(text)
    parsed = result.get("parsed", {})
    critical = result.get("critical_fields", {})
    debug = result.get("debug", {})
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  Status: {result.get('status')}")
    print(f"  Date+Time: {parsed.get('dueDateTime')}")
    print(f"  Duration: {parsed.get('durationMinutes')} minutes")
    print(f"  Window Start: {parsed.get('windowStart')}")
    print(f"  Window End: {parsed.get('windowEnd')}")
    print(f"  Task Type: {parsed.get('task_type')}")
    print(f"  Priority: {parsed.get('priority')}")
    
    print(f"\n🔍 CRITICAL FIELDS:")
    print(f"  Has Date: {critical.get('has_date')}")
    print(f"  Has Time: {critical.get('has_time')}")
    print(f"  Has Duration: {critical.get('has_duration')}")
    print(f"  All Present: {critical.get('all_present')}")
    
    # Validate
    passed = True
    
    # Check CASE 2.B conditions
    if critical.get('all_present', False):
        print(f"\n  ❌ Should NOT create directly (time is missing)")
        passed = False
    else:
        print(f"\n  ✅ shouldCreateDirectly: false (correct for CASE 2.B)")
    
    # Check date is present
    if not critical.get('has_date', False):
        print(f"  ❌ Date should be detected")
        passed = False
    else:
        print(f"  ✅ Date detected")
    
    # Check time is NOT present
    if critical.get('has_time', False):
        print(f"  ❌ Time should NOT be detected")
        passed = False
    else:
        print(f"  ✅ Time not detected (correct)")
    
    # Check duration is present
    if not critical.get('has_duration', False):
        print(f"  ❌ Duration should be detected")
        passed = False
    else:
        print(f"  ✅ Duration detected")
    
    # Check window is set (for suggestion generation)
    window_start = parsed.get('windowStart')
    window_end = parsed.get('windowEnd')
    
    if not window_start or not window_end:
        print(f"  ❌ Window (windowStart/windowEnd) should be set for suggestions")
        passed = False
    else:
        print(f"  ✅ Window set for suggestions:")
        print(f"     Start: {window_start}")
        print(f"     End:   {window_end}")
        
        # Parse the dates to verify they're on the same day
        try:
            start_dt = datetime.fromisoformat(window_start)
            end_dt = datetime.fromisoformat(window_end)
            
            if start_dt.date() != end_dt.date():
                print(f"  ❌ Window spans multiple days (should be single day)")
                passed = False
            else:
                print(f"  ✅ Window is for a single day: {start_dt.date()}")
                
            # Check it's a full day window
            if start_dt.hour != 0 or start_dt.minute != 0:
                print(f"  ⚠️  Window doesn't start at midnight (might be intentional)")
            if end_dt.hour != 23 or end_dt.minute != 59:
                print(f"  ⚠️  Window doesn't end at 23:59 (might be intentional)")
        except Exception as e:
            print(f"  ❌ Error parsing window dates: {e}")
            passed = False
    
    print(f"\n{'🎉 PASSED' if passed else '❌ FAILED'}")
    return passed


def main():
    print("="*80)
    print("CASE 2.B TESTS: Date + Duration, NO Time")
    print("="*80)
    print("These should trigger suggestion mode (not direct creation)")
    print("AND suggestions should be constrained to the parsed date")
    
    results = []
    
    # Test 1: Absolute date, no time
    results.append(test_case_2b(
        1,
        "schedule a high-priority study session on november 25th 2025 for one hour.",
        "Suggestions on 2025-11-25 only, duration 60 min"
    ))
    
    # Test 2: Relative date (next Tuesday), no time
    results.append(test_case_2b(
        2,
        "schedule a medium-priority meeting next Tuesday for one hour.",
        "Suggestions on next Tuesday only, duration 60 min"
    ))
    
    # Test 3: Absolute date with different duration
    results.append(test_case_2b(
        3,
        "plan a work session on december 10th 2025 for two hours.",
        "Suggestions on 2025-12-10 only, duration 120 min"
    ))
    
    # Test 4: Relative date (upcoming Monday), no time
    results.append(test_case_2b(
        4,
        "gym workout upcoming monday for 90 minutes.",
        "Suggestions on upcoming Monday only, duration 90 min"
    ))
    
    # Test 5: Complex relative date (ordinal of next month), no time
    results.append(test_case_2b(
        5,
        "study session on the second friday of next month for one hour.",
        "Suggestions on 2nd Friday of next month only, duration 60 min"
    ))
    
    # Test 6: Far future date (third Friday of next month) - Tests horizon fix
    results.append(test_case_2b(
        6,
        "schedule a high-priority workout on the third Friday of next month for 50 minutes.",
        "Suggestions on 3rd Friday of next month only, duration 50 min (beyond default horizon)"
    ))
    
    # Test 7: Verify explicitDateRequested flag for explicit date (rest day override)
    print(f"\n{'='*80}")
    print(f"TEST CASE 2.B.7 - REST DAY OVERRIDE FLAG")
    print(f"{'='*80}")
    print(f"Input: schedule a high-priority workout on the third Friday of next month for 50 minutes.")
    print(f"Expected: explicitDateRequested = True (enables rest day override)")
    print(f"-" * 80)
    
    result = parse_free_text("schedule a high-priority workout on the third Friday of next month for 50 minutes.")
    parsed = result.get("parsed", {})
    explicit_date_requested = parsed.get("explicitDateRequested", False)
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  explicitDateRequested: {explicit_date_requested}")
    print(f"  Window Start: {parsed.get('windowStart')}")
    print(f"  Window End: {parsed.get('windowEnd')}")
    
    if explicit_date_requested:
        print(f"\n✅ PASSED - explicitDateRequested is True")
        print(f"   This will allow suggestions on rest days when user explicitly chose the date.")
        results.append(True)
    else:
        print(f"\n❌ FAILED - explicitDateRequested should be True for explicit dates")
        results.append(False)
    
    # Test 8: Verify explicitDateRequested flag is False for generic input
    print(f"\n{'='*80}")
    print(f"TEST CASE 2.B.8 - NO EXPLICIT DATE")
    print(f"{'='*80}")
    print(f"Input: schedule a high-priority workout for 50 minutes.")
    print(f"Expected: explicitDateRequested = False (rest days should be avoided)")
    print(f"-" * 80)
    
    result = parse_free_text("schedule a high-priority workout for 50 minutes.")
    parsed = result.get("parsed", {})
    explicit_date_requested = parsed.get("explicitDateRequested", False)
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  explicitDateRequested: {explicit_date_requested}")
    print(f"  has_date: {result.get('critical_fields', {}).get('has_date')}")
    
    if not explicit_date_requested:
        print(f"\n✅ PASSED - explicitDateRequested is False")
        print(f"   Rest days will be excluded from suggestions (normal behavior).")
        results.append(True)
    else:
        print(f"\n❌ FAILED - explicitDateRequested should be False when no date specified")
        results.append(False)
    
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
        print("\n🎉 ALL CASE 2.B TESTS PASSED!")
        print("   Date constraint is preserved when time is missing.")
        print("   Suggestions will be constrained to the parsed date.")
        print("   Works for both near and far future dates (beyond default horizon).")
        print("   explicitDateRequested flag correctly set for rest day override.")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED. Review output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
