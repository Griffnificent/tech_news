import yaml
import re

class FilterEngine:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.global_filters = self.config.get("global", {})
        self.category_filters = self.config.get("categories", {})
        self.per_feed_filters = self.config.get("per_feed", {})

    def evaluate(self, entry):
        """
        Returns:
            {
                "passed": bool,
                "priority": int (0-10),
                "matched_keywords": list
            }
        """
        text = f"{entry['title']} {entry['summary']}".lower()
        category = entry.get("category", "")
        feed_name = entry.get("feed_name", "")

        matched_keywords = []
        priority = 5  # デフォルト優先度

        # 除外キーワードチェック
        exclude_keywords = self.global_filters.get("exclude_keywords", [])
        for kw in exclude_keywords:
            if kw.lower() in text:
                return {"passed": False, "priority": 0, "matched_keywords": []}

        # グローバルincludeキーワード
        global_include = self.global_filters.get("include_keywords", [])

        # カテゴリ別フィルタ
        cat_filters = self.category_filters.get(category, {})
        cat_include = cat_filters.get("include_keywords", [])
        cat_priority = cat_filters.get("priority_keywords", [])

        # フィード別フィルタ
        feed_filters = self.per_feed_filters.get(feed_name, {})
        feed_include = feed_filters.get("include_keywords", [])

        # 全キーワードをマージ
        all_include = global_include + cat_include + feed_include

        # マッチング
        for kw in all_include:
            if kw.lower() in text:
                matched_keywords.append(kw)

        # 優先キーワードチェック
        for kw in cat_priority:
            if kw.lower() in text:
                priority = 10
                matched_keywords.append(f"[HIGH] {kw}")

        # CVE番号は自動的にパス
        if re.search(r'CVE-\d{4}-\d+', entry['title'], re.IGNORECASE):
            matched_keywords.append("CVE")
            priority = max(priority, 7)

        # フィルタなしカテゴリは全パス（security系など）
        if category in ["security", "cve"] and not matched_keywords:
            return {"passed": True, "priority": priority, "matched_keywords": ["category:security"]}

        passed = len(matched_keywords) > 0

        return {
            "passed": passed,
            "priority": priority,
            "matched_keywords": matched_keywords
        }
