"""記事のジャンル分類を行うスクリプト。"""

import json
import os
from pathlib import Path

from openrouter import OpenRouter


def load_articles(path: Path) -> list[dict[str, str | None]]:
  """JSONファイルから記事情報を読み込む。

  Args:
      path: articles.json のパス。

  Returns:
      記事の辞書のリスト。
  """
  with path.open(encoding="utf-8") as f:
    return json.load(f)


def build_classification_prompt(articles: list[dict[str, str | None]]) -> str:
  """ジャンル分類用のプロンプトを生成する。

  Args:
      articles: 分類する記事の辞書のリスト（id と title を含む）。

  Returns:
      OpenRouter API に送るプロンプト文字列。
  """
  article_list = [{"id": a["id"], "title": a["title"]} for a in articles]
  return f"""
以下の日本のニュース記事のタイトル一覧を、適切なジャンル（政治、社会、事件・裁判、災害・気象、エンタメ、その他）に分類してください。

出力は、以下のJSON配列形式（キー: "id", "genre"）のみで返却してください。
余計な挨拝や説明は一切不要です。

[
  {{"id": "記事ID1", "genre": "分類されたジャンル"}},
  {{"id": "記事ID2", "genre": "分類されたジャンル"}}
]

【分類する記事一覧】
{json.dumps(article_list, ensure_ascii=False, indent=2)}
"""


def classify_articles(client: OpenRouter, prompt: str) -> str:
  """OpenRouter API を使ってタイトルをジャンル分類する。

  Args:
      client: OpenRouter クライアント。
      prompt: 分類用のプロンプト。

  Returns:
      API からのレスポンス文字列。
  """
  response = client.chat.send(
    model="google/gemma-4-31b-it:free",
    messages=[{"role": "user", "content": prompt}],
  )
  return str(response.choices[0].message.content)


def save_articles(data: list[dict[str, str | None]], output_path: Path) -> None:
  """記事情報をJSONファイルに保存する。

  Args:
      data: 記事の辞書のリスト。
      output_path: 出力ファイルのパス。
  """
  output_path.parent.mkdir(parents=True, exist_ok=True)
  text = json.dumps(data, ensure_ascii=False, indent=2)
  output_path.write_text(text, encoding="utf-8")


def main() -> None:
  """Main entry point."""
  project_root = Path(__file__).parent.parent
  articles_path = project_root / "output" / "articles.json"

  articles = load_articles(articles_path)

  # Filter to only unclassified articles (genre is None)
  unclassified = [a for a in articles if a.get("genre") is None]

  if not unclassified:
    print("No articles to classify. All articles have genre assigned.")
    return

  prompt = build_classification_prompt(unclassified)

  with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    result = classify_articles(client, prompt)

  # Parse LLM response and update genre in articles
  try:
    classifications = json.loads(result)
    genre_map = {c["id"]: c["genre"] for c in classifications}
    for article in articles:
      article_id = article.get("id")
      if article_id and article_id in genre_map:
        article["genre"] = genre_map[article_id]
  except json.JSONDecodeError, KeyError:
    print(f"Warning: Failed to parse classification result: {result}")
    return

  # Save updated articles back to articles.json
  save_articles(articles, articles_path)
  print(f"Saved {len(unclassified)} classified articles to {articles_path}")


if __name__ == "__main__":
  main()
