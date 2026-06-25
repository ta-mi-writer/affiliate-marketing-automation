"""Yahoo News domestic ranking scraper using scrapling."""

import json
from pathlib import Path

from scrapling import Fetcher
from scrapling.parser import Selector


def fetch_page(url: str) -> Selector:
  """Fetch the page and return a parsed Selector.

  Args:
      url: The URL to fetch.

  Returns:
      A Selector object containing the parsed HTML.
  """
  response = Fetcher.get(url)
  return Selector(response.html_content)


def parse_article(article: Selector) -> dict[str, str]:
  """Extract title, URL, and datetime from an article element.

  Args:
      article: A Selector element representing an article link.

  Returns:
      A dictionary with title, url, and datetime keys.
  """
  url = article.attrib.get("href", "")

  # Title is in div with class containing "sc-3ls169-0"
  title_elem = article.css(".sc-3ls169-0")
  title = title_elem[0].text if title_elem else ""

  # Time is in <time> element
  time_elem = article.css("time")
  time_text = time_elem[0].text if time_elem else ""

  return {
    "title": title,
    "url": url,
    "datetime": time_text,
  }


def scrape_yahoo_news(url: str) -> list[dict[str, str]]:
  """Scrape all articles from the Yahoo News ranking page.

  Args:
      url: The URL of the Yahoo News ranking page.

  Returns:
      A list of dictionaries containing article data.
  """
  doc = fetch_page(url)

  # Find all article links
  articles = doc.css('a[href*="articles"]')

  results = []
  for article in articles:
    data = parse_article(article)
    results.append(data)

  return results


def save_to_json(data: list[dict[str, str]], output_path: Path) -> None:
  """Save scraped data to a JSON file.

  Args:
      data: The list of article dictionaries to save.
      output_path: The path to the output JSON file.
  """
  output_path.parent.mkdir(parents=True, exist_ok=True)
  with output_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
  """Main entry point."""
  url = "https://news.yahoo.co.jp/ranking/comment/domestic"
  output_path = Path("/root/pi-workspace/scraping/output/articles.json")

  data = scrape_yahoo_news(url)
  save_to_json(data, output_path)
  print(f"Saved {len(data)} articles to {output_path}")
