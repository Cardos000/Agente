from .base import BaseScraper, RawListing
import random
import time
import re
from typing import List
from config import MAX_PRICE

class SapoCasaScraper(BaseScraper):
    """
    Scraper para SAPO Casa (imobiliário)
    
    Responsabilidade APENAS: Extrair dados RAW
    - Sem filtros
    - Sem interpretação
    - Sem business logic
    """
    
    BASE_URL = "https://casa.sapo.pt"
    
    def run(self, page) -> List[RawListing]:
        """Scrape SAPO Casa com autenticação e anti-bot"""
        all_listings = []
        try:
            self._handle_authentication(page)
            url = self._build_search_url()
            self.logger.info("Iniciando scrape SAPO Casa")
            listings = self._scrape_with_pagination(page, url)
            all_listings.extend(listings)
            self.stats["listings_found"] = len(all_listings)
        except Exception as e:
            self.logger.error(f"Erro fatal no SAPO: {e}")
            self.stats["errors"] += 1
        return all_listings

    def _build_search_url(self) -> str:
        """Construir URL de busca"""
        # SAPO Casa: apartamentos, Porto, T2, até MAX_PRICE
        return (
            f"{self.BASE_URL}/venda/apartamentos/porto/"
            f"?sa=11&lp=0&hp={MAX_PRICE}&typ=t2"
        )

    def _scrape_with_pagination(self, page, base_url: str) -> List[RawListing]:
        """Scrape com paginação, simulação de humano e anti-bot"""
        listings = []
        page_num = 1
        max_pages = 5

        while page_num <= max_pages:
            url = f"{base_url}&pag={page_num}" if page_num > 1 else base_url
            try:
                self.logger.info(f"Página {page_num}")
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                self.stats["pages_fetched"] += 1
                self._random_delay()
                self._simulate_human(page)
                if self._handle_antibot(page):
                    self.logger.warning("Abortando página devido a bloqueio anti-bot.")
                    break
                self._dismiss_modals(page)
                page_listings = self._extract_listings(page)
                if not page_listings:
                    break
                listings.extend(page_listings)
                self.logger.info(f"Encontrados {len(page_listings)} listings na página {page_num}")
                if not self._has_next_page(page):
                    break
                page_num += 1
            except Exception as e:
                self.logger.warning(f"Erro na página {page_num}: {e}")
                self.stats["errors"] += 1
                break
        return listings

    def _dismiss_modals(self, page):
        """Fechar cookies/modais"""
        try:
            # SAPO tem botão de aceitar cookies
            page.click('button:has-text("Aceitar")', timeout=2000)
        except:
            pass
        
        try:
            page.click('button:has-text("ACEITAR")', timeout=2000)
        except:
            pass

    def _extract_listings(self, page) -> List[RawListing]:
        """Extrair listings"""
        listings = []
        
        try:
            # SAPO usa divs com classes específicas
            items = page.locator('.listing-item').all()
            
            if not items:
                items = page.locator('[data-id]').all()
            
            self.logger.info(f"Total de items: {len(items)}")
            
            for idx, item in enumerate(items):
                try:
                    listing = self._parse_listing(item)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    self.logger.debug(f"Erro ao parsear item {idx}: {e}")
                    self.stats["errors"] += 1
                    continue
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair: {e}")
            self.stats["errors"] += 1
        
        return listings

    def _parse_listing(self, item) -> RawListing:
        """Parse um item"""
        listing = RawListing()
        listing.portal = "SAPO"
        
        try:
            link_el = item.locator('a').first
            if link_el:
                href = link_el.get_attribute('href')
                if href:
                    listing.link = href if href.startswith('http') else f"{self.BASE_URL}{href}"
        except:
            pass
        
        # Robust title extraction: try headline/h2/h3/a, fallback to first line
        try:
            title = None
            for selector in ['.headline', 'h2', 'h3', 'a']:
                el = item.locator(selector).first
                if el and el.is_visible():
                    t = el.inner_text().strip()
                    if t:
                        title = t
                        break
            if not title:
                text = item.inner_text()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                if lines:
                    title = lines[0]
            if title:
                listing.title = title[:200]
        except:
            pass
        
        try:
            text = item.inner_text()
            price_match = re.search(r'(\d[\d\s\.]*)\s*€', text)
            if price_match:
                listing.price = price_match.group(1).replace(' ', '').replace('.', '')
        except:
            pass
        
        try:
            text = item.inner_text().lower()
            area_match = re.search(r'(\d+)\s*m²', text)
            if area_match:
                listing.area = f"{area_match.group(1)} m²"
        except:
            pass
        
        try:
            # Tipologia via regex
            inner_text = item.inner_text()
            typology_match = re.search(r'T(\d+)', inner_text)
            if typology_match:
                listing.typology = f"T{typology_match.group(1)}"
        except:
            pass
        
        try:
            listing.description = item.inner_text()[:500]
        except:
            pass
        
        return listing

    def _has_next_page(self, page) -> bool:
        """Verificar próxima página"""
        try:
            # SAPO geralmente tem link "Próxima"
            next_links = page.locator('a:has-text("próxima")').all()
            return len(next_links) > 0
        except:
            return False
