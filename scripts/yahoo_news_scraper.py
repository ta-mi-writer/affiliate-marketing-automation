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

  # Find <time> element first (semantic, stable anchor)
  time_elems = article.css("time")
  time_text = time_elems[0].text if time_elems else ""

  # Title extraction using structural navigation:
  # Structure: <div><p>TITLE</p><div><time>...</time></div></div>
  # The <p> with title is a previous sibling of the <div> containing <time>
  # But if no previous sibling, look for <p> inside the same parent
  title = ""
  if time_elems:
    time_parent = time_elems[0].parent
    if time_parent:
      container = time_parent.parent
      if container:
        title_div = container.previous
        if title_div:
          title = title_div.text or ""
        else:
          # Title is a <p> element inside the same container
          p_elems = container.css("p")
          if p_elems:
            title = p_elems[0].text or ""

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

  # Find all article links using data-cl-params attribute
  # Filter to only include /articles/ URLs (exclude pickup articles)
  articles = doc.css('a[data-cl-params*="_cl_link:title"]')
  articles = [a for a in articles if "/articles/" in a.attrib.get("href", "")]

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


if __name__ == "__main__":
  main()
