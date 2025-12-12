#!/usr/bin/env python3
import logging
from pathlib import Path
from datetime import datetime

from feed_parser import FeedParser
from filter_engine import FilterEngine
from notifier import DiscordNotifier
from db import SeenDB

# ログ設定
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "feed.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    base_dir = Path(__file__).parent.parent

    # 初期化
    parser = FeedParser(base_dir / "config" / "feeds.yaml")
    filter_engine = FilterEngine(base_dir / "config" / "filters.yaml")
    db = SeenDB(base_dir / "data" / "seen.db")
    notifier = DiscordNotifier()

    logger.info("Starting feed check...")

    new_entries = []

    for feed in parser.get_feeds():
        if not feed.get("enabled", True):
            continue

        logger.info(f"Fetching: {feed['name']}")
        entries = parser.fetch(feed)

        for entry in entries:
            # 既読チェック
            if db.is_seen(entry["id"]):
                continue

            # フィルタリング
            entry["category"] = feed["category"]
            entry["feed_name"] = feed["name"]

            result = filter_engine.evaluate(entry)

            if result["passed"]:
                entry["priority"] = result["priority"]
                entry["matched_keywords"] = result["matched_keywords"]
                new_entries.append(entry)
                db.mark_seen(entry["id"])

    # 通知
    if new_entries:
        logger.info(f"Found {len(new_entries)} new entries")
        # 優先度でソート
        new_entries.sort(key=lambda x: x["priority"], reverse=True)
        notifier.send_batch(new_entries)
    else:
        logger.info("No new entries")

    # 古いレコードの掃除（30日以上前）
    db.cleanup(days=30)

    logger.info("Done")

if __name__ == "__main__":
    main()
