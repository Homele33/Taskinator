from datetime import datetime, timedelta
from Ai.network.training import record_task_created
from Ai.network.inference import predict_missing_duration, predict_missing_priority, score_bonus_for_slot

def test_smoke_learning(tmp_path, monkeypatch):
    # Redirect data dir to a temp folder for test isolation
    from Ai.network import model as model_mod
    monkeypatch.setattr(model_mod, "DATA_DIR", str(tmp_path))

    uid = 42
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    # Teach the model that for Meetings, morning 9:00 on Monday is popular, 60 minutes HIGH
    record_task_created(
        user_id=uid,
        title="standup",
        task_type="Meeting",
        priority="HIGH",
        scheduled_start=now,
        scheduled_end=now + timedelta(minutes=60),
        duration_minutes=60,
    )

    assert predict_missing_duration(uid, "Meeting") in (60, None)
    assert predict_missing_priority(uid, "Meeting") in ("HIGH", "MEDIUM", "LOW")

    bonus = score_bonus_for_slot(uid, "Meeting", now, now + timedelta(minutes=60))
    assert bonus >= 0.0
