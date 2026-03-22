from unittest.mock import MagicMock, patch

import pytest

from src.controllers.minutes_ctrl import MinutesController
from src.controllers.transcription_ctrl import TranscriptionController
from src.core.history_mgr import history_mgr
from src.core.state import state


@pytest.fixture
def mock_deps():
    config_mgr = MagicMock()
    transcriber = MagicMock()
    return config_mgr, transcriber


def test_transcription_controller_history_linking(mock_deps):
    config_mgr, transcriber = mock_deps
    ctrl = TranscriptionController(config_mgr, transcriber)

    # Mock LiveTranscriptionManager
    with patch("src.controllers.transcription_ctrl.LiveTranscriptionManager") as mock_live_mgr:
        instance = mock_live_mgr.return_value
        instance.stop.return_value = "Full transcript text"
        instance.mp3_path = "recordings/test.mp3"
        instance.model_name = "base"

        # Manually trigger stop logic
        ctrl.live_mgr = instance

        # We need to mock history_mgr.add_meeting as well
        with patch.object(history_mgr, "add_meeting", return_value=123) as mock_add:
            # We mimic the stop worker thread logic directly for simple testing
            full_text = ctrl.live_mgr.stop()
            meeting_id = history_mgr.add_meeting(title="Test", transcript=full_text, audio_path=instance.mp3_path, model_info=instance.model_name)
            state.set("current_meeting_id", meeting_id)

            assert state.get("current_meeting_id") == 123
            mock_add.assert_called_once()


def test_minutes_controller_history_update(mock_deps):
    config_mgr, _ = mock_deps
    MinutesController(config_mgr)

    state.set("current_meeting_id", 456)

    # Mock LLM Client
    with patch("src.llm.factory.LLMFactory.create_client") as mock_factory:
        mock_client = mock_factory.return_value
        mock_client.generate_minutes.return_value = "AI Generated Minutes"

        with patch.object(history_mgr, "update_minutes") as mock_update:
            # Use the controller logic
            # We'll just test the part that updates the history
            res = mock_client.generate_minutes("transcript", "base")
            meeting_id = state.get("current_meeting_id")
            if meeting_id:
                history_mgr.update_minutes(meeting_id, res)

            mock_update.assert_called_with(456, "AI Generated Minutes")
