# Transform Movie to Text (+ AI Minutes)

動画ファイルから音声を高精度に文字起こしし、Google Gemini APIを活用してAI議事録を自動生成するWindows向けデスクトップアプリケーションです。

## 主な機能 (Features)
- **高品質文字起こし**: OpenAIの軽量かつ高精度なローカルモデル（Whisper）を使用して、動画・音声ファイルからテキストを生成します。
- **AI議事録生成 (Gemini)**: 文字起こししたテキストをもとに、Gemini APIを用いて「会議の概要」「決定事項」「ネクストアクション」を自動で要約・抽出します。
- **モデルの自動取得**: Gemini APIの利用可能な最新・最適なモデルを自動的に取得して選択可能です。
- **GPU対応**: NVIDIA GPU搭載PCではCUDAを活用した超高速な文字起こしが可能です。
- **環境構築不要**: GitHub Releasesからダウンロード可能なStandalone版(`.exe`)を提供しています。

## 使い方 (How to Use)
### 方法1: 実行ファイル (.exe) を使う（おすすめ）
最も簡単な方法です。Pythonの環境構築は必要ありません。

1. [Releasesページ](https://github.com/Ayato-AI-for-Auto/Transform_MovieToText/releases) にアクセスします。
2. 環境に合わせてZIPファイルをダウンロード・展開します。
   - `TransformMovieToText-Windows-gpu.zip` : NVIDIA GPU搭載PC用（高速）
   - `TransformMovieToText-Windows-cpu.zip` : GPU非搭載のPC用（軽量）
3. 展開したフォルダ内の `TransformMovieToText.exe` をダブルクリックで起動します。

※ **補足**: AI議事録生成機能の利用には、無料の [Google AI Studio API Key](https://aistudio.google.com/app/apikey) が必要です。

---

### 方法2: ソースコードから実行する
開発やカスタマイズを行いたい場合は、ソースコードから実行できます。

**必須要件**:
- Python 3.10以降
- [uv](https://github.com/astral-sh/uv) (高速なPythonパッケージマネージャ)
- FFmpeg (システムにインストールされ、PATHが通っていること)

**セットアップ手順**:
```bash
# クローンと依存関係のインストール
git clone https://github.com/Ayato-AI-for-Auto/Transform_MovieToText.git
cd Transform_MovieToText

# uvを利用したローカルインストール
uv pip install -e .

# [GPUを使う場合] CUDA版のPyTorchをインストール
uv pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121

# 起動
uv run main.py
```

## ソースからEXEをビルドする
もし自分で実行ファイル (`.exe`) を構築したい場合は、プロジェクトに同梱されているビルドスクリプトを利用します。
```bash
python scripts/build_exe.py
```
このスクリプトは、ローカル環境のGPUの有無を自動判定し、最適なバージョンのPyInstallerビルドを実行します。
