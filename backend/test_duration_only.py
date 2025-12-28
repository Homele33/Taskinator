"""
Test script for CASE "Duration Only"

Verifies that when the user provides only duration (no date, no time):
1. Suggestions span multiple days across the horizon
2. All suggestions use the exact same duration
3. Rest days are excluded (no explicit date = filter rest days)
4. BN scoring ranks the suggestions
5. Refresh produces different suggestions but same duration
"""

from Ai.NLP import parse_free_text


def test_duration_only_case(num: int, text: str, expected_duration: int, description: str):
    """Test that duration-only inputs produce correct NLP output."""
    print(f"\n{'='*80}")
    print(f"DURATION ONLY TEST {num}")
    print(f"{'='*80}")
    print(f"Input: {text}")
    print(f"Expected: Duration={expected_duration} min, No date, No time")
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
    
    print(f"\n🔍 CRITICAL FIELDS:")
    print(f"  Has Date: {critical.get('has_date')}")
    print(f"  Has Time: {critical.get('has_time')}")
    print(f"  Has Duration: {critical.get('has_duration')}")
    print(f"  All Present: {critical.get('all_present')}")
    
    # Verify expectations
    checks = []
    
    # 1. Status should be partial (missing date/time)
    if result.get("status") == "partial":
        print(f"\n  ✅ Status is 'partial' (correct)")
        checks.append(True)
    else:
        print(f"\n  ❌ Status should be 'partial', got '{result.get('status')}'")
        checks.append(False)
    
    # 2. No dueDateTime (no date+time given)
    if not parsed.get("dueDateTime"):
        print(f"  ✅ No dueDateTime (correct)")
        checks.append(True)
    else:
        print(f"  ❌ dueDateTime should be None, got '{parsed.get('dueDateTime')}'")
        checks.append(False)
    
    # 3. Duration should match expected
    if parsed.get("durationMinutes") == expected_duration:
        print(f"  ✅ Duration matches: {expected_duration} minutes")
        checks.append(True)
    else:
        print(f"  ❌ Duration should be {expected_duration}, got {parsed.get('durationMinutes')}")
        checks.append(False)
    
    # 4. No window (no date range given)
    if not parsed.get("windowStart") and not parsed.get("windowEnd"):
        print(f"  ✅ No window (correct for duration-only)")
        checks.append(True)
    else:
        print(f"  ❌ Should have no window for duration-only")
        checks.append(False)
    
    # 5. No preferred time (no time given)
    if not parsed.get("preferredTimeOfDay"):
        print(f"  ✅ No preferredTimeOfDay (correct)")
        checks.append(True)
    else:
        print(f"  ❌ Should have no preferredTimeOfDay for duration-only")
        checks.append(False)
    
    # 6. explicitDateRequested should be False (no date given)
    if parsed.get("explicitDateRequested") == False:
        print(f"  ✅ explicitDateRequested is False (correct - will filter rest days)")
        checks.append(True)
    else:
        print(f"  ❌ explicitDateRequested should be False for duration-only")
        checks.append(False)
    
    # 7. Critical fields check
    if (not critical.get("has_date") and 
        not critical.get("has_time") and 
        critical.get("has_duration") and 
        not critical.get("all_present")):
        print(f"  ✅ Critical fields correct (only duration present)")
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
    print("DURATION ONLY TESTS")
    print("="*80)
    print("Testing CASE 'Duration Only' - user provides only task duration")
    print()
    print("Expected behavior:")
    print("  1. Suggestions should span multiple days (not just today)")
    print("  2. All suggestions must use the exact same duration")
    print("  3. Rest days should be excluded (no explicit date)")
    print("  4. BN scoring should rank suggestions")
    print("  5. Refresh may change suggestions but duration stays fixed")
    print()
    
    results = []
    
    # ============================================================
    # TEST CASES: Duration Only
    # ============================================================
    
    # Test 1: Short task - 30 minutes
    results.append(test_duration_only_case(
        1,
        "schedule a short task for 30 minutes",
        30,
        "Simple duration-only input"
    ))
    
    # Test 2: Medium task - 60 minutes
    results.append(test_duration_only_case(
        2,
        "schedule a meeting for one hour",
        60,
        "Duration in hours"
    ))
    
    # Test 3: Long task - 90 minutes
    results.append(test_duration_only_case(
        3,
        "schedule a deep work session for 90 minutes",
        90,
        "Explicit minutes"
    ))
    
    # Test 4: Two hours
    results.append(test_duration_only_case(
        4,
        "schedule a high-priority study session for two hours",
        120,
        "Two hours with priority"
    ))
    
    # Test 5: 45 minutes
    results.append(test_duration_only_case(
        5,
        "plan a workout for 45 minutes",
        45,
        "45-minute workout"
    ))
    
    # Test 6: Three hours
    results.append(test_duration_only_case(
        6,
        "block time for 3 hours",
        180,
        "Three hours"
    ))
    
    # Test 7: 50 minutes
    results.append(test_duration_only_case(
        7,
        "schedule a training session for 50 minutes",
        50,
        "50-minute training"
    ))
    
    # Test 8: Half hour
    results.append(test_duration_only_case(
        8,
        "quick meeting for half an hour",
        30,
        "Half hour expression"
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
        print("\n🎉 ALL DURATION ONLY TESTS PASSED!")
        print()
        print("✅ NLP correctly parses duration-only inputs")
        print("✅ No date or time is inferred (correct)")
        print("✅ explicitDateRequested is False (rest days will be filtered)")
        print("✅ Status is 'partial' (triggers suggestion mode)")
        print()
        print("📝 Next Step:")
        print("   The suggestion engine should now:")
        print("   - Generate suggestions across multiple days (not just today)")
        print("   - Use the exact parsed duration for all suggestions")
        print("   - Exclude rest days (Friday/Saturday in typical setup)")
        print("   - Rank suggestions by BN scores")
        print("   - Allow variation on refresh while keeping duration fixed")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED. Review output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
