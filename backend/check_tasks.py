"""
Check existing tasks to see if they have scheduled_start/end or just due_date.
"""
from models import Task, db
from config import app

def main():
    with app.app_context():
        # Get all tasks
        all_tasks = Task.query.all()
        
        print(f"Total tasks in database: {len(all_tasks)}\n")
        
        # Count tasks by scheduling status
        has_scheduled = 0
        has_due_date_only = 0
        has_neither = 0
        
        tasks_with_scheduled = []
        tasks_with_due_only = []
        
        for task in all_tasks:
            if task.scheduled_start and task.scheduled_end:
                has_scheduled += 1
                tasks_with_scheduled.append(task)
            elif task.due_date:
                has_due_date_only += 1
                tasks_with_due_only.append(task)
            else:
                has_neither += 1
        
        print("=" * 60)
        print("TASK SCHEDULING STATUS")
        print("=" * 60)
        print(f"✅ Tasks with scheduled_start & scheduled_end: {has_scheduled}")
        print(f"⚠️  Tasks with only due_date (NO scheduling): {has_due_date_only}")
        print(f"❌ Tasks with neither: {has_neither}")
        print()
        
        # Show sample of tasks with scheduled times
        if tasks_with_scheduled:
            print("\n" + "=" * 60)
            print("SAMPLE: Tasks with scheduling (BN CAN learn from these)")
            print("=" * 60)
            for task in tasks_with_scheduled[:5]:
                print(f"ID={task.id}, user={task.user_id}, type={task.task_type}")
                print(f"  Title: {task.title}")
                print(f"  Scheduled: {task.scheduled_start} → {task.scheduled_end}")
                print()
        
        # Show sample of tasks with only due_date
        if tasks_with_due_only:
            print("\n" + "=" * 60)
            print("SAMPLE: Tasks with only due_date (BN CANNOT learn from these)")
            print("=" * 60)
            for task in tasks_with_due_only[:5]:
                print(f"ID={task.id}, user={task.user_id}, type={task.task_type}")
                print(f"  Title: {task.title}")
                print(f"  Due date: {task.due_date}")
                print(f"  Due time: {task.due_time}")
                print(f"  Duration: {task.duration_minutes} min")
                print(f"  scheduled_start: {task.scheduled_start}")
                print(f"  scheduled_end: {task.scheduled_end}")
                print()
        
        # Breakdown by user
        print("\n" + "=" * 60)
        print("BREAKDOWN BY USER")
        print("=" * 60)
        user_stats = {}
        for task in all_tasks:
            uid = task.user_id
            if uid not in user_stats:
                user_stats[uid] = {'scheduled': 0, 'due_only': 0, 'neither': 0}
            
            if task.scheduled_start and task.scheduled_end:
                user_stats[uid]['scheduled'] += 1
            elif task.due_date:
                user_stats[uid]['due_only'] += 1
            else:
                user_stats[uid]['neither'] += 1
        
        for uid, stats in sorted(user_stats.items()):
            total = stats['scheduled'] + stats['due_only'] + stats['neither']
            print(f"\nUser {uid}: {total} tasks total")
            print(f"  - {stats['scheduled']} with scheduling (learnable)")
            print(f"  - {stats['due_only']} with only due_date (not learnable)")
            print(f"  - {stats['neither']} with neither")

if __name__ == "__main__":
    main()
