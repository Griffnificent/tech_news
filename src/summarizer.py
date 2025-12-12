import requests
from bs4 import BeautifulSoup
import re

def is_english_title(title):
    """タイトルが英語かどうかを判定（日本語文字が含まれていない）"""
    # ひらがな、カタカナ、漢字のいずれかが含まれていれば日本語
    japanese_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]'
    return not bool(re.search(japanese_pattern, title))

class OllamaSummarizer:
    def __init__(self, model="gemma2:9b", ollama_url="http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url
        self.timeout = 30

    def generate_japanese_title(self, entry):
        """
        英語タイトルから日本語タイトルを生成

        Args:
            entry: dict with "title" and "summary" (optional)

        Returns:
            str: 日本語タイトル（失敗時は元のタイトル）
        """
        try:
            # 既に日本語タイトルの場合はそのまま返す
            if not is_english_title(entry["title"]):
                return entry["title"]

            # 記事本文を取得
            article_text = self._fetch_article_content(entry["link"])

            # 本文が取得できない場合、summaryを使用
            if not article_text and entry.get("summary"):
                article_text = entry["summary"]

            if not article_text:
                return entry["title"]

            # 長すぎる場合は先頭1000文字に制限（タイトル生成なので短めでOK）
            if len(article_text) > 1000:
                article_text = article_text[:1000] + "..."

            # Ollamaで日本語タイトルを生成
            japanese_title = self._generate_japanese_title_from_content(entry["title"], article_text)
            return japanese_title if japanese_title else entry["title"]

        except Exception as e:
            print(f"Japanese title generation failed for {entry['link']}: {e}")
            return entry["title"]

    def summarize(self, entry):
        """
        記事URLから本文を取得し、日本語で要約を生成

        Args:
            entry: dict with "link" and "title"

        Returns:
            str: 日本語要約（失敗時は空文字列）
        """
        try:
            # 記事本文を取得
            article_text = self._fetch_article_content(entry["link"])

            if not article_text:
                return ""

            # 長すぎる場合は先頭2000文字に制限
            if len(article_text) > 2000:
                article_text = article_text[:2000] + "..."

            # Ollamaで日本語要約を生成
            summary = self._generate_summary(entry["title"], article_text)
            return summary

        except Exception as e:
            print(f"Summarization failed for {entry['link']}: {e}")
            return ""

    def _fetch_article_content(self, url):
        """記事URLから本文テキストを取得"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.content, "html.parser")

            # 不要なタグを削除
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            # 本文を取得（一般的なタグから抽出）
            article = soup.find("article") or soup.find("main") or soup.find("body")
            if not article:
                return ""

            # テキストを抽出
            text = article.get_text(separator="\n", strip=True)

            # 空行を削除し、整形
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines)

        except Exception as e:
            print(f"Failed to fetch article content: {e}")
            return ""

    def _generate_japanese_title_from_content(self, original_title, content):
        """Ollama APIを使って日本語タイトルを生成"""
        try:
            prompt = f"""以下のセキュリティ記事の英語タイトルを、本文の内容を読んで適切な日本語タイトルに翻訳してください。
簡潔で分かりやすいタイトルにしてください（20文字以内推奨）。

英語タイトル: {original_title}

本文:
{content[:500]}

日本語タイトル:"""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 50  # タイトルなので短め
                }
            }

            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()

            result = resp.json()
            title = result.get("response", "").strip()

            # 余計な改行や引用符を削除
            title = title.replace("\n", " ").strip('"').strip("'")

            return title

        except Exception as e:
            print(f"Ollama API failed for title generation: {e}")
            return ""

    def _generate_summary(self, title, content):
        """Ollama APIを使って日本語要約を生成"""
        try:
            prompt = f"""以下のセキュリティ記事を日本語で簡潔に要約してください（2-3文）。

タイトル: {title}

本文:
{content}

要約（日本語）:"""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 200  # 最大トークン数
                }
            }

            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()

            result = resp.json()
            summary = result.get("response", "").strip()

            return summary

        except Exception as e:
            print(f"Ollama API failed: {e}")
            return ""

    def is_available(self):
        """Ollamaが利用可能かチェック"""
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except:
            return False
