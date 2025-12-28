"""
Test script for the 5 new failing NLP cases with relative dates and complex durations.
All should trigger direct creation (CASE 2.A).
"""

from Ai.NLP import parse_free_text
from datetime import datetime
import json


def test_case(name: str, text: str, expected: dict):
    """Test a single case and report results."""
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")
    print(f"Input: {text}")
    print(f"-" * 80)
    
    result = parse_free_text(text)
    
    # Extract parsed values
    parsed = result.get("parsed", {})
    critical = result.get("critical_fields", {})
    
    print(f"\n📊 PARSED RESULTS:")
    print(f"  Status: {result.get('status')}")
    print(f"  Date+Time: {parsed.get('dueDateTime')}")
    print(f"  Duration: {parsed.get('durationMinutes')} minutes")
    print(f"  Task Type: {parsed.get('task_type')}")
    print(f"  Priority: {parsed.get('priority')}")
    print(f"  Title: {parsed.get('title')}")
    
    print(f"\n🔍 CRITICAL FIELDS:")
    print(f"  Has Date: {critical.get('has_date')}")
    print(f"  Has Time: {critical.get('has_time')}")
    print(f"  Has Duration: {critical.get('has_duration')}")
    print(f"  All Present: {critical.get('all_present')}")
    
    print(f"\n✅ EXPECTED:")
    for key, value in expected.items():
        print(f"  {key}: {value}")
    
    # Validate expectations
    print(f"\n🧪 VALIDATION:")
    passed = True
    
    # Check shouldCreateDirectly
    should_create = critical.get('all_present', False)
    if expected.get('shouldCreateDirectly') != should_create:
        print(f"  ❌ shouldCreateDirectly: Expected {expected['shouldCreateDirectly']}, got {should_create}")
        passed = False
    else:
        print(f"  ✅ shouldCreateDirectly: {should_create}")
    
    # Check duration
    expected_duration = expected.get('duration_minutes')
    actual_duration = parsed.get('durationMinutes')
    if expected_duration and actual_duration != expected_duration:
        print(f"  ❌ Duration: Expected {expected_duration}, got {actual_duration}")
        passed = False
    else:
        print(f"  ✅ Duration: {actual_duration} minutes")
    
    # Check task type
    expected_type = expected.get('task_type')
    actual_type = parsed.get('task_type')
    if expected_type and actual_type != expected_type:
        print(f"  ❌ Task Type: Expected {expected_type}, got {actual_type}")
        passed = False
    else:
        print(f"  ✅ Task Type: {actual_type}")
    
    # Check priority
    expected_priority = expected.get('priority')
    actual_priority = parsed.get('priority')
    if expected_priority and actual_priority != expected_priority:
        print(f"  ❌ Priority: Expected {expected_priority}, got {actual_priority}")
        passed = False
    else:
        print(f"  ✅ Priority: {actual_priority}")
    
    # Check date+time parsed
    if expected.get('shouldCreateDirectly') and not parsed.get('dueDateTime'):
        print(f"  ❌ Date+Time: Expected to be parsed, got None")
        passed = False
    elif expected.get('shouldCreateDirectly'):
        print(f"  ✅ Date+Time: {parsed.get('dueDateTime')}")
    
    # Additional validation: check date components if expected
    if expected.get('check_date_components'):
        actual_dt_str = parsed.get('dueDateTime')
        if actual_dt_str:
            actual_dt = datetime.fromisoformat(actual_dt_str)
            checks = expected['check_date_components']
            
            if 'weekday' in checks:
                expected_weekday = checks['weekday']
                actual_weekday = actual_dt.strftime('%A')
                if expected_weekday.lower() != actual_weekday.lower():
                    print(f"  ❌ Weekday: Expected {expected_weekday}, got {actual_weekday}")
                    passed = False
                else:
                    print(f"  ✅ Weekday: {actual_weekday}")
            
            if 'hour' in checks:
                expected_hour = checks['hour']
                actual_hour = actual_dt.hour
                if expected_hour != actual_hour:
                    print(f"  ❌ Hour: Expected {expected_hour}, got {actual_hour}")
                    passed = False
                else:
                    print(f"  ✅ Hour: {actual_hour:02d}:00")
    
    # Overall result
    print(f"\n{'🎉 TEST PASSED' if passed else '❌ TEST FAILED'}")
    
    return passed


def main():
    print("="*80)
    print("NLP NEW CASES VALIDATION - Relative Dates & Complex Durations")
    print("="*80)
    print("Testing 5 new cases that should trigger DIRECT CREATION")
    print("All should have shouldCreateDirectly=True and no suggestions")
    print("\nNOTE: Dates are relative to current time, so exact dates will vary")
    
    results = []
    
    # TEST CASE 1: Second Friday of next month, 2.5 hours
    results.append(test_case(
        name="CASE 1 - Second Friday of next month at 10am, 2.5 hours",
        text="plan a medium-priority deep reading study block for the psychology exam on the second friday of next month at 10 in the morning, lasting two and a half hours.",
        expected={
            'shouldCreateDirectly': True,
            'duration_minutes': 150,  # 2.5 hours
            'task_type': 'Studies',  # "study", "reading", "exam"
            'priority': 'MEDIUM',
            'check_date_components': {
                'weekday': 'Friday',
                'hour': 10
            }
        }
    ))
    
    # TEST CASE 2: Upcoming Monday at 6am, ~1 hour
    results.append(test_case(
        name="CASE 2 - Upcoming Monday at 6am, about an hour",
        text="schedule a medium-priority gym workout for the upcoming monday at 6 in the morning, lasting about an hour.",
        expected={
            'shouldCreateDirectly': True,
            'duration_minutes': 60,
            'task_type': 'Training',  # "gym", "workout"
            'priority': 'MEDIUM',
            'check_date_components': {
                'weekday': 'Monday',
                'hour': 6
            }
        }
    ))
    
    # TEST CASE 3: Upcoming Friday at 5pm, 1h15
    results.append(test_case(
        name="CASE 3 - Upcoming Friday at 5pm, one hour and fifteen minutes",
        text="schedule a high-priority strength training workout on the upcoming friday at 5 in the evening for one hour and fifteen minutes.",
        expected={
            'shouldCreateDirectly': True,
            'duration_minutes': 75,  # 1h 15min
            'task_type': 'Training',  # "strength training", "workout"
            'priority': 'HIGH',
            'check_date_components': {
                'weekday': 'Friday',
                'hour': 17  # 5pm
            }
        }
    ))
    
    # TEST CASE 4: Next month, second Monday at 11am, ~1 hour
    results.append(test_case(
        name="CASE 4 - Next month, second Monday at 11am, about an hour",
        text="schedule a low-priority study session next month on the second monday at 11 in the morning for about an hour.",
        expected={
            'shouldCreateDirectly': True,
            'duration_minutes': 60,
            'task_type': 'Studies',  # "study"
            'priority': 'LOW',
            'check_date_components': {
                'weekday': 'Monday',
                'hour': 11
            }
        }
    ))
    
    # TEST CASE 5: Upcoming Wednesday at 2pm, 1 hour
    results.append(test_case(
        name="CASE 5 - Upcoming Wednesday at 2pm, lasting one hour",
        text="set a high-priority research reading session for the upcoming wednesday at 2 in the afternoon, lasting one hour.",
        expected={
            'shouldCreateDirectly': True,
            'duration_minutes': 60,
            'task_type': 'Studies',  # "research", "reading"
            'priority': 'HIGH',
            'check_date_components': {
                'weekday': 'Wednesday',
                'hour': 14  # 2pm
            }
        }
    ))
    
    # SUMMARY
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
        print("\n🎉 ALL TESTS PASSED! The new fixes work correctly.")
        print("   All 5 cases now trigger direct creation as expected.")
        print("   Relative dates, complex durations, and 'upcoming' patterns work!")
    else:
        print("\n⚠️ SOME TESTS FAILED. Review the output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
