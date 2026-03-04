import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from src.transcriber import WhisperTranscriber
from src.config_manager import ConfigManager
from src.gemini_client import GeminiClient

class WhisperApp:
    """
    Frontend class for the Whisper GUI.
    Handles UI elements and user interactions.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Movie to Text (Whisper) + AI Minutes")
        self.root.geometry("1000x800")

        # Config Manager
        self.config_mgr = ConfigManager()

        # Backend instance
        self.transcriber = WhisperTranscriber()
        self.gemini_client = None
        
        # UI Setup
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        # Create Main PanedWindow
        self.paned = tk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Upper Section (Transcription)
        upper_frame = tk.Frame(self.paned)
        self.paned.add(upper_frame, height=450)

        # File selection area
        file_frame = tk.Frame(upper_frame, pady=10)
        file_frame.pack(fill=tk.X, padx=20)

        tk.Label(file_frame, text="動画ファイル:").pack(side=tk.LEFT)
        self.entry_path = tk.Entry(file_frame, width=60)
        self.entry_path.pack(side=tk.LEFT, padx=5)
        
        btn_browse = tk.Button(file_frame, text="選択...", command=self.select_file)
        btn_browse.pack(side=tk.LEFT)

        # Control area
        control_frame = tk.Frame(upper_frame, pady=5)
        control_frame.pack(fill=tk.X, padx=20)

        self.btn_transcribe = tk.Button(
            control_frame, 
            text="文字起こし開始", 
            command=self.start_transcription,
            bg="#4CAF50", 
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.btn_transcribe.pack(side=tk.LEFT)

        self.lbl_status = tk.Label(control_frame, text="待機中", fg="gray")
        self.lbl_status.pack(side=tk.LEFT, padx=20)

        # Output area (Transcript)
        tk.Label(upper_frame, text="文字起こし結果 (編集可能):").pack(anchor=tk.W, padx=20)
        self.text_result = scrolledtext.ScrolledText(upper_frame, wrap=tk.WORD, font=("Meiryo", 10))
        self.text_result.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Save area
        save_frame = tk.Frame(upper_frame, pady=5)
        save_frame.pack(fill=tk.X, padx=20)

        self.btn_save_transcript = tk.Button(
            save_frame, 
            text="文字起こしを保存...", 
            command=lambda: self.save_file(self.text_result, "transcript"),
            state=tk.DISABLED
        )
        self.btn_save_transcript.pack(side=tk.RIGHT)

        # Lower Section (AI Minutes)
        lower_frame = tk.LabelFrame(self.paned, text="AI議事録作成 (Gemini)", pady=10)
        self.paned.add(lower_frame, height=350)

        # Gemini Settings Area
        settings_frame = tk.Frame(lower_frame)
        settings_frame.pack(fill=tk.X, padx=20)

        tk.Label(settings_frame, text="Gemini API Key:").pack(side=tk.LEFT)
        self.entry_api_key = tk.Entry(settings_frame, width=30, show="*")
        self.entry_api_key.pack(side=tk.LEFT, padx=5)
        self.entry_api_key.bind("<FocusOut>", lambda e: self.config_mgr.set_api_key(self.entry_api_key.get()))

        tk.Label(settings_frame, text="モデル:").pack(side=tk.LEFT, padx=(15, 0))
        self.combo_model = ttk.Combobox(settings_frame, width=25, state="readonly")
        self.combo_model.pack(side=tk.LEFT, padx=5)
        self.combo_model.bind("<<ComboboxSelected>>", lambda e: self.config_mgr.set_last_model(self.combo_model.get()))

        btn_refresh = tk.Button(settings_frame, text="モデル取得", command=self.refresh_gemini_models)
        btn_refresh.pack(side=tk.LEFT, padx=5)

        self.btn_generate_minutes = tk.Button(
            settings_frame, 
            text="議事録生成", 
            command=self.start_minutes_generation,
            bg="#2196F3",
            fg="white",
            state=tk.DISABLED
        )
        self.btn_generate_minutes.pack(side=tk.LEFT, padx=10)

        # Minutes Result Area
        self.text_minutes = scrolledtext.ScrolledText(lower_frame, wrap=tk.WORD, font=("Meiryo", 10), bg="#F5F5F5")
        self.text_minutes.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        btn_save_minutes = tk.Button(
            lower_frame,
            text="議事録を保存...",
            command=lambda: self.save_file(self.text_minutes, "minutes")
        )
        btn_save_minutes.pack(side=tk.RIGHT, padx=20, pady=5)

    def load_settings(self):
        """Loads saved settings from ConfigManager."""
        api_key = self.config_mgr.get_api_key()
        if api_key:
            self.entry_api_key.insert(0, api_key)
        
        last_model = self.config_mgr.get_last_model()
        if last_model:
            self.combo_model.set(last_model)

    def select_file(self):
        filename = filedialog.askopenfilename(
            title="動画ファイルを選択",
            filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.flv *.ts"), ("All files", "*.*")]
        )
        if filename:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, filename)

    def start_transcription(self):
        video_path = self.entry_path.get()
        if not video_path:
            messagebox.showwarning("警告", "動画ファイルを選択してください。")
            return
        
        if not os.path.exists(video_path):
            messagebox.showerror("エラー", "ファイルが見つかりません。")
            return

        self.toggle_ui(False)
        self.lbl_status.config(text="処理中... (初回はモデルのダウンロードが発生する場合があります)", fg="blue")
        self.text_result.delete(1.0, tk.END)
        
        # Run in worker thread
        threading.Thread(target=self._run_transcription_thread, args=(video_path,), daemon=True).start()

    def _run_transcription_thread(self, path):
        try:
            # Load and transcribe using the backend
            self.transcriber.load_model("base")
            text = self.transcriber.transcribe(path)

            self.root.after(0, self.on_transcription_complete, text)
        except Exception as e:
            error_msg = str(e)
            if "ffmpeg" in error_msg.lower():
                error_msg = "FFmpegが見つかりません。システムにインストールしてパスを通してください。"
            self.root.after(0, self.on_transcription_error, error_msg)

    def on_transcription_complete(self, text):
        self.text_result.insert(tk.END, text)
        self.lbl_status.config(text="完了", fg="green")
        self.btn_save_transcript.config(state=tk.NORMAL)
        self.btn_generate_minutes.config(state=tk.NORMAL)
        self.toggle_ui(True)
        messagebox.showinfo("完了", "文字起こしが完了しました。")

    def on_transcription_error(self, error):
        self.lbl_status.config(text="エラー発生", fg="red")
        self.toggle_ui(True)
        messagebox.showerror("エラー", f"文字起こし中にエラーが発生しました:\n{error}")

    def toggle_ui(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_transcribe.config(state=state)

    def refresh_gemini_models(self):
        api_key = self.entry_api_key.get()
        if not api_key:
            messagebox.showwarning("警告", "APIキーを入力してください。")
            return

        try:
            self.gemini_client = GeminiClient(api_key)
            models = self.gemini_client.get_available_models()
            self.combo_model["values"] = models
            if models:
                if self.config_mgr.get_last_model() in models:
                    self.combo_model.set(self.config_mgr.get_last_model())
                else:
                    self.combo_model.current(0)
            messagebox.showinfo("成功", "利用可能なモデルリストを更新しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"モデルの取得に失敗しました:\n{e}")

    def start_minutes_generation(self):
        transcript = self.text_result.get(1.0, tk.END).strip()
        if not transcript:
            messagebox.showwarning("警告", "文字起こしテキストが空です。")
            return

        api_key = self.entry_api_key.get()
        model_name = self.combo_model.get()

        if not api_key or not model_name:
            messagebox.showwarning("警告", "APIキーとモデルを選択してください。")
            return

        self.btn_generate_minutes.config(state=tk.DISABLED)
        self.text_minutes.delete(1.0, tk.END)
        self.text_minutes.insert(tk.END, "議事録を生成中...")
        
        threading.Thread(target=self._run_minutes_thread, args=(transcript, api_key, model_name), daemon=True).start()

    def _run_minutes_thread(self, transcript, api_key, model_name):
        try:
            if not self.gemini_client:
                self.gemini_client = GeminiClient(api_key)
            
            minutes = self.gemini_client.generate_minutes(transcript, model_name)
            self.root.after(0, self.on_minutes_complete, minutes)
        except Exception as e:
            self.root.after(0, self.on_minutes_error, str(e))

    def on_minutes_complete(self, minutes):
        self.text_minutes.delete(1.0, tk.END)
        self.text_minutes.insert(tk.END, minutes)
        self.btn_generate_minutes.config(state=tk.NORMAL)
        messagebox.showinfo("完了", "議事録の生成が完了しました。")

    def on_minutes_error(self, error):
        self.text_minutes.delete(1.0, tk.END)
        self.text_minutes.insert(tk.END, f"エラー: {error}")
        self.btn_generate_minutes.config(state=tk.NORMAL)
        messagebox.showerror("エラー", f"議事録生成中にエラーが発生しました:\n{error}")

    def save_file(self, text_widget, default_name):
        text_content = text_widget.get(1.0, tk.END).strip()
        if not text_content:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")],
            title=f"{default_name}の保存先を指定"
        )
        
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
                messagebox.showinfo("保存完了", f"ファイルが正常に保存されました:\n{save_path}")
            except Exception as e:
                messagebox.showerror("保存エラー", f"保存中にエラーが発生しました:\n{e}")
