import logging
import os
import threading
import flet as ft

from src.config_manager import ConfigManager
from src.gemini_client import GeminiClient
from src.transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)


class FletApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Movie to Text v2.0"
        self.page.theme_mode = "dark"
        self.page.window_width = 1100
        self.page.window_height = 850
        self.page.padding = 0

        # Backend instances
        self.config_mgr = ConfigManager()
        self.transcriber = WhisperTranscriber()
        self.gemini_client = None
        
        # Hardware Info
        self.hw_info = self.transcriber.get_hardware_info()

        # UI Components
        self.setup_components()
        self.build_ui()
        self.load_settings()

    def setup_components(self):
        # File Pickers
        self.file_picker = ft.FilePicker()
        self.file_picker.on_result = self.on_file_result
        self.save_picker = ft.FilePicker()
        self.save_picker.on_result = self.on_save_result
        self.page.overlay.extend([self.file_picker, self.save_picker])

        # State Variables
        self.selected_file_path = ""
        self.transcript_text = ""
        self.minutes_text = ""

        # UI Components (Transcription)
        self.path_text = ft.Text("ファイルが選択されていません", color="grey500")
        
        # Generate model options with device labels
        hw = self.transcriber.get_hardware_info()
        model_options = []
        for model_name, req_gb in self.transcriber.MODEL_REQUIREMENTS.items():
            if self.transcriber.can_run_on_gpu(model_name):
                label = f"{model_name} (GPU - {req_gb:.0f}GB)"
            else:
                label = f"{model_name} (CPU - {req_gb:.0f}GB)"
            model_options.append(ft.dropdown.Option(key=model_name, text=label))

        self.model_dropdown = ft.Dropdown(
            label="Whisperモデル",
            options=model_options,
            value=self.config_mgr.get_whisper_model(),
            width=250,
        )
        self.model_dropdown.on_change = lambda e: self.config_mgr.set_whisper_model(e.control.value)

        self.transcribe_btn = ft.ElevatedButton(
            "文字起こし開始",
            icon="play_arrow",
            style=ft.ButtonStyle(color="white", bgcolor="green700"),
        )
        self.transcribe_btn.on_click = self.start_transcription

        self.status_text = ft.Text("待機中", color="grey400")
        self.progress_bar = ft.ProgressBar(width=400, color="blue", visible=False)

        self.result_area = ft.TextField(
            label="文字起こし結果",
            multiline=True,
            min_lines=15,
            max_lines=20,
            expand=True,
            read_only=False,
            text_size=14,
        )

        # UI Components (Minutes)
        self.gemini_model_dropdown = ft.Dropdown(
            label="Geminiモデル",
            options=[],
            width=300,
        )
        self.generate_btn = ft.ElevatedButton(
            "議事録を生成",
            icon="stars",
            bgcolor="blue700",
            color="white",
        )
        self.generate_btn.on_click = self.start_minutes_generation

        self.minutes_area = ft.TextField(
            label="生成された議事録",
            multiline=True,
            min_lines=20,
            max_lines=25,
            expand=True,
            read_only=False,
            text_size=14,
            bgcolor="grey900",
        )

        # UI Components (Settings)
        self.api_key_field = ft.TextField(
            label="Gemini API Key",
            password=True,
            can_reveal_password=True,
            width=500,
        )
        self.api_key_field.on_change = lambda e: self.config_mgr.set_api_key(e.control.value)

    def build_ui(self):
        # Navigation Rail
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type="all",
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon="mic",
                    selected_icon="mic",
                    label="文字起こし",
                ),
                ft.NavigationRailDestination(
                    icon="stars",
                    selected_icon="stars",
                    label="AI議事録",
                ),
                ft.NavigationRailDestination(
                    icon="settings",
                    selected_icon="settings",
                    label="設定",
                ),
            ],
        )
        self.nav_rail.on_change = self.on_nav_change

        # Content Container
        self.content_container = ft.Container(
            content=self.get_transcription_view(),
            expand=True,
            padding=20,
        )

        # Layout
        self.page.add(
            ft.Row(
                [
                    self.nav_rail,
                    ft.VerticalDivider(width=1),
                    self.content_container,
                ],
                expand=True,
            )
        )

    # --- View Generators ---

    def get_transcription_view(self):
        return ft.Column(
            [
                ft.Text("文字起こし (Whisper)", size=24, weight="bold"),
                ft.Row([
                    ft.ElevatedButton("動画ファイルを選択", icon="folder_open", on_click=lambda _: self.file_picker.pick_files()),
                    self.path_text,
                ]),
                ft.Row([self.model_dropdown, self.transcribe_btn]),
                self.status_text,
                self.progress_bar,
                self.result_area,
                ft.Row([
                    ft.ElevatedButton("結果を保存", icon="save", on_click=self.handle_save_transcript),
                ], alignment="end"),
            ],
            scroll="auto",
            expand=True,
        )

    def get_minutes_view(self):
        return ft.Column(
            [
                ft.Text("AI議事録生成 (Gemini)", size=24, weight="bold"),
                ft.Row([
                    self.gemini_model_dropdown,
                    ft.IconButton("refresh", on_click=self.refresh_gemini_models),
                    self.generate_btn,
                ]),
                ft.Text("※ 文字起こしが完了している場合、最新のテキストが使用されます。"),
                self.minutes_area,
                ft.Row([
                    ft.ElevatedButton("議事録を保存", icon="save", on_click=self.handle_save_minutes),
                ], alignment="end"),
            ],
            scroll="auto",
            expand=True,
        )

    def get_settings_view(self):

        # Hardware display
        hw_rows = [
            ft.Row([ft.Icon("computer"), ft.Text(f"System RAM: {self.hw_info['ram']} GB")]),
            ft.Row([ft.Icon("storage"), ft.Text(f"GPU VRAM: {self.hw_info['vram']} GB")]),
        ]

        # Model compatibility list
        comp_items = []
        for model, req in self.transcriber.MODEL_REQUIREMENTS.items():
            can_gpu = self.hw_info['vram'] >= req
            can_cpu = self.hw_info['ram'] >= req
            status_icon = "check_circle" if (can_gpu or can_cpu) else "cancel"
            status_color = "green" if can_gpu else ("amber" if can_cpu else "red")
            device_text = "(GPU可)" if can_gpu else ("(CPUのみ可)" if can_cpu else "(スペック不足)")
            
            comp_items.append(
                ft.ListTile(
                    leading=ft.Icon(status_icon, color=status_color),
                    title=ft.Text(f"{model} (要 {req}GB)"),
                    subtitle=ft.Text(device_text),
                )
            )

        return ft.Column(
            [
                ft.Text("設定", size=24, weight="bold"),
                ft.Divider(),
                ft.Text("API 設定", size=18, weight="w500"),
                self.api_key_field,
                ft.Divider(),
                ft.Text("ハードウェア情報", size=18, weight="w500"),
                ft.Column(hw_rows),
                ft.Text("モデル適合状況 (目安):", size=14, italic=True),
                ft.Container(
                    content=ft.Column(comp_items, spacing=0),
                    border=ft.border.all(1, "grey700"),
                    border_radius=10,
                    padding=10,
                ),
            ],
            scroll="auto",
            expand=True,
        )

    # --- Event Handlers ---

    def on_nav_change(self, e):
        idx = e.control.selected_index
        if idx == 0:
            self.content_container.content = self.get_transcription_view()
        elif idx == 1:
            self.content_container.content = self.get_minutes_view()
            self.load_gemini_models_to_dropdown()
        elif idx == 2:
            self.content_container.content = self.get_settings_view()
            self.load_settings()
        self.page.update()

    def on_file_result(self, e):
        if e.files:
            self.selected_file_path = e.files[0].path
            self.path_text.value = os.path.basename(self.selected_file_path)
            self.page.update()

    def handle_save_transcript(self, e):
        base_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] if self.selected_file_path else "transcript"
        default_name = f"【文字起こし】{base_name}.txt"
        self.save_picker.save_file(file_name=default_name)

    def handle_save_minutes(self, e):
        base_name = os.path.splitext(os.path.basename(self.selected_file_path))[0] if self.selected_file_path else "minutes"
        default_name = f"【議事録】{base_name}.md"
        self.save_picker.save_file(file_name=default_name)

    def on_save_result(self, e):
        if e.path:
            # Check file extension to decide content
            is_md = e.path.endswith(".md")
            content = self.minutes_area.value if is_md else self.result_area.value
            try:
                with open(e.path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.show_snack(f"ファイルを保存しました: {os.path.basename(e.path)}")
            except Exception as ex:
                self.show_snack(f"保存失敗: {ex}")

    def load_settings(self):
        self.api_key_field.value = self.config_mgr.get_api_key()
        # Initial model loading for Gemini if possible
        if self.api_key_field.value:
            threading.Thread(target=self.silent_refresh_gemini, daemon=True).start()

    def silent_refresh_gemini(self):
        try:
            if not self.gemini_client:
                self.gemini_client = GeminiClient(self.api_key_field.value)
            self.load_gemini_models_to_dropdown()
        except:
            pass

    def load_gemini_models_to_dropdown(self):
        if self.gemini_client:
            models = self.gemini_client.get_available_models()
            self.gemini_model_dropdown.options = [ft.dropdown.Option(m) for m in models]
            last = self.config_mgr.get_last_model()
            if last in models:
                self.gemini_model_dropdown.value = last
            elif models:
                self.gemini_model_dropdown.value = models[0]
            self.page.update()

    def refresh_gemini_models(self, e):
        api_key = self.api_key_field.value
        if not api_key:
            self.show_snack("APIキーを入力してください")
            return
        
        try:
            self.gemini_client = GeminiClient(api_key)
            self.load_gemini_models_to_dropdown()
            self.show_snack("モデルリストを更新しました")
        except Exception as ex:
            self.show_snack(f"取得失敗: {ex}")

    def show_snack(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    # --- Business Logic Threads ---

    def start_transcription(self, e):
        if not self.selected_file_path:
            self.show_snack("ファイルを選択してください")
            return
        
        model_name = self.model_dropdown.value
        self.transcribe_btn.disabled = True
        self.progress_bar.visible = True
        self.status_text.value = "文字起こし中... (初回モデルDL時は時間がかかります)"
        self.page.update()

        threading.Thread(target=self._transcribe_worker, args=(model_name,), daemon=True).start()

    def _transcribe_worker(self, model_name):
        try:
            text = self.transcriber.transcribe(self.selected_file_path, model_name)
            self.transcript_text = text
            self.result_area.value = text
            self.status_text.value = "文字起こし完了"
        except Exception as ex:
            logger.error(f"Transcription error: {ex}")
            self.status_text.value = f"エラー: {ex}"
        finally:
            self.transcribe_btn.disabled = False
            self.progress_bar.visible = False
            self.page.update()

    def start_minutes_generation(self, e):
        text = self.result_area.value
        if not text:
            self.show_snack("文字起こしテキストがありません")
            return
        
        model = self.gemini_model_dropdown.value
        if not model:
            self.show_snack("Geminiモデルを選択してください")
            return

        self.generate_btn.disabled = True
        self.minutes_area.value = "議事録を生成中..."
        self.page.update()

        threading.Thread(target=self._minutes_worker, args=(text, model), daemon=True).start()

    def _minutes_worker(self, transcript, model):
        try:
            res = self.gemini_client.generate_minutes(transcript, model)
            self.minutes_area.value = res
            self.minutes_text = res
        except Exception as ex:
            self.minutes_area.value = f"エラー: {ex}"
        finally:
            self.generate_btn.disabled = False
            self.page.update()
