"""
Test script for absolute date parsing fixes.
Tests all 8 cases that should trigger direct creation.
"""

from Ai.NLP import parse_free_text
from datetime import datetime


def test_case(num: int, text: str, expected_date: str, expected_duration: int):
    """Test a single absolute date case."""
    print(f"\n{'='*80}")
    print(f"TEST CASE {num}")
    print(f"{'='*80}")
    print(f"Input: {text}")
    print(f"-" * 80)
    
    result = parse_free_text(text)
    parsed = result.get("parsed", {})
    critical = result.get("critical_fields", {})
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  Status: {result.get('status')}")
    print(f"  Date+Time: {parsed.get('dueDateTime')}")
    print(f"  Duration: {parsed.get('durationMinutes')} minutes")
    print(f"  Task Type: {parsed.get('task_type')}")
    print(f"  Priority: {parsed.get('priority')}")
    
    print(f"\n🔍 CRITICAL FIELDS:")
    print(f"  Has Date: {critical.get('has_date')}")
    print(f"  Has Time: {critical.get('has_time')}")
    print(f"  Has Duration: {critical.get('has_duration')}")
    print(f"  All Present: {critical.get('all_present')}")
    
    # Validate
    passed = True
    
    # Check shouldCreateDirectly
    should_create = critical.get('all_present', False)
    if not should_create:
        print(f"\n  ❌ shouldCreateDirectly: Expected true, got false")
        passed = False
    else:
        print(f"\n  ✅ shouldCreateDirectly: true")
    
    # Check date was parsed
    actual_datetime = parsed.get('dueDateTime')
    if not actual_datetime:
        print(f"  ❌ Date+Time: Not parsed")
        passed = False
    else:
        # Check the date portion matches (we'll be flexible on exact match)
        if expected_date in actual_datetime:
            print(f"  ✅ Date: Contains {expected_date}")
        else:
            print(f"  ❌ Date: Expected to contain {expected_date}, got {actual_datetime}")
            passed = False
    
    # Check duration
    actual_duration = parsed.get('durationMinutes')
    if actual_duration != expected_duration:
        print(f"  ❌ Duration: Expected {expected_duration}, got {actual_duration}")
        passed = False
    else:
        print(f"  ✅ Duration: {actual_duration} minutes")
    
    print(f"\n{'🎉 PASSED' if passed else '❌ FAILED'}")
    return passed


def main():
    print("="*80)
    print("ABSOLUTE DATE PARSING TESTS")
    print("="*80)
    print("All 8 cases should trigger direct creation (shouldCreateDirectly=true)")
    
    results = []
    
    # Case 1: Written month, ordinal day, year, natural-language time
    results.append(test_case(
        1,
        "schedule a high-priority study session on november 25th 2025 at 10 in the morning for one hour.",
        "2025-11-25T10:00",
        60
    ))
    
    # Case 2: Written month, ordinal day, year, numeric time
    results.append(test_case(
        2,
        "create a medium-priority training workout on december 3rd 2025 at 14:30 for 90 minutes.",
        "2025-12-03T14:30",
        90
    ))
    
    # Case 3: Numeric date (MM/DD/YYYY)
    results.append(test_case(
        3,
        "add a low-priority personal appointment on 12/10/2025 at 09:15 for 30 minutes.",
        "2025-12-10T09:15",  # Assuming MM/DD format
        30
    ))
    
    # Case 4: Month name + day, WITHOUT explicit year
    results.append(test_case(
        4,
        "schedule a high-priority work meeting on December 10th at 11:00 for 45 minutes.",
        "12-10",  # Just check month-day, year will be inferred
        45
    ))
    
    # Case 5: ISO date
    results.append(test_case(
        5,
        "add a personal task on 2025-12-20 at 08:45 for 50 minutes.",
        "2025-12-20T08:45",
        50
    ))
    
    # Case 6: European-style numeric date with dots
    results.append(test_case(
        6,
        "schedule a low-priority personal task on 20.12.2025 at 18:00 for 40 minutes.",
        "2025-12-20T18:00",
        40
    ))
    
    # Case 7: Day Month Year
    results.append(test_case(
        7,
        "schedule a medium-priority work meeting on 10 dec 2025 at 16:00 for 90 minutes.",
        "2025-12-10T16:00",
        90
    ))
    
    # Case 8: Month Day, Year WITH comma - TEST THE TIME BUG FIX
    results.append(test_case(
        8,
        "schedule a low-priority personal appointment on december 5, 2025 at 13:00 for 30 minutes.",
        "2025-12-05T13:00",  # Must be 13:00, NOT 05:00!
        30
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
        print("\n🎉 ALL ABSOLUTE DATE TESTS PASSED!")
        print("   Direct creation now works for all absolute date formats.")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED. Review output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
