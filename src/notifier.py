import os
import requests
from datetime import datetime

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    def send_batch(self, entries, batch_size=5):
        """複数エントリをまとめて送信"""
        if not self.webhook_url:
            print("DISCORD_WEBHOOK_URL not set")
            return

        # 優先度でグループ分け
        high_priority = [e for e in entries if e["priority"] >= 8]
        normal = [e for e in entries if e["priority"] < 8]

        # 高優先度は個別送信
        for entry in high_priority:
            self._send_single(entry, is_priority=True)

        # 通常はまとめて送信
        for i in range(0, len(normal), batch_size):
            batch = normal[i:i+batch_size]
            self._send_batch_embed(batch)

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
