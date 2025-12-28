"""
Test script to validate NLP parsing fixes for the three test cases.
Run this to verify all bugs are fixed before deploying.
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
    
    # Overall result
    print(f"\n{'🎉 TEST PASSED' if passed else '❌ TEST FAILED'}")
    
    return passed


def main():
    print("="*80)
    print("NLP PARSING FIX VALIDATION")
    print("="*80)
    print("Testing three problem cases that should trigger DIRECT CREATION")
    print("All should have shouldCreateDirectly=True and no suggestions")
    
    results = []
    
    # TEST CASE A
    results.append(test_case(
        name="CASE A - Brainstorming Session (next Tuesday, 3 in afternoon, 90 min)",
        text="high-priority brainstorming session for the project scheduled for next Tuesday at 3 in the afternoon, lasting about an hour and a half.",
        expected={
            'shouldCreateDirectly': True,
            'duration_minutes': 90,
            'task_type': 'Studies',  # "brainstorming" and "project" → Studies
            'priority': 'HIGH'
        }
    ))
    
    # TEST CASE B
    results.append(test_case(
        name="CASE B - Running Session (next Thursday, 7 in evening, 50 min)",
        text="schedule a low-priority running session next Thursday at 7 in the evening for about 50 minutes.",
        expected={
            'shouldCreateDirectly': True,
            'duration_minutes': 50,
            'task_type': 'Training',  # "running" → Training
            'priority': 'LOW'
        }
    ))
    
    # TEST CASE C
    results.append(test_case(
        name="CASE C - Study Review (first Wed of next month, 9 in morning, 2 hours)",
        text="plan a medium-priority study review session for the final exam on the first Wednesday of next month at 9 in the morning, lasting two hours.",
        expected={
            'shouldCreateDirectly': True,
            'duration_minutes': 120,
            'task_type': 'Studies',  # "study" and "exam" → Studies
            'priority': 'MEDIUM'
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
        print("\n🎉 ALL TESTS PASSED! The fixes work correctly.")
        print("   All three cases now trigger direct creation as expected.")
    else:
        print("\n⚠️ SOME TESTS FAILED. Review the output above for details.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
