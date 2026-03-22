import logging

import flet as ft

from src.controllers.history_ctrl import HistoryController
from src.core.state import state

logger = logging.getLogger(__name__)


class HistoryView(ft.Column):
    def __init__(self, controller: HistoryController, folder_picker: ft.FilePicker):
        super().__init__(expand=True, scroll="auto")
        self.controller = controller
        self.folder_picker = folder_picker
        self.selected_meeting_id = None

        self.folder_picker.on_result = self._on_folder_result

        self.history_list = ft.ListView(expand=True, spacing=10, padding=10)

        self.controls = [
            ft.Text("会議履歴", size=24, weight="bold"),
            ft.Text("過去の録音と議事録を確認・書き出せます。"),
            ft.Divider(),
            self.history_list,
        ]

    def init_view(self):
        self._refresh_history()

    def _refresh_history(self):
        self.history_list.controls.clear()
        meetings = self.controller.get_meetings()

        if not meetings:
            self.history_list.controls.append(ft.Text("履歴がありません。", italic=True, color="grey500"))
        else:
            for m in meetings:
                self.history_list.controls.append(self._build_meeting_card(m))

        if self.page:
            self.update()

    def _build_meeting_card(self, meeting):
        meeting_id = meeting["id"]
        timestamp = meeting["timestamp"]
        title = meeting["title"]
        has_minutes = bool(meeting["minutes"])
        audio_path = meeting["audio_path"]

        card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.RECORD_VOICE_OVER if not has_minutes else ft.icons.DESCRIPTION),
                            title=ft.Text(f"{title}"),
                            subtitle=ft.Text(f"日時: {timestamp}"),
                        ),
                        ft.Row(
                            [
                                ft.TextButton("詳細を表示", icon=ft.icons.BROWSE_GALLERY, on_click=lambda _: self._show_details(meeting)),
                                ft.TextButton(
                                    "音声を書き出し",
                                    icon=ft.icons.DOWNLOAD,
                                    on_click=lambda _: self._start_export(meeting_id),
                                    visible=bool(audio_path),
                                ),
                            ],
                            alignment="end",
                        ),
                    ],
                    spacing=0,
                ),
                padding=10,
            )
        )
        return card

    def _show_details(self, meeting):
        # Update app state to show this meeting's content in the transcription/minutes tabs
        state.set("transcript_text", meeting["transcript"])
        state.set("minutes_text", meeting["minutes"] or "（未生成）")

        # Simple snackbar
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"「{meeting['title']}」の内容を各タブにロードしました"))
            self.page.snack_bar.open = True
            self.page.update()

    def _start_export(self, meeting_id):
        self.selected_meeting_id = meeting_id
        self.folder_picker.get_directory_path()

    def _on_folder_result(self, e: ft.FilePickerResultEvent):
        if not e.path or not self.selected_meeting_id:
            return

        success, message = self.controller.export_audio(self.selected_meeting_id, e.path)

        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(message))
            self.page.snack_bar.open = True
            self.page.update()

        self.selected_meeting_id = None
