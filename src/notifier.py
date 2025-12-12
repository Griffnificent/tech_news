import os
import requests
from datetime import datetime
from summarizer import OllamaSummarizer, is_english_title

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        self.summarizer = OllamaSummarizer()
        self.use_summarizer = self.summarizer.is_available()

    def send_batch(self, entries, batch_size=5):
        """High Priority（優先度8以上）のみを個別送信"""
        if not self.webhook_url:
            print("DISCORD_WEBHOOK_URL not set")
            return

        # High Level（優先度8以上）のみ通知
        high_priority = [e for e in entries if e["priority"] >= 8]

        if high_priority:
            print(f"Sending {len(high_priority)} high priority notifications")

        # 優先度8未満はスキップ
        skipped = len([e for e in entries if e["priority"] < 8])
        if skipped > 0:
            print(f"Skipped {skipped} lower priority entries (priority < 8)")

        # 高優先度のみ個別送信
        for entry in high_priority:
            self._send_single(entry, is_priority=True)

    def _send_single(self, entry, is_priority=False):
        color = 0xFF0000 if is_priority else 0x00FF00  # 赤 or 緑

        # タイトルを決定（英語の場合は日本語タイトルを生成）
        display_title = entry['title']

        if is_priority and self.use_summarizer and is_english_title(entry['title']):
            print(f"Generating Japanese title for: {entry['title'][:50]}...")
            japanese_title = self.summarizer.generate_japanese_title(entry)
            if japanese_title and japanese_title != entry['title']:
                display_title = japanese_title

        # High Priorityの場合、日本語要約を生成
        description = entry["summary"][:300] if entry["summary"] else ""

        if is_priority and self.use_summarizer:
            print(f"Generating Japanese summary for: {display_title[:50]}...")
            ai_summary = self.summarizer.summarize(entry)

            if ai_summary:
                description = f"**📝 AI要約（日本語）:**\n{ai_summary}\n\n---\n{description}"

        embed = {
            "title": f"{'🚨 ' if is_priority else ''}{display_title[:200]}",
            "url": entry["link"],
            "description": description[:2000],  # Discord limit
            "color": color,
            "fields": [
                {"name": "Source", "value": entry["feed_name"], "inline": True},
                {"name": "Category", "value": entry["category"], "inline": True},
                {"name": "Matched", "value": ", ".join(entry["matched_keywords"][:5]), "inline": False}
            ],
            "timestamp": entry["published"].isoformat() if entry["published"] else None
        }

        self._post({"embeds": [embed]})

    def _send_batch_embed(self, entries):
        if not entries:
            return

        description_lines = []
        for e in entries:
            line = f"• [{e['title'][:60]}...]({e['link']}) ({e['feed_name']})"
            description_lines.append(line)

        embed = {
            "title": f"📰 New Security Updates ({len(entries)} items)",
            "description": "\n".join(description_lines),
            "color": 0x0099FF,
            "timestamp": datetime.now().isoformat()
        }

        self._post({"embeds": [embed]})

    def _post(self, payload):
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Discord notification failed: {e}")
