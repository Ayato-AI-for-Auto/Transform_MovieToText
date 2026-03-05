import logging

import flet as ft

from src.ui.views.minutes_view import MinutesView
from src.ui.views.settings_view import SettingsView
from src.ui.views.transcription_view import TranscriptionView

logger = logging.getLogger(__name__)


class MainWindow(ft.Row):
    def __init__(self, transcription_view: TranscriptionView, minutes_view: MinutesView, settings_view: SettingsView):
        super().__init__(expand=True)
        self.transcription_view = transcription_view
        self.minutes_view = minutes_view
        self.settings_view = settings_view

        # Navigation Rail
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type="all",
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(icon="mic", selected_icon="mic", label="文字起こし"),
                ft.NavigationRailDestination(icon="stars", selected_icon="stars", label="AI議事録"),
                ft.NavigationRailDestination(icon="settings", selected_icon="settings", label="設定"),
            ],
            on_change=self._on_nav_change
        )

        # Content Container
        self.content_container = ft.Container(
            content=self.transcription_view,
            expand=True,
            padding=20,
        )

        self.controls = [
            self.nav_rail,
            ft.VerticalDivider(width=1),
            self.content_container,
        ]

    def _on_nav_change(self, e):
        idx = e.control.selected_index
        logger.info(f"Navigation changed to index: {idx}")
        try:
            if idx == 0:
                self.content_container.content = self.transcription_view
            elif idx == 1:
                self.content_container.content = self.minutes_view
                self.content_container.update()
                self.minutes_view.init_view()
            elif idx == 2:
                self.content_container.content = self.settings_view
                self.content_container.update()
                self.settings_view.init_view()
            
            logger.info("Updating main window/page...")
            if self.page:
                self.page.update()
            else:
                self.update()
        except Exception as ex:
            logger.error(f"Error in navigation: {ex}", exc_info=True)
