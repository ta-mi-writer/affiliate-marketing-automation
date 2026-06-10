# あなた（AI Agent）に守ってほしいこと

## プログラミングコード作成・修正時
- この環境では`uv`が使用可能
  - `pyhon`コマンドや`pip`コマンドは使用せず、`uv`コマンドを使用する
    - Pythonファイルを実行するときのコマンドは、`uv run --env-file .env ファイル名 その他の引数`を使用する
    - リントチェックの時のコマンドは、`uv run ruff check ファイル名`を使用する
    - 型をチェックする時のコマンドは、`uv run basedpyright ファイル名`
- パッケージのインストールを行わない
  - インストールされていないモノを使用する場合は、
    - インストールを私に依頼する
    - セッションを閉じたら自動で消える様な方法で使用する
- まずは詳細なコーディングのプランを立てる
  - 基本的にはPythonの標準モジュールを使用する
  - 標準モジュール以外を用いるときは、プランを立てる段階で書き出す
  - プランを立て終わったら、そのまま実装を開始せずに、必ずプランの相談を私（ユーザー）と行う
- プランに基づいて、プログラムをコーディングする
  - 環境変数を用いる
    - `.env`ファイルを使用する
    - envの使用例：
      ```python
      import os
      
      def get_api_key(api_key: str | None = None) -> str | None:
        if api_key is None:
          api_key = os.getenv("API_KEY")
        return api_key
      
      api_key = get_api_key(api_key)
      ```
  - コードはRuffのlintに準拠する（`pyproject.toml`を参考にする）
- コードが完成したら
  - Ruffとbasedpyrightのエラーを確認する
