# ReCiel

> Generic Discord Bot built with discord.py.

discord.py で構築された、多目的で拡張可能な Discord ボットです。

## ✨ 機能 (Features)

### 🛠️ 汎用 (General)

- **/ping** : 応答速度の表示
- **/help** : コマンド一覧・詳細表示
- **エラー通知** : コマンド実行時のエラーをEmbedで通知

### 🎵 音楽 (Music)

Youtubeなどの動画URLから音声を再生する機能

- **/search-all [word]** : キーワードで動画を検索し、結果から選択して再生
- **/play [URL]** : 指定した動画URLの音声を再生
- **/autoplay [word]** : キーワードに適した楽曲をAIが自動で選曲

### 👑 開発者用 (Develop)

Botのオーナーのみが使用できる機能

- **/reload** : extensionのホットリロード
- **/sync** : 手動でのコマンド同期
- **/map** : コマンド情報の詳細確認

## 🚀 導入方法 (Getting Started)

### 必要なもの (Requirements)

- Python 3.13 以上
- [uv](https://github.com/astral-sh/uv) (高速なPythonパッケージインストーラー兼リゾルバー)
- Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications)から取得可能)
- Google API Key ([Google Cloud Platform](https://console.cloud.google.com)から取得可能 以下のAPIを有効化)
  - Youtube Data API v3
  - Generative Language API

### インストール (Installation)

1. **リポジトリのクローン**

    ```bash
    git clone <リポジトリのURL>
    cd ReCiel
    ```

2. **仮想環境の構築**
    `uv` が `pyproject.toml` を元に仮想環境を構築し、必要なパッケージを仮想環境にインストールします。

    ```bash
    uv sync
    ```

3. **環境変数の設定**
    `.env` ファイルを作成し、Discord BotのトークンとGoogle APIのキーを記述します。

    ```env
    DISCORD_TOKEN = あなたのDiscord Bot Token
    GOOGLE_API_KEY = あなたのGoogle API Key
    ```

## ▶️ 使い方 (Usage)

以下のコマンドでボットを起動します。`uv` が仮想環境を自動的に検出して実行します。

```bash
uv run python main.py
```

コンソールに `Ciel Start-up` と表示されれば、正常に起動しています。

## 📂 プロジェクト構造 (Project Structure)

```text
.
├── cogs/              # コグ（機能拡張）ディレクトリ
│   ├── __init__.py    # 初期化処理
│   ├── develop/          # 開発用コマンド（サブディレクトリ）
│   │   ├── __init__.py   # 初期化処理
│   │   ├── core.py       # 主要処理
│   │   └── embed.py      # 専用Embed
│   ├── music/            # 音楽用コマンド（サブディレクトリ）
│   │   ├── __init__.py   # 初期化処理
│   │   ├── agent.py      # 音楽提案エージェント
│   │   ├── core.py       # 主要処理
│   │   ├── embed.py      # 専用Embed
│   │   ├── errors.py     # 専用エラークラス
│   │   ├── model.py      # データモデル
│   │   ├── view.py       # 専用View
│   │   └── youtube.py    # YouTube関連処理
│   ├── error.py       # エラーハンドリング
│   └── general.py     # 一般コマンド
├── utils/             # ユーティリティ（補助機能）ディレクトリ
│   ├── __init__.py    # 初期化処理
│   ├── agent.py       # Google ADK関連
│   ├── commands.py    # コマンド関連機能
│   ├── decorators.py  # コマンド用デコレーター
│   ├── embed.py       # Embed関連
│   ├── errors.py      # エラーハンドリング補助
│   ├── logging.py     # ロギング機能
│   ├── types.py       # 型アノテーション
│   └── view.py        # View関連
├── .env            # 環境変数ファイル (トークンなど)
├── .gitignore      # Gitで無視するファイル
├── main.py         # メインファイル
├── ciel.py         # Bot本体クラス
├── pyproject.toml  # プロジェクト設定と依存関係
├── uv.lock         # 依存関係のロックファイル
└── README.md       # このファイル
```

## 👑 開発者用機能 (Advanced Features)

### 開発者用コマンド一覧

`cogs/develop.py` には、Bot開発・運用を支援する以下のコマンドが実装されています。

- **/extensions** : 現在ロードされている拡張の一覧を表示します。
- **/reload [extension] [sync]** : 指定した拡張、または全拡張をリロードし、必要に応じてコマンド同期も行います。
- **/sync [force]** : すべてのコマンドをDiscordに同期します。
- **/register** : `Command`と`AppCommand`の関係を再登録します。
- **/map** : 現在の`Command`と`AppCommand`の対応状況を表示します。

これらのコマンドは、Botのオーナーのみが利用できるよう `developer_only` デコレータで保護されています。

### 環境ファイル `.env`

Botのトークンに加えて `.env` ファイルには開発者用の情報を指定できます。

#### 必須情報

- `DISCORD_TOKEN` : 本番用Botトークン
- `GOOGLE_API_KEY` : YouTube Data API v3用APIキー

#### 開発者用情報

- `DEVELOP_DISCORD_TOKEN` : 開発用Botトークン 開発モード時に使用
- `DEVELOP_GUILD_ID` : 開発用ギルドID 開発モード時に使用
- `LOG_FOLDER` : ログファイルの保存先ディレクトリ

### 起動時のオプション

`main.py` 実行時に以下のオプションを指定できます。

- `--develop` : 開発モードで起動。開発用Botトークン・ギルドを利用し、コマンド同期が即座に反映されます。
- `--sync` : 起動時にすべてのコマンドをDiscordに同期します。
