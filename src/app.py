import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from src.transcriber import WhisperTranscriber

class WhisperApp:
    """
    Frontend class for the Whisper GUI.
    Handles UI elements and user interactions.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Movie to Text (Whisper)")
        self.root.geometry("800x600")

        # Backend instance
        self.transcriber = WhisperTranscriber()
        
        # UI Setup
        self.setup_ui()

    def setup_ui(self):
        # File selection area
        file_frame = tk.Frame(self.root, pady=10)
        file_frame.pack(fill=tk.X, padx=20)

        tk.Label(file_frame, text="動画ファイル:").pack(side=tk.LEFT)
        self.entry_path = tk.Entry(file_frame, width=60)
        self.entry_path.pack(side=tk.LEFT, padx=5)
        
        btn_browse = tk.Button(file_frame, text="選択...", command=self.select_file)
        btn_browse.pack(side=tk.LEFT)

        # Control area
        control_frame = tk.Frame(self.root, pady=10)
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

        # Output area
        tk.Label(self.root, text="文字起こし結果:").pack(anchor=tk.W, padx=20)
        self.text_result = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Meiryo", 10))
        self.text_result.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Save area
        save_frame = tk.Frame(self.root, pady=10)
        save_frame.pack(fill=tk.X, padx=20)

        self.btn_save = tk.Button(
            save_frame, 
            text="テキストとして保存...", 
            command=self.save_file,
            state=tk.DISABLED
        )
        self.btn_save.pack(side=tk.RIGHT)

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
        self.btn_save.config(state=tk.NORMAL)
        self.toggle_ui(True)
        messagebox.showinfo("完了", "文字起こしが完了しました。")

    def on_transcription_error(self, error):
        self.lbl_status.config(text="エラー発生", fg="red")
        self.toggle_ui(True)
        messagebox.showerror("エラー", f"文字起こし中にエラーが発生しました:\n{error}")

    def toggle_ui(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_transcribe.config(state=state)

    def save_file(self):
        text_content = self.text_result.get(1.0, tk.END).strip()
        if not text_content:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")],
            title="保存先を指定"
        )
        
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
                messagebox.showinfo("保存完了", f"ファイルが正常に保存されました:\n{save_path}")
            except Exception as e:
                messagebox.showerror("保存エラー", f"保存中にエラーが発生しました:\n{e}")
