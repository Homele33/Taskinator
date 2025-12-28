"""
Retroactively train Bayesian Networks on all existing tasks.

This script:
1. Finds all users with tasks
2. For each user, collects all their scheduled tasks
3. Trains the BN on those tasks

Run this after fixing the BN loading bug to populate learning data.
"""
from models import Task, UserPreferences, db
from config import app
from Ai.network.bayesian import UserBayesianNetwork
from datetime import timedelta

def task_to_observation(task: Task) -> dict:
    """Convert a Task to an observation dict for BN learning."""
    start = getattr(task, "scheduled_start", None) or getattr(task, "due_date", None)
    end = getattr(task, "scheduled_end", None)
    
    if not end and start and getattr(task, "duration_minutes", None):
        end = start + timedelta(minutes=int(task.duration_minutes or 0))
    
    dur = None
    if start and end:
        dur = int((end - start).total_seconds() // 60)
    
    return {
        "user_id": task.user_id,
        "task_type": task.task_type or "Meeting",
        "priority": task.priority or "MEDIUM",
        "scheduled_start": start,
        "scheduled_end": end,
        "duration_minutes": dur or task.duration_minutes,
    }


def retrain_user_bn(user_id: int, dry_run: bool = False) -> dict:
    """
    Retrain a user's BN from all their existing tasks.
    
    Args:
        user_id: User ID
        dry_run: If True, don't save changes
    
    Returns:
        Dict with stats about the retraining
    """
    # Get all tasks with scheduling info
    tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.scheduled_start.isnot(None),
        Task.scheduled_end.isnot(None)
    ).all()
    
    if not tasks:
        return {
            "user_id": user_id,
            "status": "no_tasks",
            "message": "No scheduled tasks to learn from"
        }
    
    # Check if user has preferences (required for BN)
    prefs = UserPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        return {
            "user_id": user_id,
            "status": "no_preferences",
            "message": "User has no preferences, skipping"
        }
    
    try:
        # Load or initialize BN
        bn = UserBayesianNetwork(user_id)
        
        if not bn.is_trained():
            # Initialize from preferences if not already done
            print(f"  [User {user_id}] Initializing BN from preferences...")
            bn.initialize_from_preferences(prefs)
        
        # Clear existing observations
        old_count = len(bn.observations)
        bn.observations = []
        bn.statistics = bn.statistics.__class__()  # Reset statistics
        
        # Add all observations
        valid_count = 0
        for task in tasks:
            obs = task_to_observation(task)
            if obs["scheduled_start"] and obs["scheduled_end"]:
                bn.observations.append(obs)
                bn.statistics.add_observation(obs)
                valid_count += 1
        
        # Recompute CPTs from observations
        if bn.observations:
            from Ai.network.bayesian.bn_learning import recompute_all_cpts_from_observations
            recompute_all_cpts_from_observations(bn.network, bn.observations)
        
        # Save to disk
        if not dry_run:
            bn._save_to_disk()
        
        return {
            "user_id": user_id,
            "status": "success",
            "old_observations": old_count,
            "new_observations": valid_count,
            "total_tasks": len(tasks),
            "message": f"Retrained BN with {valid_count} observations"
        }
    
    except Exception as e:
        return {
            "user_id": user_id,
            "status": "error",
            "message": f"Failed: {str(e)}"
        }


def main(dry_run: bool = False):
    """
    Retrain BNs for all users.
    
    Args:
        dry_run: If True, don't save changes
    """
    with app.app_context():
        # Get all unique user IDs with tasks
        user_ids = db.session.query(Task.user_id).distinct().all()
        user_ids = [uid[0] for uid in user_ids]
        
        print("=" * 70)
        print("RETROACTIVE BN TRAINING")
        print("=" * 70)
        print(f"Found {len(user_ids)} users with tasks")
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be saved\n")
        else:
            print("💾 LIVE MODE - Changes will be saved\n")
        
        results = []
        for user_id in user_ids:
            print(f"\n[User {user_id}] Starting retraining...")
            result = retrain_user_bn(user_id, dry_run=dry_run)
            results.append(result)
            
            status = result["status"]
            msg = result["message"]
            
            if status == "success":
                print(f"  ✅ {msg}")
                print(f"     Old observations: {result['old_observations']}")
                print(f"     New observations: {result['new_observations']}")
            elif status == "no_tasks":
                print(f"  ⚠️  {msg}")
            elif status == "no_preferences":
                print(f"  ⚠️  {msg}")
            else:
                print(f"  ❌ {msg}")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        success_count = sum(1 for r in results if r["status"] == "success")
        total_obs = sum(r.get("new_observations", 0) for r in results if r["status"] == "success")
        
        print(f"✅ Successfully retrained: {success_count} users")
        print(f"📊 Total observations added: {total_obs}")
        print(f"⚠️  Skipped (no tasks): {sum(1 for r in results if r['status'] == 'no_tasks')}")
        print(f"⚠️  Skipped (no prefs): {sum(1 for r in results if r['status'] == 'no_preferences')}")
        print(f"❌ Errors: {sum(1 for r in results if r['status'] == 'error')}")
        
        if dry_run:
            print("\n🔍 This was a dry run. Run without --dry-run to save changes.")


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
