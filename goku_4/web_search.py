import re
import urllib.request
import urllib.parse
import json
import html
import logging

logger = logging.getLogger('GOKU.WebSearch')

class WebSearch:
    def __init__(self):
        self._ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

    def _duckduckgo_lite(self, query):
        try:
            url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={
                'User-Agent': self._ua,
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
            results = []
            title_pattern = re.findall(r'class="result-link"[^>]*href="[^"]*"[^>]*>(.*?)</a>', content, re.DOTALL)
            snippet_pattern = re.findall(r'class="result-snippet"[^>]*>(.*?)</td>', content, re.DOTALL)
            for i, t in enumerate(title_pattern[:3]):
                clean_t = html.unescape(re.sub(r'<[^>]+>', '', t)).strip()
                clean_s = ""
                if i < len(snippet_pattern):
                    clean_s = html.unescape(re.sub(r'<[^>]+>', '', snippet_pattern[i])).strip()
                if clean_t and len(clean_t) > 5:
                    results.append(f"{clean_t}. {clean_s}" if clean_s else clean_t)
            if results:
                return " ".join(results)[:500]
            return None
        except Exception as e:
            logger.warning(f"DDG Lite error: {e}")
            return None

    def _duckduckgo_html(self, query):
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={
                'User-Agent': self._ua,
                'Accept': 'text/html,application/xhtml+xml',
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
            titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', content, re.DOTALL)
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</td>', content, re.DOTALL)
            if titles:
                parts = []
                for i, t in enumerate(titles[:3]):
                    clean = html.unescape(re.sub(r'<[^>]+>', '', t)).strip()
                    if clean and len(clean) > 5:
                        parts.append(clean)
                    if i < len(snippets):
                        s = html.unescape(re.sub(r'<[^>]+>', '', snippets[i])).strip()
                        if s and len(s) > 5:
                            parts.append(s)
                result = " ".join(parts)
                if len(result) > 10:
                    return result[:500]
            return None
        except Exception as e:
            logger.warning(f"DDG HTML error: {e}")
            return None

    def _wikipedia(self, query):
        try:
            clean_q = re.sub(r'^(what\s+is\s+|who\s+is\s+|what\s+are\s+|who\s+are\s+|tell\s+me\s+about\s+|define\s+|explain\s+)', '', query, flags=re.I).strip()
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_q)}"
            req = urllib.request.Request(url, headers={'User-Agent': self._ua})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            if data.get('type') in ('disambiguation', 'error'):
                return None
            extract = data.get('extract', '')
            if extract and len(extract) > 20:
                return f"{data.get('title', clean_q)}: {extract}"[:500]
            return None
        except urllib.error.HTTPError:
            return None
        except Exception as e:
            logger.warning(f"Wiki error: {e}")
            return None

    def _brave_summarize(self, query):
        try:
            url = f"https://search.brave.com/api/suggest?q={urllib.parse.quote(query)}&format=json"
            req = urllib.request.Request(url, headers={'User-Agent': self._ua})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
            if data and len(data) > 2 and data[2]:
                suggestions = data[2]
                if suggestions and len(suggestions[0]) > 10 and suggestions[0].lower() != query.lower().strip():
                    return suggestions[0][:300]
            return None
        except Exception as e:
            logger.warning(f"Brave error: {e}")
            return None

    def search(self, query):
        logger.info(f"Searching: {query}")

        result = self._brave_summarize(query)
        if result and len(result) > 10:
            logger.info(f"Found via Brave: {result[:100]}")
            return result

        result = self._duckduckgo_lite(query)
        if result and len(result) > 10:
            logger.info(f"Found via DDG Lite: {result[:100]}")
            return result

        result = self._duckduckgo_html(query)
        if result and len(result) > 10:
            logger.info(f"Found via DDG HTML: {result[:100]}")
            return result

        result = self._wikipedia(query)
        if result and len(result) > 20:
            logger.info(f"Found via Wiki: {result[:100]}")
            return result

        logger.info("No useful search results found")
        return None

    def needs_search(self, query):
        ql = query.lower().strip()

        if ql.startswith(("what time", "what date", "what day", "current time",
                        "current date", "today's date", "what's the time",
                        "whats the time", "what's the date", "whats the date",
                        "tell me the time", "tell me the date", "time is it",
                        "date is it", "time now", "date today")):
            return False

        if ql.startswith(("what is", "who is", "what are", "who are")):
            words = ql.split()
            if len(words) <= 5:
                return False

        if ql.startswith(("what", "who", "how", "why", "when", "where")):
            return True

        search_triggers = [
            "weather", "news", "latest", "recent", "current", "today",
            "tell me about", "explain", "describe", "search for", "look up",
            "define", "definition", "meaning of", "who is", "what is",
        ]
        return any(p in ql for p in search_triggers)

web_search = WebSearch()
