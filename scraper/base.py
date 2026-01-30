from playwright.sync_api import sync_playwright
from abc import ABC, abstractmethod
import logging
import random
import time
from datetime import datetime
from typing import List, Dict, Optional

class RawListing:
    """Wrapper para dados brutos extraídos do scraper"""
    def __init__(self):
        self.title: Optional[str] = None
        self.price: Optional[str] = None
        self.area: Optional[str] = None
        self.location: Optional[str] = None
        self.description: Optional[str] = None
        self.link: Optional[str] = None
        self.published_date: Optional[str] = None
        self.portal: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "price": self.price,
            "area": self.area,
            "location": self.location,
            "description": self.description,
            "link": self.link,
            "published_date": self.published_date,
            "portal": self.portal,
            "scraped_at": datetime.now().isoformat()
        }

class BaseScraper(ABC):
    def _handle_antibot(self, page):
        """Hook para tratamento de bloqueios anti-bot/captcha (sobrescrever nos filhos)"""
        try:
            content = page.content().lower()
            if "captcha" in content or "cloudflare" in content or "houston" in content:
                self.logger.warning("Possível bloqueio anti-bot detectado!")
                return True
        except Exception:
            pass
        return False

    def __init__(self, headless=False, delay_range=(4, 10)):
        # headless=False para simular browser real
        self.headless = headless
        self.delay_range = delay_range  # delays maiores
        self.logger = self._setup_logger()
        self.stats = {
            "pages_fetched": 0,
            "listings_found": 0,
            "errors": 0
        }

    def _simulate_human(self, page):
        """Simula ações humanas para evitar bloqueios anti-bot"""
        try:
            page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            page.mouse.click(random.randint(100, 500), random.randint(100, 500))
            page.keyboard.press('PageDown')
            time.sleep(random.uniform(0.5, 1.5))
            page.mouse.wheel(0, random.randint(200, 800))
        except Exception:
            pass

    def _handle_authentication(self, page):
        """Hook para login/autenticação se necessário (sobrescrever nos filhos)"""
        pass

    def _setup_logger(self) -> logging.Logger:
        """Configurar logger específico do scraper"""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'[{self.__class__.__name__}] %(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def scrape(self) -> List[RawListing]:
        """Entry point - executa o scraper em contexto Playwright"""
        try:
            from playwright_stealth import Stealth
            from fake_useragent import UserAgent
        except ImportError:
            self.logger.error("Dependências faltando: playwright-stealth, fake-useragent")
            return []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox"
                ]
            )

            try:
                ua = UserAgent()
                viewport = random.choice([
                    {"width": 1920, "height": 1080},
                    {"width": 1440, "height": 900},
                    {"width": 1366, "height": 768}
                ])

                context = browser.new_context(
                    user_agent=ua.random,
                    viewport=viewport,
                    locale="pt-PT",
                    timezone_id="Europe/Lisbon"
                )

                context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                page = context.new_page()
                
                try:
                    from playwright_stealth import Stealth
                    Stealth().apply_stealth_sync(page)
                except:
                    pass

                results = self.run(page)
                
                self.logger.info(
                    f"[STATS] Pages: {self.stats['pages_fetched']}, "
                    f"Listings: {self.stats['listings_found']}, "
                    f"Errors: {self.stats['errors']}"
                )

                page.close()
                context.close()
                return results

            except Exception as e:
                self.logger.error(f"Fatal scraper error: {e}", exc_info=True)
                return []
            finally:
                browser.close()

    def _random_delay(self):
        """Delay aleatório para simular comportamento humano"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

    def _safe_extract(self, text: Optional[str], pattern: str = None) -> Optional[str]:
        """
        Extração defensiva: retorna None se falhar.
        Se pattern é None, apenas remove whitespace.
        """
        if not text:
            return None
        
        text = str(text).strip()
        if not text:
            return None

        if pattern:
            import re
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
            return None

        return text

    @abstractmethod
    def run(self, page) -> List[RawListing]:
        """
        Implementar em cada scraper:
        - Navegar para URLs
        - Extrair dados brutos
        - Retornar lista de RawListing
        
        DEVE LOGAR:
        - Páginas visitadas
        - Listings encontrados
        - Erros (mas continuar executando)
        """
        pass
