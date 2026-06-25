"""記事のジャンル分類を行うスクリプト。"""

import json
import os
from pathlib import Path

from openrouter import OpenRouter


def load_articles(path: Path) -> list[dict[str, str]]:
  """JSONファイルから記事情報を読み込む。

  Args:
      path: articles.json のパス。

  Returns:
      記事の辞書のリスト。
  """
  with path.open(encoding="utf-8") as f:
    return json.load(f)


def build_classification_prompt(titles: list[str]) -> str:
  """ジャンル分類用のプロンプトを生成する。

  Args:
      titles: 分類するニュースタイトルのリスト。

  Returns:
      OpenRouter API に送るプロンプト文字列。
  """
  return f"""
以下の日本のニュース記事のタイトル一覧を、適切なジャンル（政治、社会、事件・裁判、災害・気象、エンタメ、その他）に分類してください。

出力は、以下のJSON配列形式（キー: "title", "genre"）のみで返却してください。
余計な挨拶や説明は一切不要です。

[
  {{"title": "ニュースのタイトル1", "genre": "分類されたジャンル"}},
  {{"title": "ニュースのタイトル2", "genre": "分類されたジャンル"}}
]

【分類するタイトル一覧】
{json.dumps(titles, ensure_ascii=False, indent=2)}
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


def save_classified_result(data: str, output_path: Path) -> None:
  """分類結果をJSONファイルに保存する。

  Args:
      data: 分類結果のJSON文字列。
      output_path: 出力ファイルのパス。
  """
  output_path.parent.mkdir(parents=True, exist_ok=True)
  output_path.write_text(data, encoding="utf-8")


def main() -> None:
  """Main entry point."""
  project_root = Path(__file__).parent.parent
  articles_path = project_root / "output" / "articles.json"
  output_path = project_root / "output" / "classified_articles.json"

  articles = load_articles(articles_path)
  titles = [item["title"] for item in articles if item.get("title")]
  prompt = build_classification_prompt(titles)

  with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    result = classify_articles(client, prompt)

  save_classified_result(result, output_path)
  print(f"Saved classified result to {output_path}")


if __name__ == "__main__":
  main()
