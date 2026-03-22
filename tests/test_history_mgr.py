import pytest

from src.core.history_mgr import HistoryManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_history.db"
    mgr = HistoryManager(db_path=str(db_file))
    yield mgr
    # Connection is handled by HistoryManager (context manager style or persistent)
    # Since HistoryManager currently doesn't have a close() method, we just let it be.


def test_add_and_get_meeting(temp_db):
    meeting_id = temp_db.add_meeting(title="Test Meeting", transcript="Hello world", audio_path="test.mp3", model_info="base")
    assert meeting_id == 1

    meetings = temp_db.get_all_meetings()
    assert len(meetings) == 1
    assert meetings[0]["title"] == "Test Meeting"
    assert meetings[0]["transcript"] == "Hello world"
    assert meetings[0]["audio_path"] == "test.mp3"


def test_update_minutes(temp_db):
    meeting_id = temp_db.add_meeting(title="Test Meeting", transcript="Hello world", audio_path="test.mp3")

    temp_db.update_minutes(meeting_id, "Summary of meeting")

    meetings = temp_db.get_all_meetings()
    assert meetings[0]["minutes"] == "Summary of meeting"


def test_get_single_meeting(temp_db):
    meeting_id = temp_db.add_meeting(title="Single", transcript="...", audio_path="...")
    meeting = temp_db.get_meeting(meeting_id)
    assert meeting["title"] == "Single"

    # Test non-existent
    assert temp_db.get_meeting(999) is None
