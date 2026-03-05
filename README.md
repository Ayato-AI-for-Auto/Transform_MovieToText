# Transform Movie to Text (+ AI Minutes)

動画ファイルやPC内部の音声から高精度に文字起こしし、複数のAIプロバイダー（Gemini / Ollama Cloud / OpenAI互換）を活用して議事録を自動生成する **Windows向け** デスクトップアプリケーションです。

> **Note**: 本ツールは **Windows 環境** で開発・テストされています。
> macOS / Linux では、WASAPI Loopback（システム音キャプチャ）や `run.bat` による自動環境構築など、OS固有の機能が動作しません。
> 他OSでの動作は一切保証しておらず、サポートも行いません。

## 主な機能 (Features)

- **高品質文字起こし**: OpenAIのローカルモデル（Whisper）を使用して、動画・音声ファイルからテキストを生成します。
- **システム音ライブ録音**: PCから出力されているあらゆる音声（YouTube, Zoom, Teams等）をリアルタイムでキャプチャし、文字起こしできます。録音ファイルは処理後に自動で削除されます。
- **AI議事録生成（マルチプロバイダー対応）**: Gemini, Ollama Cloud, OpenAI互換API（Groq等）を切り替えて利用可能。文字起こしテキストから「会議の概要」「決定事項」「ネクストアクション」を自動で要約・抽出します。
- **GPU対応**: NVIDIA GPU搭載PCではCUDAを活用した高速な文字起こしが可能です。

## 動作環境

| 項目 | 要件 |
|------|------|
| **OS** | **Windows 10 / 11**（必須） |
| **FFmpeg** | システムにインストールされ、PATHが通っていること |
| **GPU** | NVIDIA GPU（CUDA対応）があれば高速化。なくても動作可能 |
| **Python** | `run.bat` が自動でインストールするため、手動導入は不要 |

### 重要: システム音の録音について

「PC音声を録音して文字起こし」機能（会議の文字起こし等）を利用するには、Windows 側で **「ステレオ ミキサー」** を有効にする必要があります。

1. **[設定] > [システム] > [サウンド] > [詳細設定] > [サウンドの設定]** (サウンド コントロール パネル) を開きます。
2. **[録音]** タブを選択します。
3. リスト内の **「ステレオ ミキサー」** を右クリックし、**[有効]** を選択します。
   - 表示されない場合は、リストの何もないところを右クリックし、[無効なデバイスの表示] にチェックを入れてください。
4. ステレオ ミキサーが「既定のデバイス」である必要はありませんが、「準備完了」状態でメーターが動く必要があります。

## 使い方 (How to Use)

### Thin Client インストール（推奨）

環境構築は `run.bat` が全自動で行います。Pythonのインストールすら不要です。

1. [Releases ページ](https://github.com/Ayato-AI-for-Auto/Transform_MovieToText/releases) から最新の `TransformMovieToText-Windows-ThinClient.zip` をダウンロードします。
2. ZIP を展開し、`run.bat` をダブルクリックします。
3. 初回起動時に以下が自動実行されます：
   - **uv**（高速パッケージマネージャ）のダウンロード
   - **Python 3.11** のインストール（システムを汚しません）
   - **PyTorch 等の全依存ライブラリ**のインストール
4. 2回目以降は一瞬で起動します。

### ソースコードから実行する

開発やカスタマイズを行いたい場合：

```bash
git clone https://github.com/Ayato-AI-for-Auto/Transform_MovieToText.git
cd Transform_MovieToText

# uvを利用したローカルインストール
uv pip install -e .

# [GPUを使う場合] CUDA版のPyTorchをインストール
uv pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121

# 起動
uv run main.py
```

## 開発スタンスについて

本ツールは**開発者自身が使うために作られたもの**であり、「ついでに公開している」というスタンスです。
詳しくは [docs/設計思想.md](docs/設計思想.md) をご覧ください。

- 環境構築の自動化は提供しますが、**個別環境のバグ対応やサポートは行いません。**
- ご利用は **As-Is（現状有姿）** です。

## License

[Apache License 2.0](LICENSE)
