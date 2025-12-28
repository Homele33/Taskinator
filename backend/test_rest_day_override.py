"""
Test script for REST DAY OVERRIDE

Verifies that explicitDateRequested flag works correctly across all CASE types:
- CASE 2.B: Date only, no time
- CASE 2.C: Time + vague range
- CASE 2.D: Date + time, no duration

When explicitDateRequested=True, suggestions MUST appear even on rest days.
When explicitDateRequested=False, rest days MUST be filtered out.
"""

from Ai.NLP import parse_free_text


def test_explicit_date_flag(num: int, text: str, expected_explicit: bool, reason: str):
    """Test that explicitDateRequested flag is set correctly."""
    print(f"\n{'='*80}")
    print(f"REST DAY OVERRIDE TEST {num}")
    print(f"{'='*80}")
    print(f"Input: {text}")
    print(f"Expected: explicitDateRequested = {expected_explicit}")
    print(f"Reason: {reason}")
    print(f"-" * 80)
    
    result = parse_free_text(text)
    parsed = result.get("parsed", {})
    explicit = parsed.get("explicitDateRequested", False)
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  explicitDateRequested: {explicit}")
    print(f"  dueDateTime: {parsed.get('dueDateTime')}")
    print(f"  windowStart: {parsed.get('windowStart')}")
    print(f"  windowEnd: {parsed.get('windowEnd')}")
    print(f"  preferredTimeOfDay: {parsed.get('preferredTimeOfDay')}")
    print(f"  durationMinutes: {parsed.get('durationMinutes')}")
    
    if explicit == expected_explicit:
        print(f"\n✅ PASSED - Flag correctly set to {explicit}")
        if explicit:
            print(f"   → Suggestions WILL appear on rest days (user chose specific date)")
        else:
            print(f"   → Rest days WILL be filtered out (vague range)")
        return True
    else:
        print(f"\n❌ FAILED - Expected {expected_explicit}, got {explicit}")
        return False


def main():
    print("="*80)
    print("REST DAY OVERRIDE TESTS")
    print("="*80)
    print("Testing explicitDateRequested flag across all CASE types")
    print()
    print("RULE 1: Explicit date → explicitDateRequested=True → Allow rest days")
    print("RULE 2: Vague range → explicitDateRequested=False → Filter rest days")
    print()
    
    results = []
    
    # ============================================================
    # GROUP 1: EXPLICIT DATES (should be TRUE)
    # ============================================================
    print("\n" + "="*80)
    print("GROUP 1: EXPLICIT DATES (explicitDateRequested should be TRUE)")
    print("="*80)
    
    # Test 1: Absolute date with year + time + duration (CASE 2.A)
    results.append(test_explicit_date_flag(
        1,
        "schedule a meeting on November 25th 2025 at 10:00 for one hour",
        True,
        "Absolute date + time + duration (CASE 2.A)"
    ))
    
    # Test 2: Absolute date + duration, no time (CASE 2.B)
    results.append(test_explicit_date_flag(
        2,
        "schedule a study session on December 3rd 2025 for two hours",
        True,
        "Absolute date + duration, no time (CASE 2.B)"
    ))
    
    # Test 3: Absolute date + time, no duration (CASE 2.D)
    results.append(test_explicit_date_flag(
        3,
        "schedule a meeting on December 3rd 2025 at 18:00",
        True,
        "Absolute date + time, no duration (CASE 2.D)"
    ))
    
    # Test 4: Relative date (next Tuesday) + time + duration
    results.append(test_explicit_date_flag(
        4,
        "schedule a workout next Tuesday at 7 in the evening for 45 minutes",
        True,
        "Relative date (next Tuesday) is explicit"
    ))
    
    # Test 5: Relative date (on Friday) + duration, no time
    results.append(test_explicit_date_flag(
        5,
        "schedule a study session on Friday for one hour",
        True,
        "Relative date (on Friday/upcoming Friday) is explicit"
    ))
    
    # Test 6: Relative date (upcoming Monday) + time, no duration
    results.append(test_explicit_date_flag(
        6,
        "schedule a meeting upcoming Monday at 11 am",
        True,
        "Relative date (upcoming Monday) is explicit (CASE 2.D)"
    ))
    
    # Test 7: Third Friday of next month + duration
    results.append(test_explicit_date_flag(
        7,
        "schedule a workout on the third Friday of next month for 50 minutes",
        True,
        "Third Friday of next month is explicit"
    ))
    
    # Test 8: Month + day (December 5th) + time
    results.append(test_explicit_date_flag(
        8,
        "schedule a training session on December 5th at 09:15",
        True,
        "Month + day is explicit (CASE 2.D)"
    ))
    
    # ============================================================
    # GROUP 2: VAGUE RANGES (should be FALSE)
    # ============================================================
    print("\n" + "="*80)
    print("GROUP 2: VAGUE RANGES (explicitDateRequested should be FALSE)")
    print("="*80)
    
    # Test 9: Sometime this week + time + duration (CASE 2.C)
    results.append(test_explicit_date_flag(
        9,
        "schedule a study session sometime this week at 10 in the morning for one hour",
        False,
        "Vague range (sometime this week) - CASE 2.C"
    ))
    
    # Test 10: Later this month + time + duration (CASE 2.C)
    results.append(test_explicit_date_flag(
        10,
        "schedule a meeting later this month at 18:00 for 90 minutes",
        False,
        "Vague range (later this month) - CASE 2.C"
    ))
    
    # Test 11: Sometime next week + time + duration (CASE 2.C)
    results.append(test_explicit_date_flag(
        11,
        "schedule a workout sometime next week at 7 in the evening for 45 minutes",
        False,
        "Vague range (sometime next week) - CASE 2.C"
    ))
    
    # Test 12: Sometime next month + time + duration (CASE 2.C)
    results.append(test_explicit_date_flag(
        12,
        "schedule a training session sometime next month at 6 in the morning for one hour",
        False,
        "Vague range (sometime next month) - CASE 2.C"
    ))
    
    # Test 13: Sometime in January + time + duration (CASE 2.C)
    results.append(test_explicit_date_flag(
        13,
        "schedule a personal appointment sometime in January at 14:30 for 2 hours",
        False,
        "Vague range (sometime in January) - CASE 2.C"
    ))
    
    # Test 14: This month + time + duration (CASE 2.C)
    results.append(test_explicit_date_flag(
        14,
        "schedule a meeting this month at 9 am for 30 minutes",
        False,
        "Vague range (this month) - CASE 2.C"
    ))
    
    # Test 15: No date at all, just duration
    results.append(test_explicit_date_flag(
        15,
        "schedule a high-priority workout for 50 minutes",
        False,
        "No date provided at all"
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
        print("\n🎉 ALL REST DAY OVERRIDE TESTS PASSED!")
        print()
        print("✅ Explicit dates correctly set flag to TRUE")
        print("   → Suggestions will appear on rest days when user chooses specific date")
        print()
        print("✅ Vague ranges correctly set flag to FALSE")
        print("   → Rest days will be filtered out for vague time ranges")
        print()
        print("✅ Flag works across CASE 2.A, 2.B, 2.C, and 2.D")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED. Review output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
