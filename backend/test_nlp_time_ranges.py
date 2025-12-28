"""
Test script for Time Range Parsing Feature

Tests that the NLP parser correctly identifies time ranges like "9:00 - 11:00" 
or "9:00 to 11:00" and calculates duration automatically.

Expected behavior:
- Time ranges should be detected and duration calculated from start to end
- Explicit duration (e.g., "for 2 hours") should take precedence over time ranges
- Single time parsing (e.g., "at 9:00") should still work
- Various time range formats should be supported (dash, to, until, AM/PM)
"""

from Ai.NLP import parse_free_text
from datetime import datetime


def test_time_range(num: int, text: str, expected_time: str, expected_duration: int, description: str):
    """Test that time range is correctly parsed."""
    print(f"\n{'='*80}")
    print(f"TEST {num}")
    print(f"{'='*80}")
    print(f"Input: {text}")
    print(f"Expected: Time={expected_time}, Duration={expected_duration} minutes")
    print(f"Description: {description}")
    print(f"-" * 80)
    
    result = parse_free_text(text)
    parsed = result.get("parsed", {})
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  Status: {result.get('status')}")
    print(f"  Due DateTime: {parsed.get('dueDateTime')}")
    print(f"  Duration: {parsed.get('durationMinutes')} minutes")
    print(f"  Priority: {parsed.get('priority')}")
    print(f"  Task Type: {parsed.get('task_type')}")
    
    checks = []
    
    # Check duration
    actual_duration = parsed.get('durationMinutes')
    if actual_duration == expected_duration:
        print(f"\n  ✅ Duration correct: {actual_duration} minutes")
        checks.append(True)
    else:
        print(f"\n  ❌ Duration incorrect: Expected {expected_duration}, got {actual_duration}")
        checks.append(False)
    
    # Check time (if datetime is present)
    if parsed.get('dueDateTime'):
        dt = datetime.fromisoformat(parsed['dueDateTime'])
        actual_time = dt.strftime("%H:%M")
        if actual_time == expected_time:
            print(f"  ✅ Time correct: {actual_time}")
            checks.append(True)
        else:
            print(f"  ❌ Time incorrect: Expected {expected_time}, got {actual_time}")
            checks.append(False)
    else:
        # For cases without full datetime, just verify duration was extracted
        print(f"  ℹ️  No full datetime (expected for partial dates)")
    
    if all(checks):
        print(f"\n🎉 PASSED")
        return True
    else:
        print(f"\n❌ FAILED")
        return False


def main():
    print("="*80)
    print("TIME RANGE PARSING TESTS")
    print("="*80)
    print("Testing NLP parser's ability to detect time ranges and calculate duration")
    
    results = []
    
    # Test 1: Basic time range with dash (no spaces)
    results.append(test_time_range(
        1,
        "Meeting next week at 9:00-11:00",
        "09:00",
        120,
        "Basic range with dash, no spaces"
    ))
    
    # Test 2: Time range with dash (with spaces)
    results.append(test_time_range(
        2,
        "Meeting next week at 9:00 - 11:00",
        "09:00",
        120,
        "Basic range with dash and spaces"
    ))
    
    # Test 3: Time range with "to"
    results.append(test_time_range(
        3,
        "Call from 14:00 to 14:30",
        "14:00",
        30,
        "Range with 'to' keyword"
    ))
    
    # Test 4: Time range with "until"
    results.append(test_time_range(
        4,
        "Event 10:00 until 11:15",
        "10:00",
        75,
        "Range with 'until' keyword"
    ))
    
    # Test 5: Time range with AM/PM
    results.append(test_time_range(
        5,
        "Meeting 9:00 am - 11:00 am next Monday",
        "09:00",
        120,
        "Range with AM notation"
    ))
    
    # Test 6: Time range crossing AM/PM
    results.append(test_time_range(
        6,
        "Event 10:30 am to 2:00 pm on December 15th",
        "10:30",
        210,
        "Range crossing AM to PM"
    ))
    
    # Test 7: Afternoon time range (24-hour format)
    results.append(test_time_range(
        7,
        "Workshop on January 10th from 14:00 to 17:30",
        "14:00",
        210,
        "Afternoon range in 24-hour format"
    ))
    
    # Test 8: Short meeting (15 minutes)
    results.append(test_time_range(
        8,
        "Quick sync next Tuesday 15:00-15:15",
        "15:00",
        15,
        "Short 15-minute range"
    ))
    
    # Test 9: Evening range with PM
    results.append(test_time_range(
        9,
        "Dinner meeting 6:00 pm - 8:30 pm next Friday",
        "18:00",
        150,
        "Evening range with PM"
    ))
    
    # Test 10: Explicit duration should take precedence
    results.append(test_time_range(
        10,
        "Meeting at 9:00 - 11:00 for 90 minutes",
        "09:00",
        90,
        "Explicit duration overrides time range"
    ))
    
    # Test 11: Single time (no range) should still work
    results.append(test_time_range(
        11,
        "Meeting at 9:00 for 2 hours next week",
        "09:00",
        120,
        "Single time with explicit duration (regression test)"
    ))
    
    # Test 12: Time only, no date
    results.append(test_time_range(
        12,
        "Schedule task from 10:00 to 11:30",
        "10:00",
        90,
        "Time range without specific date"
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
        print("\n🎉 ALL TIME RANGE TESTS PASSED!")
        print("   Time ranges are correctly detected")
        print("   Duration is automatically calculated from start to end time")
        print("   Explicit duration takes precedence when both are present")
        print("   Single time parsing still works (no regression)")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED. Review output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
