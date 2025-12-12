import feedparser
import yaml
import hashlib
from datetime import datetime
from dateutil import parser as date_parser

class FeedParser:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get_feeds(self):
        return self.config.get("feeds", [])

    def fetch(self, feed_config, limit=20):
        entries = []
        try:
            parsed = feedparser.parse(feed_config["url"])

            for entry in parsed.entries[:limit]:
                # 一意なIDを生成
                entry_id = entry.get("id") or entry.get("link") or entry.get("title")
                unique_id = hashlib.md5(entry_id.encode()).hexdigest()

                # 日付のパース
                published = None
                for date_field in ["published", "updated", "created"]:
                    if hasattr(entry, date_field):
                        try:
                            published = date_parser.parse(getattr(entry, date_field))
                            break
                        except:
                            pass

                entries.append({
                    "id": unique_id,
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:500],  # 長すぎる場合カット
                    "published": published or datetime.now(),
                })

        except Exception as e:
            print(f"Error fetching {feed_config['name']}: {e}")

        return entries
