import logging
import os
import threading

import flet as ft

from src.controllers.minutes_ctrl import MinutesController
from src.core.state import state

logger = logging.getLogger(__name__)


class MinutesView(ft.Column):
    def __init__(self, controller: MinutesController, save_picker: ft.FilePicker):
        super().__init__(expand=True, scroll="auto")
        self.controller = controller
        self.save_picker = save_picker

        # Initialize UI Components
        self.llm_provider_dropdown = ft.Dropdown(
            label="AIプロバイダー",
            options=[
                ft.dropdown.Option("gemini", "Gemini (Google)"),
                ft.dropdown.Option("ollama_local", "Ollama Local (ローカル資源/Pattern 1)"),
                ft.dropdown.Option("ollama_cloud", "Ollama Cloud (API直接/Pattern 2)"),
            ],
            width=200,
            on_change=self._on_provider_change,
        )

        self.llm_model_dropdown = ft.Dropdown(
            label="モデルを選択",
            options=[],
            width=250,
        )

        self.generate_btn = ft.ElevatedButton(
            "議事録を生成",
            icon="stars",
            bgcolor="blue700",
            color="white",
            on_click=self._on_generate_click,
        )

        self.minutes_area = ft.TextField(
            label="生成された議事録",
            multiline=True,
            min_lines=20,
            max_lines=25,
            expand=True,
            read_only=False,
            text_size=14,
            bgcolor="grey900",
            on_change=self._on_minutes_change
        )

        # Build Layout
        self.controls = [
            ft.Text("AI議事録生成", size=24, weight="bold"),
            ft.Row([
                self.llm_provider_dropdown,
                self.llm_model_dropdown,
                ft.IconButton("refresh", on_click=self._on_refresh_models),
                self.generate_btn,
            ]),
            ft.Text("※ 文字起こしが完了している場合、最新のテキストが使用されます。"),
            self.minutes_area,
            ft.Row([
                ft.ElevatedButton("議事録を保存", icon="save", on_click=self._on_save_click),
            ], alignment="end"),
        ]

        # Subscribe to state changes
        state.subscribe("minutes_text", self._update_minutes)
        state.subscribe("is_processing", self._update_processing_ui)

    def _update_minutes(self, val):
        self.minutes_area.value = val
        if self.page:
            self.update()

    def _update_processing_ui(self, is_processing):
        self.generate_btn.disabled = is_processing
        if self.page:
            self.update()

    def _on_provider_change(self, e):
        provider = e.control.value
        state.set("llm_provider", provider)
        self.controller.config_mgr.set_active_provider(provider)
        self._refresh_models()

    def _on_refresh_models(self, e=None):
        self._refresh_models()

    def _refresh_models(self):
        provider = state.get("llm_provider")
        self.llm_model_dropdown.options = [ft.dropdown.Option("読み込み中...")]
        self.llm_model_dropdown.disabled = True
        if self.page:
            self.update()

        def _fetch_worker():
            try:
                models = self.controller.get_available_models(provider)
                
                self.llm_model_dropdown.options = [ft.dropdown.Option(m) for m in models]
                if models:
                    last_model = self.controller.config_mgr.get_last_model(provider)
                    self.llm_model_dropdown.value = last_model if last_model in models else models[0]
                else:
                    self.llm_model_dropdown.value = None
                
                state.set("llm_model", self.llm_model_dropdown.value)
                self.llm_model_dropdown.disabled = False
                if self.page:
                    self.update()
            except Exception as e:
                logger.error(f"Error fetching models in thread: {e}")
                self.llm_model_dropdown.disabled = False
                if self.page:
                    self.update()

        threading.Thread(target=_fetch_worker, daemon=True).start()

    def _on_generate_click(self, e):
        transcript = state.get("transcript_text")
        provider = state.get("llm_provider")
        model = self.llm_model_dropdown.value
        self.controller.generate_minutes(transcript, provider, model)

    def _on_save_click(self, e):
        path = state.get("selected_file_path")
        base_name = os.path.splitext(os.path.basename(path))[0] if path else "minutes"
        self.save_picker.save_file(file_name=f"【議事録】{base_name}.md")

    def _on_minutes_change(self, e):
        state.set("minutes_text", e.control.value, notify=False)

    def init_view(self):
        """Called when view becomes active."""
        active_provider = self.controller.config_mgr.get_active_provider()
        self.llm_provider_dropdown.value = active_provider
        state.set("llm_provider", active_provider, notify=False)
        self._refresh_models()
        if self.page:
            self.update()
