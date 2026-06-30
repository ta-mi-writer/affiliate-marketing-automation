"""Yahoo News domestic ranking scraper using scrapling."""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scrapling import Fetcher
from scrapling.parser import Selector

# Module-level constants
_JST = timezone(timedelta(hours=9))
_EXPECTED_SPLIT_COUNT = 2
_JANUARY = 1
_DECEMBER = 12


def fetch_page(url: str) -> Selector:
  """Fetch the page and return a parsed Selector.

  Args:
      url: The URL to fetch.

  Returns:
      A Selector object containing the parsed HTML.
  """
  response = Fetcher.get(url)
  return Selector(response.html_content)


def extract_article_id(url: str) -> str:
  """Extract the article ID (hash) from a Yahoo News URL.

  Args:
      url: The URL string to extract the ID from.

  Returns:
      The hash portion after /articles/ in the URL, or an empty string if
      the URL does not contain /articles/.
  """
  if "/articles/" not in url:
    return ""

  # Find the /articles/ part and extract the hash after it
  # parts[0] is everything before /articles/, parts[1] is everything after
  after_articles = url.split("/articles/")[1]

  # The hash is the first path segment after /articles/
  # It may be followed by query params or additional path segments
  return after_articles.split("?")[0].split("/")[0]


def normalize_datetime(datetime_str: str) -> str | None:
  """Normalize a datetime string to ISO 8601 format.

  Converts strings like '6/28(日) 16:20' to '2026-06-28T16:20:00'.
  The day-of-week part in parentheses is ignored.

  Args:
      datetime_str: A datetime string in format M/D(day-of-week) H:M.

  Returns:
      ISO 8601 formatted string, or None if parsing fails or string is empty.
  """
  if not datetime_str or not datetime_str.strip():
    return None

  try:
    # Remove the day-of-week part in parentheses, e.g., "6/28(日) 16:20" -> "6/28 16:20"
    cleaned = re.sub(r"\([^)]+\)\s*", " ", datetime_str).strip()

    # Parse the date and time parts
    parts = cleaned.split()
    if len(parts) != _EXPECTED_SPLIT_COUNT:
      return None

    date_part, time_part = parts

    # Parse month and day
    date_components = date_part.split("/")
    if len(date_components) != _EXPECTED_SPLIT_COUNT:
      return None

    month = int(date_components[0])
    day = int(date_components[1])

    # Parse hour and minute
    time_components = time_part.split(":")
    if len(time_components) != _EXPECTED_SPLIT_COUNT:
      return None

    hour = int(time_components[0])
    minute = int(time_components[1])

    # Get current year and month with JST (Japan Standard Time, UTC+9)
    now = datetime.now(_JST)
    current_year = now.year
    current_month = now.month

    # Handle year-crossing: if current month is January and parsed month is December
    year = current_year
    if current_month == _JANUARY and month == _DECEMBER:
      year = current_year - 1

    # Create the datetime object and format as ISO 8601 with timezone
    result = datetime(year, month, day, hour, minute, tzinfo=_JST)
    return result.isoformat()
  except ValueError, IndexError:
    return None


def filter_recent_articles(
  articles: list[dict[str, str | None]], days: int = 2
) -> list[dict[str, str | None]]:
  """Filter articles to only include those within the last 'days' days.

  Args:
      articles: List of article dictionaries with 'datetime' field.
      days: Number of days to look back (default: 2).

  Returns:
      Filtered list of articles with datetime within the specified range.
      Articles with datetime=None are kept (safe side).
  """
  cutoff = datetime.now(_JST) - timedelta(days=days)
  filtered = []
  for article in articles:
    dt = article.get("datetime")
    if dt is None:
      # Keep articles with None datetime (safe side)
      filtered.append(article)
    else:
      try:
        article_dt = datetime.fromisoformat(dt)
        if article_dt >= cutoff:
          filtered.append(article)
      except ValueError:
        # Keep articles with invalid datetime (safe side)
        filtered.append(article)
  return filtered


def parse_article(article: Selector) -> dict[str, str | None]:
  """Extract title, URL, id, genre, and normalized datetime from an article element.

  Args:
      article: A Selector element representing an article link.

  Returns:
      A dictionary with title, url, id, genre, and datetime keys.
  """
  url = article.attrib.get("href", "")
  article_id = extract_article_id(url)

  # Find <time> element first (semantic, stable anchor)
  time_elems = article.css("time")
  time_text = ""

  if time_elems:
    time_elem = time_elems[0]
    # Try direct text first
    time_text = time_elem.text or ""

    # If no direct text, look for nested spans with time parts
    if not time_text.strip():
      # Find all span elements within time
      spans = time_elem.css("span")
      if spans:
        # Collect text from all spans
        span_texts = [s.text for s in spans if s.text]
        if span_texts:
          # Join spans with space - format is typically "M/D(曜) H:M"
          time_text = " ".join(span_texts)

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
    "id": article_id,
    "genre": None,
    "datetime": normalize_datetime(time_text),
  }


def scrape_yahoo_news(url: str) -> list[dict[str, str | None]]:
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

  # Filter out articles older than 2 days
  return filter_recent_articles(results)


def save_articles(new_articles: list[dict[str, str | None]], output_path: Path) -> None:
  """Merge new articles with existing articles.json and save.

  Reads existing articles.json if it exists, merges articles by ID, and
  prefers non-null values from new data when updating existing articles.
  Also purges articles older than 2 days from the merged list.

  Args:
      new_articles: The list of new article dictionaries to merge.
      output_path: The path to the output JSON file.
  """
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # Read existing articles if file exists
  existing_articles: list[dict[str, str | None]] = []
  if output_path.exists():
    with output_path.open("r", encoding="utf-8") as f:
      existing_articles = json.load(f)

  # Create a map of existing articles by ID for efficient lookup and merging
  existing_by_id: dict[str, dict[str, str | None]] = {
    a.get("id") or "": a for a in existing_articles
  }

  # Merge new articles into existing map
  for new_article in new_articles:
    article_id = new_article.get("id") or ""
    if article_id in existing_by_id:
      # UPDATE existing article - prefer non-null values from new data
      existing = existing_by_id[article_id]
      for key, value in new_article.items():
        if value is not None and existing.get(key) is None:
          existing[key] = value
    else:
      # Add new article
      existing_by_id[article_id] = new_article.copy()

  # Convert map back to list
  merged = list(existing_by_id.values())
  total_before_purge = len(merged)

  # Purge articles older than 2 days
  merged = filter_recent_articles(merged)
  purged_count = total_before_purge - len(merged)

  # Save
  with output_path.open("w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

  new_count = sum(1 for a in new_articles if (a.get("id") or "") not in existing_by_id)
  update_count = sum(1 for a in new_articles if (a.get("id") or "") in existing_by_id)
  print(
    f"Added {new_count} new articles, updated {update_count} existing articles. "
    f"Purged {purged_count} old articles. Total: {len(merged)} articles."
  )


def main() -> None:
  """Main entry point."""
  url = "https://news.yahoo.co.jp/ranking/comment/domestic"
  output_path = Path("/root/pi-workspace/scraping/output/articles.json")

  data = scrape_yahoo_news(url)
  save_articles(data, output_path)


if __name__ == "__main__":
  main()
