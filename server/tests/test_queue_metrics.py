from unittest.mock import patch, MagicMock
from app.utils.queue_metrics import (
    compute_estimated_wait_minutes,
    get_session_avg_resolve_time_minutes,
    sort_questions,
    _parse_ts
)

def test_parse_ts():
    assert _parse_ts(None) is None
    assert _parse_ts("invalid") is None
    dt = _parse_ts("2024-01-01T12:00:00Z")
    assert dt is not None
    assert dt.year == 2024

def test_compute_estimated_wait_minutes():
    # position <= 0 or avg <= 0 -> 5
    assert compute_estimated_wait_minutes(0, 10.0) == 5
    assert compute_estimated_wait_minutes(1, 0.0) == 5
    
    # 1 * 5.0 -> 5
    assert compute_estimated_wait_minutes(1, 5.0) == 5
    
    # rounding logic
    assert compute_estimated_wait_minutes(1, 5.4) == 5
    assert compute_estimated_wait_minutes(1, 5.6) == 6
    
    # cap at 60
    assert compute_estimated_wait_minutes(10, 10.0) == 60
    
    # floor at 1
    assert compute_estimated_wait_minutes(1, 0.1) == 1

def test_sort_questions_priority_and_time():
    questions = [
        {"id": "q1", "priority": "low", "created_at": "2024-01-01T10:05:00", "status": "queued"},
        {"id": "q2", "priority": "high", "created_at": "2024-01-01T10:06:00", "status": "queued"},
        {"id": "q3", "priority": "medium", "created_at": "2024-01-01T10:04:00", "status": "queued"},
        {"id": "q4", "priority": "high", "created_at": "2024-01-01T10:01:00", "status": "queued"},
    ]
    
    sorted_q = sort_questions(questions)
    
    # Priority high -> medium -> low
    # Within high: q4 (10:01) before q2 (10:06)
    assert sorted_q[0]["id"] == "q4"
    assert sorted_q[1]["id"] == "q2"
    assert sorted_q[2]["id"] == "q3"
    assert sorted_q[3]["id"] == "q1"

def test_sort_questions_deferred():
    questions = [
        {"id": "active1", "priority": "low", "created_at": "2024-01-01T10:05:00", "status": "queued"},
        {"id": "def2", "priority": "high", "created_at": "2024-01-01T09:00:00", "deferred_at": "2024-01-01T11:05:00", "status": "deferred"},
        {"id": "def1", "priority": "high", "created_at": "2024-01-01T09:00:00", "deferred_at": "2024-01-01T11:00:00", "status": "deferred"},
        {"id": "active2", "priority": "high", "created_at": "2024-01-01T10:01:00", "status": "queued"},
    ]
    
    sorted_q = sort_questions(questions)
    
    # Active items come first (active2 -> active1)
    assert sorted_q[0]["id"] == "active2"
    assert sorted_q[1]["id"] == "active1"
    
    # Deferred items go last, sorted by deferred_at (def1 -> def2)
    assert sorted_q[2]["id"] == "def1"
    assert sorted_q[3]["id"] == "def2"

@patch("app.utils.queue_metrics.supabase")
def test_get_session_avg_resolve_time_minutes_success(mock_supabase):
    mock_execute = MagicMock()
    # 2 resolved questions
    # q1 took 5 minutes (300s)
    # q2 took 15 minutes (900s)
    # average should be 10 minutes
    mock_execute.data = [
        {"created_at": "2024-01-01T10:00:00Z", "resolved_at": "2024-01-01T10:05:00Z", "status": "resolved"},
        {"created_at": "2024-01-01T10:10:00Z", "resolved_at": "2024-01-01T10:25:00Z", "status": "resolved"},
        {"created_at": "2024-01-01T10:10:00Z", "resolved_at": "invalid", "status": "resolved"}, # should be skipped
        {"created_at": "2024-01-01T10:10:00Z", "resolved_at": "2024-01-01T09:25:00Z", "status": "resolved"}, # negative time, skipped
        {"created_at": "2024-01-01T10:10:00Z", "resolved_at": "2024-01-01T10:10:30Z", "status": "resolved"}, # 30s -> rounded to 1.0 minute min
    ]
    
    # Mocking supabase.table().select().eq().eq().execute()
    mock_table = mock_supabase.table.return_value
    mock_select = mock_table.select.return_value
    mock_eq1 = mock_select.eq.return_value
    mock_eq2 = mock_eq1.eq.return_value
    mock_eq2.execute.return_value = mock_execute
    
    avg = get_session_avg_resolve_time_minutes("session_id")
    
    # Average of 5, 15, and 1 = 21 / 3 = 7.0
    assert avg == 7.0

@patch("app.utils.queue_metrics.supabase")
def test_get_session_avg_resolve_time_minutes_empty(mock_supabase):
    mock_execute = MagicMock()
    mock_execute.data = []
    
    mock_supabase.table().select().eq().eq().execute.return_value = mock_execute
    
    avg = get_session_avg_resolve_time_minutes("session_id")
    assert avg == 5.0 # default

@patch("app.utils.queue_metrics.supabase")
def test_get_session_avg_resolve_time_minutes_error(mock_supabase):
    mock_supabase.table().select().eq().eq().execute.side_effect = Exception("DB Error")
    
    avg = get_session_avg_resolve_time_minutes("session_id")
    assert avg == 5.0 # fallback
