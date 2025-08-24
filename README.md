# ReCiel

> Generic Discord Bot built with discord.py.

discord.py で構築された、多目的で拡張可能な Discord ボットです。

## ✨ 機能 (Features)

Comming Soon..

## 🚀 導入方法 (Getting Started)

### 必要なもの (Requirements)

- Python 3.13 以上
- [uv](https://github.com/astral-sh/uv) (高速なPythonパッケージインストーラー兼リゾルバー)
- Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications)から取得可能)

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
    `.env` ファイルを作成し、Discord Botのトークンを記述します。

    ```env
    DISCORD_TOKEN = あなたのDiscord Bot Token
    ```

## 使い方 (Usage)

以下のコマンドでボットを起動します。`uv` が仮想環境を自動的に検出して実行します。

```bash
uv run python main.py
```

コンソールに `Ciel Start-up` と表示されれば、正常に起動しています。

## 📂 プロジェクト構造 (Project Structure)

```text
.
├── .env               # 環境変数ファイル (トークンなど)
├── .gitignore         # Gitで無視するファイル
├── main.py            # メインファイル
├── pyproject.toml     # プロジェクト設定と依存関係
├── uv.lock            # 依存関係のロックファイル
└── README.md          # このファイル
```
