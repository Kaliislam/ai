"""Web skills package for Turkish Jarvis.
Provides advanced web search, info refresh, and RSS reading capabilities.
"""

from .web_search_advanced import WebSearchSkill
from .info_refresh import InfoRefreshSkill
from .rss_reader import RSSReaderSkill
from .free_search import FreeSearchEngine, SearchResult, free_search

__all__ = ["WebSearchSkill", "InfoRefreshSkill", "RSSReaderSkill", "FreeSearchEngine", "SearchResult", "free_search"]
