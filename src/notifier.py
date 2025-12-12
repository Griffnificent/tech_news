import os
import requests
from datetime import datetime

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

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

        embed = {
            "title": f"{'🚨 ' if is_priority else ''}{entry['title'][:200]}",
            "url": entry["link"],
            "description": entry["summary"][:300] if entry["summary"] else "",
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
