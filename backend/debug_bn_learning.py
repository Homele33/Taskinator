"""
Debug why BN has 0 observations despite tasks having scheduled times.
"""
from models import Task, db
from config import app
from Ai.network.bayesian import UserBayesianNetwork
from datetime import datetime

def main():
    with app.app_context():
        # Get user 6's tasks (the one with 31 tasks)
        user_id = 6
        tasks = Task.query.filter_by(user_id=user_id).limit(5).all()
        
        print("=" * 70)
        print(f"DEBUGGING BN LEARNING FOR USER {user_id}")
        print("=" * 70)
        
        # Check BN state
        bn = UserBayesianNetwork(user_id)
        print(f"\nBN Status:")
        print(f"  - is_trained: {bn.is_trained()}")
        print(f"  - num observations: {len(bn.observations)}")
        print(f"  - is_initialized: {bn.is_initialized}")
        
        # Show what observations look like
        print(f"\n\nFirst 5 tasks and their observation format:")
        print("=" * 70)
        
        for task in tasks:
            print(f"\nTask ID={task.id}: {task.title[:50]}")
            print(f"  - task_type: {task.task_type}")
            print(f"  - priority: {task.priority}")
            print(f"  - scheduled_start: {task.scheduled_start}")
            print(f"  - scheduled_end: {task.scheduled_end}")
            print(f"  - duration_minutes: {task.duration_minutes}")
            
            # Simulate what _task_to_obs would produce
            from datetime import timedelta
            start = getattr(task, "scheduled_start", None) or getattr(task, "due_date", None)
            end = getattr(task, "scheduled_end", None)
            
            if not end and start and getattr(task, "duration_minutes", None):
                end = start + timedelta(minutes=int(task.duration_minutes or 0))
            
            dur = None
            if start and end:
                dur = int((end - start).total_seconds() // 60)
            
            obs = {
                "user_id": task.user_id,
                "task_type": task.task_type or "Meeting",
                "priority": task.priority or "MEDIUM",
                "scheduled_start": start,
                "scheduled_end": end,
                "duration_minutes": dur or task.duration_minutes,
            }
            
            print(f"\n  Observation dict:")
            print(f"    user_id: {obs['user_id']}")
            print(f"    task_type: {obs['task_type']}")
            print(f"    scheduled_start: {obs['scheduled_start']} (type: {type(obs['scheduled_start'])})")
            print(f"    scheduled_end: {obs['scheduled_end']} (type: {type(obs['scheduled_end'])})")
            print(f"    duration_minutes: {obs['duration_minutes']}")
            
            # Check if this would pass the learning filter
            start_ok = obs['scheduled_start'] and isinstance(obs['scheduled_start'], datetime)
            print(f"\n  Would pass learning filter? {start_ok}")
            if not start_ok:
                print(f"    ❌ scheduled_start is None or not datetime")
        
        # Check statistics
        print("\n\n" + "=" * 70)
        print("BN STATISTICS STATE")
        print("=" * 70)
        print(f"Task type counts: {dict(bn.statistics.task_type_counts)}")
        print(f"Hour counts (Meeting): {dict(bn.statistics.hour_counts_by_type.get('Meeting', {}))}")
        print(f"Hour counts (Training): {dict(bn.statistics.hour_counts_by_type.get('Training', {}))}")
        print(f"Hour counts (Studies): {dict(bn.statistics.hour_counts_by_type.get('Studies', {}))}")
        
        # Check if BN was ever initialized
        print("\n\n" + "=" * 70)
        print("CHECKING BN FILE")
        print("=" * 70)
        from Ai.network.bayesian.bn_persistence import get_bn_file_path, load_bn_state
        bn_path = get_bn_file_path(user_id)
        print(f"BN file path: {bn_path}")
        print(f"BN file exists: {bn_path.exists()}")
        
        if bn_path.exists():
            data = load_bn_state(user_id)
            if data:
                print(f"\nBN file contents:")
                print(f"  - user_id: {data.get('user_id')}")
                print(f"  - num observations: {len(data.get('observations', []))}")
                print(f"  - metadata: {data.get('metadata')}")
                
                if data.get('observations'):
                    print(f"\nFirst observation in file:")
                    print(f"  {data['observations'][0]}")
                else:
                    print(f"\n  ⚠️  No observations in file!")

if __name__ == "__main__":
    main()
