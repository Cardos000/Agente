from .base import BaseScraper, RawListing
import random
import time
import re
from typing import List
from config import MAX_PRICE

class IdealistaScraper(BaseScraper):
    """
    Scraper para Idealista.pt
    
    Responsabilidade APENAS: Extrair dados RAW
    - Sem filtros
    - Sem interpretação
    - Sem business logic
    """
    
    BASE_URL = "https://www.idealista.pt"
    
    def run(self, page) -> List[RawListing]:
        """Scrape Idealista com paginação, autenticação e anti-bot"""
        all_listings = []
        try:
            self._handle_authentication(page)
            url = self._build_search_url()
            self.logger.info(f"Iniciando scrape Idealista")
            listings = self._scrape_with_pagination(page, url)
            all_listings.extend(listings)
            self.stats["listings_found"] = len(all_listings)
        except Exception as e:
            self.logger.error(f"Erro fatal no Idealista: {e}")
            self.stats["errors"] += 1
        return all_listings

    def _build_search_url(self) -> str:
        """Construir URL de busca para Idealista"""
        # Busca: Porto, T2+, até MAX_PRICE, ordenado por recente
        return (
            f"{self.BASE_URL}/comprar/casas/porto-distrito/"
            f"com-preco-max_{MAX_PRICE},t2/?ordem=publicado-desc"
        )

    def _scrape_with_pagination(self, page, base_url: str) -> List[RawListing]:
        """Scrape com paginação, simulação de humano e anti-bot"""
        listings = []
        page_num = 1
        max_pages = 5

        while page_num <= max_pages:
            url = f"{base_url}&pagina={page_num}" if page_num > 1 else base_url
            try:
                self.logger.info(f"Página {page_num}: {url[:80]}...")
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                self.stats["pages_fetched"] += 1
                self._random_delay()
                self._simulate_human(page)
                if self._handle_antibot(page):
                    self.logger.warning("Abortando página devido a bloqueio anti-bot.")
                    break
                self._dismiss_cookies(page)
                page_listings = self._extract_listings(page)
                if not page_listings:
                    self.logger.info(f"Nenhum listing encontrado na página {page_num}")
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

    def _dismiss_cookies(self, page):
        """Fechar modal de cookies"""
        try:
            page.click('#didomi-notice-agree-button', timeout=3000)
            time.sleep(random.uniform(0.5, 1.5))
        except:
            pass

    def _extract_listings(self, page) -> List[RawListing]:
        """Extrair listings brutos da página"""
        listings = []
        
        try:
            # Idealista usa 'article.item'
            articles = page.locator('article.item').all()
            
            self.logger.info(f"Total de articles encontrados: {len(articles)}")
            
            for idx, article in enumerate(articles):
                try:
                    listing = self._parse_listing(article)
                    
                    if listing and listing.link:
                        listings.append(listing)
                    elif listing:
                        listings.append(listing)
                        self.logger.debug(f"Listing {idx} sem link, mas adicionado")
                        
                except Exception as e:
                    self.logger.debug(f"Erro ao parsear article {idx}: {e}")
                    self.stats["errors"] += 1
                    continue
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair listings: {e}")
            self.stats["errors"] += 1
        
        return listings

    def _parse_listing(self, article) -> RawListing:
        """Parse um article em RawListing"""
        listing = RawListing()
        listing.portal = "Idealista"
        
        try:
            # Link
            link_el = article.locator('.item-link').first
            if link_el:
                href = link_el.get_attribute('href')
                if href:
                    listing.link = f"{self.BASE_URL}{href}" if href.startswith('/') else href
        except:
            pass
        
        # Robust title extraction: try .item-link, h2, h3, a, fallback to first line
        try:
            title = None
            for selector in ['.item-link', 'h2', 'h3', 'a']:
                el = article.locator(selector).first
                if el and el.is_visible():
                    t = el.inner_text().strip()
                    if t:
                        title = t
                        break
            if not title:
                text = article.inner_text()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                if lines:
                    title = lines[0]
            if title:
                listing.title = title[:200]
        except:
            pass
        
        try:
            # Preço
            price_el = article.locator('.item-price').first
            if price_el:
                price_text = price_el.inner_text().strip()
                # Extrair apenas números
                price_match = re.search(r'(\d[\d\s\.]*)', price_text)
                if price_match:
                    listing.price = price_match.group(1).replace(' ', '').replace('.', '')
        except:
            pass
        
        try:
            # Localização e área
            card_text = article.inner_text().lower()
            
            # Área
            area_match = re.search(r'(\d+)\s*m²', card_text)
            if area_match:
                listing.area = f"{area_match.group(1)} m²"
            
            # Localização (procurar padrão de zona)
            # Idealista geralmente coloca em "Porto - Zona"
            location_lines = article.inner_text().split('\n')
            for line in location_lines:
                if 'porto' in line.lower() or 'matosinhos' in line.lower():
                    listing.location = line.strip()[:100]
                    break
                    
        except:
            pass
        
        try:
            # Descrição é texto completo
            listing.description = article.inner_text()[:500]
        except:
            pass
        
        try:
            # Data de publicação
            inner_text = article.inner_text()
            date_match = re.search(r'(há\s+\d+\s+(?:hora|dia|semana|mês)s?)', inner_text, re.IGNORECASE)
            if date_match:
                listing.published_date = date_match.group(1)
        except:
            pass
        
        try:
            # Tipologia via regex
            inner_text = article.inner_text()
            typology_match = re.search(r'T(\d+)', inner_text)
            if typology_match:
                listing.typology = f"T{typology_match.group(1)}"
        except:
            pass
        
        return listing

    def _has_next_page(self, page) -> bool:
        """Verificar se existe próxima página"""
        try:
            # Idealista geralmente tem botão "Próxima" ou link com classe específica
            next_elements = page.locator('a[title="Siguiente"]').all()
            if next_elements:
                return True
            
            # Alternativa
            next_elements = page.locator('[aria-label*="Siguiente"]').all()
            return len(next_elements) > 0
            
        except:
            return False
