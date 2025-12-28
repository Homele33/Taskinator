"""
Test BN predictions to ensure scores vary based on learned patterns.
"""
from models import db
from config import app
from Ai.network.bayesian import UserBayesianNetwork
from datetime import datetime, timedelta

def main():
    with app.app_context():
        user_id = 6
        bn = UserBayesianNetwork(user_id)
        
        print("=" * 70)
        print(f"TESTING BN PREDICTIONS FOR USER {user_id}")
        print("=" * 70)
        print(f"\nBN Status:")
        print(f"  - is_trained: {bn.is_trained()}")
        print(f"  - observations: {len(bn.observations)}")
        
        # Test predictions at different times
        base_date = datetime(2025, 11, 25)  # A Monday
        test_slots = []
        
        # Morning slots
        for hour in [7, 8, 9, 10, 11]:
            start = base_date.replace(hour=hour, minute=0)
            end = start + timedelta(hours=1)
            test_slots.append(("Morning", hour, start, end))
        
        # Afternoon/Evening slots
        for hour in [12, 14, 16, 17, 19, 20]:
            start = base_date.replace(hour=hour, minute=0)
            end = start + timedelta(hours=1)
            test_slots.append(("Afternoon/Evening", hour, start, end))
        
        # Test for each task type
        for task_type in ["Meeting", "Training", "Studies"]:
            print(f"\n{'=' * 70}")
            print(f"TASK TYPE: {task_type}")
            print(f"{'=' * 70}")
            print(f"{'Time Period':<20} {'Hour':<6} {'Score':<8} {'Interpretation'}")
            print("-" * 70)
            
            scores = []
            for period, hour, start, end in test_slots:
                score = bn.predict_slot_score(task_type, start, end)
                scores.append((hour, score))
                
                # Interpretation
                if score >= 7:
                    interp = "🟢 Excellent"
                elif score >= 5:
                    interp = "🟡 Good"
                elif score >= 3:
                    interp = "🟠 Fair"
                else:
                    interp = "🔴 Poor"
                
                print(f"{period:<20} {hour:02d}:00  {score:6.2f}   {interp}")
            
            # Show range
            min_score = min(s[1] for s in scores)
            max_score = max(s[1] for s in scores)
            score_range = max_score - min_score
            
            print(f"\nScore Range: {min_score:.2f} - {max_score:.2f} (spread: {score_range:.2f})")
            
            if score_range < 0.1:
                print("  ⚠️  WARNING: All scores are nearly identical!")
                print("     This suggests the BN is not using learned data properly.")
            else:
                print(f"  ✅ Scores vary by {score_range:.2f} points - learning is working!")
        
        # Show learned patterns
        print(f"\n{'=' * 70}")
        print("LEARNED PATTERNS FROM TASK HISTORY")
        print(f"{'=' * 70}")
        
        for task_type in ["Meeting", "Training", "Studies"]:
            hour_counts = bn.statistics.hour_counts_by_type.get(task_type, {})
            if hour_counts:
                sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                top_3 = sorted_hours[:3]
                
                print(f"\n{task_type}:")
                print(f"  Most common hours:")
                for hour, count in top_3:
                    print(f"    {hour:02d}:00 - {count} tasks")

if __name__ == "__main__":
    main()
