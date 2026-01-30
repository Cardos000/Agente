"""
Scrapers para portais imobiliários
Extraem dados RAW sem interpretação ou filtros
"""

from .base import BaseScraper, RawListing
from .imovirtual import ImovirtualScraper
from .idealista import IdealistaScraper
from .olx import OlxScraper
from .casayes import CasaYesScraper
from .sapocasa import SapoCasaScraper
from .supercasa import SuperCasaScraper
from .orchestrator import ScraperOrchestrator

__all__ = [
    "BaseScraper",
    "RawListing",
    "ImovirtualScraper",
    "IdealistaScraper",
    "OlxScraper",
    "CasaYesScraper",
    "SapoCasaScraper",
    "SuperCasaScraper",
    "ScraperOrchestrator",
]
