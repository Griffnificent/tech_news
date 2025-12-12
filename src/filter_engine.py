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
        security_keywords = ["vulnerability", "security", "cve-", "脆弱性", "セキュリティ",
                            "critical", "high", "severe", "exploit", "rce", "zero-day"]
        has_security_keyword = any(sk in text for sk in security_keywords)

        for kw in all_include:
            if kw.lower() in text:
                # packageカテゴリの場合、言語名だけでなくセキュリティキーワードも必要
                if category == "package":
                    # セキュリティキーワードがない場合はスキップ
                    if not has_security_keyword and kw.lower() in ["npm", "node", "nodejs", "javascript",
                        "typescript", "python", "pip", "pypi", "flutter", "dart", "pub",
                        "kotlin", "java", "maven", "gradle", "spring", "ruby", "gem",
                        "rubygems", "rails", "swift", "cocoapods", "bash", "shell",
                        "zsh", "docker", "container"]:
                        continue
                matched_keywords.append(kw)

        # 優先キーワードチェック（High/Critical判定）
        feed_priority = feed_filters.get("priority_keywords", [])
        all_priority = cat_priority + feed_priority

        for kw in all_priority:
            if kw.lower() in text:
                priority = 10
                matched_keywords.append(f"[HIGH] {kw}")

        # CVE番号は自動的にパス
        if re.search(r'CVE-\d{4}-\d+', entry['title'], re.IGNORECASE):
            matched_keywords.append("CVE")
            priority = max(priority, 7)

        # High/Criticalキーワードの追加チェック
        high_severity_keywords = ["critical", "high", "severe", "9.", "10.0", "zero-day", "ゼロデイ"]
        for kw in high_severity_keywords:
            if kw in text:
                priority = max(priority, 8)
                if kw not in [k.lower() for k in matched_keywords]:
                    matched_keywords.append(f"severity:{kw}")

        # security/cveカテゴリもキーワードマッチが必要
        if category in ["security", "cve"] and not matched_keywords:
            # キーワードなしでもCVEやsecurityという単語があれば通過
            if "cve-" in text or "security" in text or "脆弱性" in text:
                matched_keywords.append("category:security")
            else:
                return {"passed": False, "priority": 0, "matched_keywords": []}

        passed = len(matched_keywords) > 0

        return {
            "passed": passed,
            "priority": priority,
            "matched_keywords": matched_keywords
        }
