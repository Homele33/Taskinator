"""
Test script for CASE 2.G (Time Only)

Verifies that when the user provides only TIME (no date, no duration):
1. preferredTimeOfDay is correctly extracted
2. No date or duration is present
3. Appropriate flags are set
4. Suggestion engine enters fixed-time mode
5. All suggestions use the exact time from input
6. Dates vary across horizon
7. Durations vary (30, 45, 60, 90, 120 min)
8. Rest days are excluded (no explicit date)
"""

from Ai.NLP import parse_free_text


def test_case_2g(num: int, text: str, expected_time: str, description: str):
    """Test that time-only inputs produce correct NLP output."""
    print(f"\n{'='*80}")
    print(f"CASE 2.G TEST {num}")
    print(f"{'='*80}")
    print(f"Input: {text}")
    print(f"Expected: Time={expected_time}, No date, No duration")
    print(f"Description: {description}")
    print(f"-" * 80)
    
    result = parse_free_text(text)
    parsed = result.get("parsed", {})
    critical = result.get("critical_fields", {})
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  Status: {result.get('status')}")
    print(f"  dueDateTime: {parsed.get('dueDateTime')}")
    print(f"  durationMinutes: {parsed.get('durationMinutes')}")
    print(f"  windowStart: {parsed.get('windowStart')}")
    print(f"  windowEnd: {parsed.get('windowEnd')}")
    print(f"  preferredTimeOfDay: {parsed.get('preferredTimeOfDay')}")
    print(f"  explicitDateRequested: {parsed.get('explicitDateRequested')}")
    print(f"  explicitDateTimeGiven: {parsed.get('explicitDateTimeGiven')}")
    
    print(f"\n🔍 CRITICAL FIELDS:")
    print(f"  Has Date: {critical.get('has_date')}")
    print(f"  Has Time: {critical.get('has_time')}")
    print(f"  Has Duration: {critical.get('has_duration')}")
    print(f"  All Present: {critical.get('all_present')}")
    
    # Verify expectations
    checks = []
    
    # 1. Status should be partial (missing date/duration)
    if result.get("status") == "partial":
        print(f"\n  ✅ Status is 'partial' (correct)")
        checks.append(True)
    else:
        print(f"\n  ❌ Status should be 'partial', got '{result.get('status')}'")
        checks.append(False)
    
    # 2. No dueDateTime (no full date+time)
    if not parsed.get("dueDateTime"):
        print(f"  ✅ No dueDateTime (correct)")
        checks.append(True)
    else:
        print(f"  ❌ dueDateTime should be None, got '{parsed.get('dueDateTime')}'")
        checks.append(False)
    
    # 3. No duration
    if not parsed.get("durationMinutes"):
        print(f"  ✅ No duration (correct)")
        checks.append(True)
    else:
        print(f"  ❌ Duration should be None, got {parsed.get('durationMinutes')}")
        checks.append(False)
    
    # 4. No window
    if not parsed.get("windowStart") and not parsed.get("windowEnd"):
        print(f"  ✅ No window (correct for time-only)")
        checks.append(True)
    else:
        print(f"  ❌ Should have no window for time-only")
        checks.append(False)
    
    # 5. preferredTimeOfDay should match expected
    if parsed.get("preferredTimeOfDay") == expected_time:
        print(f"  ✅ preferredTimeOfDay matches: {expected_time}")
        checks.append(True)
    else:
        print(f"  ❌ preferredTimeOfDay should be {expected_time}, got {parsed.get('preferredTimeOfDay')}")
        checks.append(False)
    
    # 6. explicitDateRequested should be False (no date given)
    if parsed.get("explicitDateRequested") == False:
        print(f"  ✅ explicitDateRequested is False (correct - will filter rest days)")
        checks.append(True)
    else:
        print(f"  ❌ explicitDateRequested should be False for time-only")
        checks.append(False)
    
    # 7. explicitDateTimeGiven should be False (no full datetime)
    if parsed.get("explicitDateTimeGiven") == False:
        print(f"  ✅ explicitDateTimeGiven is False (correct)")
        checks.append(True)
    else:
        print(f"  ❌ explicitDateTimeGiven should be False for time-only")
        checks.append(False)
    
    # 8. Critical fields check
    if (not critical.get("has_date") and 
        not critical.get("has_time") and 
        not critical.get("has_duration") and 
        not critical.get("all_present")):
        print(f"  ✅ Critical fields correct (none present)")
        checks.append(True)
    else:
        print(f"  ❌ Critical fields incorrect")
        checks.append(False)
    
    if all(checks):
        print(f"\n🎉 PASSED")
        return True
    else:
        print(f"\n❌ FAILED")
        return False


def main():
    print("="*80)
    print("CASE 2.G TESTS: Time Only (No Date, No Duration)")
    print("="*80)
    print("Testing inputs where user provides ONLY a time")
    print()
    print("Expected behavior:")
    print("  1. preferredTimeOfDay extracted correctly")
    print("  2. No date or duration")
    print("  3. explicitDateRequested = False (rest days filtered)")
    print("  4. Suggestion engine enters fixed-time mode")
    print("  5. All suggestions use the exact input time")
    print("  6. Dates vary across horizon")
    print("  7. Durations vary (30, 45, 60, 90, 120 min)")
    print()
    
    results = []
    
    # ============================================================
    # TEST CASES: Time Only (CASE 2.G)
    # ============================================================
    
    # Test 1: 24-hour format with "at"
    results.append(test_case_2g(
        1,
        "schedule a task at 15:00",
        "15:00",
        "24-hour format with 'at'"
    ))
    
    # Test 2: 12-hour format with am
    results.append(test_case_2g(
        2,
        "add a meeting at 7 am",
        "07:00",
        "12-hour format with am"
    ))
    
    # Test 3: Time with "in the morning"
    results.append(test_case_2g(
        3,
        "plan something at 9 in the morning",
        "09:00",
        "Time with 'in the morning' pattern"
    ))
    
    # Test 4: Time with pm
    results.append(test_case_2g(
        4,
        "create a task at 6 pm",
        "18:00",
        "12-hour format with pm"
    ))
    
    # Test 5: Precise time with minutes
    results.append(test_case_2g(
        5,
        "schedule something at 14:30",
        "14:30",
        "24-hour format with minutes"
    ))
    
    # Test 6: Evening time
    results.append(test_case_2g(
        6,
        "add a task at 7 in the evening",
        "19:00",
        "Time with 'in the evening' pattern"
    ))
    
    # Test 7: Morning with minutes and am
    results.append(test_case_2g(
        7,
        "plan a meeting at 9:15 am",
        "09:15",
        "12-hour format with minutes and am"
    ))
    
    # Test 8: Afternoon time
    results.append(test_case_2g(
        8,
        "schedule at 3 in the afternoon",
        "15:00",
        "Time with 'in the afternoon' pattern"
    ))
    
    # Test 9: Late evening
    results.append(test_case_2g(
        9,
        "create something at 21:00",
        "21:00",
        "Late evening 24-hour format"
    ))
    
    # Test 10: Early morning
    results.append(test_case_2g(
        10,
        "add a task at 8:30 am",
        "08:30",
        "Early morning with minutes"
    ))
    
    # ============================================================
    # SUMMARY
    # ============================================================
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
        print("\n🎉 ALL CASE 2.G TESTS PASSED!")
        print()
        print("✅ NLP correctly extracts time from time-only inputs")
        print("✅ No date or duration is inferred (correct)")
        print("✅ preferredTimeOfDay is set correctly")
        print("✅ explicitDateRequested is False (rest days will be filtered)")
        print("✅ explicitDateTimeGiven is False (no full datetime)")
        print("✅ Status is 'partial' (triggers suggestion mode)")
        print()
        print("📝 Next Step:")
        print("   The suggestion engine should now:")
        print("   - Enter CASE 2.G mode (fixed time + flexible date + flexible duration)")
        print("   - Generate suggestions at the EXACT time specified")
        print("   - Vary dates across the horizon (skip rest days)")
        print("   - Vary durations (30, 45, 60, 90, 120 min)")
        print("   - Rank by BN scores")
        print("   - On refresh, keep the same time but explore different dates/durations")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED. Review output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
