import flet as ft

from src.config_manager import ConfigManager


class SettingsView(ft.Column):
    def __init__(self, config_mgr: ConfigManager, hw_info: dict, model_requirements: dict):
        super().__init__(expand=True, scroll="auto")
        self.config_mgr = config_mgr
        self.hw_info = hw_info
        self.model_requirements = model_requirements

        # Initialize UI Components
        self.gemini_api_key = ft.TextField(
            label="Gemini API Key", password=True, can_reveal_password=True, width=500,
            on_change=self._on_settings_change
        )
        self.ollama_local_url = ft.TextField(
            label="Ollama Local Base URL", width=500, hint_text="http://localhost:11434",
            on_change=self._on_settings_change
        )
        self.ollama_cloud_api_key = ft.TextField(
            label="Ollama Cloud API Key", password=True, can_reveal_password=True, width=500,
            on_change=self._on_settings_change
        )
        self.ollama_cloud_url = ft.TextField(
            label="Ollama Cloud URL", width=500, hint_text="https://ollama.com",
            on_change=self._on_settings_change
        )
        self.force_gpu_checkbox = ft.Checkbox(
            label="GPUを強制使用する (VRAM不足警告を無視)",
            on_change=self._on_force_gpu_change
        )

        # Hardware display
        self.hw_rows = ft.Column([
            ft.Row([ft.Icon("computer"), ft.Text(f"System RAM: {hw_info['ram']} GB")]),
            ft.Row([ft.Icon("storage"), ft.Text(f"GPU VRAM: {hw_info['vram']} GB")]),
        ])

        # Model compatibility list
        self.comp_items = ft.Column(spacing=0)
        self._build_compatibility_list()

        # Build Layout
        self.controls = [
            ft.Text("設定", size=24, weight="bold"),
            ft.Divider(),
            ft.Text("AIプロバイダー設定", size=18, weight="w500"),
            self._create_card("Google Gemini", [self.gemini_api_key]),
            self._create_card("Ollama Local (ローカルまたはPattern 1)", [self.ollama_local_url]),
            self._create_card("Ollama Cloud (クラウドAPIを消費)", [self.ollama_cloud_api_key, self.ollama_cloud_url]),
            ft.Divider(),
            ft.Text("ハードウェア情報", size=18, weight="w500"),
            self.hw_rows,
            ft.Text("モデル適合状況 (目安):", size=14, italic=True),
            ft.Container(
                content=self.comp_items,
                border=ft.border.all(1, "grey700"),
                border_radius=10,
                padding=10,
            ),
            ft.Divider(),
            ft.Text("Whisper設定", size=18, weight="w500"),
            self.force_gpu_checkbox,
        ]

    def _create_card(self, title: str, controls: list):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([ft.Text(title, weight="bold")] + controls),
                padding=15
            )
        )

    def _build_compatibility_list(self):
        self.comp_items.controls.clear()
        for model, req in self.model_requirements.items():
            can_gpu = self.hw_info["vram"] >= req
            can_cpu = self.hw_info["ram"] >= req
            status_icon = "check_circle" if (can_gpu or can_cpu) else "cancel"
            status_color = "green" if can_gpu else ("amber" if can_cpu else "red")
            device_text = "(GPU可)" if can_gpu else ("(CPUのみ可)" if can_cpu else "(スペック不足)")

            self.comp_items.controls.append(
                ft.ListTile(
                    leading=ft.Icon(status_icon, color=status_color),
                    title=ft.Text(f"{model} (要 {req}GB)"),
                    subtitle=ft.Text(device_text),
                )
            )

    def _on_settings_change(self, e):
        self.config_mgr.set_provider_config("gemini", {"api_key": self.gemini_api_key.value})
        self.config_mgr.set_provider_config("ollama_local", {"base_url": self.ollama_local_url.value})
        self.config_mgr.set_provider_config("ollama_cloud", {
            "api_key": self.ollama_cloud_api_key.value,
            "base_url": self.ollama_cloud_url.value
        })

    def _on_force_gpu_change(self, e):
        self.config_mgr.set_force_gpu(e.control.value)

    def init_view(self):
        gemini_conf = self.config_mgr.get_provider_config("gemini")
        self.gemini_api_key.value = gemini_conf.get("api_key", "")
        
        ollama_local_conf = self.config_mgr.get_provider_config("ollama_local")
        self.ollama_local_url.value = ollama_local_conf.get("base_url", "http://localhost:11434")
        
        ollama_cloud_conf = self.config_mgr.get_provider_config("ollama_cloud")
        self.ollama_cloud_api_key.value = ollama_cloud_conf.get("api_key", "")
        self.ollama_cloud_url.value = ollama_cloud_conf.get("base_url", "https://ollama.com")
        
        self.force_gpu_checkbox.value = self.config_mgr.get_force_gpu()
        if self.page:
            self.update()
