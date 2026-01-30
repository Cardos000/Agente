
from .base import BaseScraper, RawListing
import random
import time
import os
import shutil
import json
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from config import MAX_PRICE

class OlxScraper(BaseScraper):

    def run(self, page=None) -> List[RawListing]:
        # --- CÓPIA FIEL DO HARDMODE ---
        OLX_URL = "https://www.olx.pt/imoveis/apartamento-casa-a-venda/apartamentos-venda/porto/?search%5Bfilter_float_price:from%5D=30000&search%5Bfilter_float_price:to%5D=250000&search%5Bfilter_float_area_util:from%5D=80"
        ORIG_PROFILE = r"C:/Users/Joaop/AppData/Local/Google/Chrome/User Data/Default"
        TMP_PROFILE = r"C:/Users/Joaop/AGENTEV2/real_estate_bot/tmp_chrome_profile/Default"
        TMP_PROFILE_ROOT = r"C:/Users/Joaop/AGENTEV2/real_estate_bot/tmp_chrome_profile"

        # Copiar perfil real para pasta temporária (apagar sempre)
        if os.path.exists(TMP_PROFILE):
            shutil.rmtree(TMP_PROFILE)
        shutil.copytree(ORIG_PROFILE, TMP_PROFILE)

        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={TMP_PROFILE_ROOT}")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--remote-debugging-port=9222")

        driver = webdriver.Chrome(options=chrome_options)

        def wait_for_cloudflare(driver, timeout=30):
            start = time.time()
            while time.time() - start < timeout:
                if "Checking your browser" not in driver.page_source and "Cloudflare" not in driver.page_source:
                    return True
                time.sleep(1)
            return False

        def accept_cookies(driver):
            try:
                btn = driver.find_element(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Concordo')]")
                btn.click()
                time.sleep(2)
            except Exception:
                pass

        def human_scroll_until_end(driver, max_scrolls=50):
            last_count = 0
            for i in range(max_scrolls):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2.5, 4.5))
                items = driver.find_elements(By.CSS_SELECTOR, 'div[data-cy="l-card"][data-testid="l-card"]')
                if len(items) == last_count:
                    break
                last_count = len(items)
            time.sleep(3)

        def go_to_next_page(driver):
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="pagination-forward"]')
                if next_btn.is_enabled():
                    next_btn.click()
                    time.sleep(random.uniform(2.5, 4.5))
                    return True
            except Exception:
                pass
            return False

        def extract_ads(driver):
            items = driver.find_elements(By.CSS_SELECTOR, 'div[data-cy="l-card"][data-testid="l-card"]')
            basic_ads = []
            for item in items:
                try:
                    title = item.find_element(By.CSS_SELECTOR, '[data-testid="ad-card-title"] h4').text if item.find_elements(By.CSS_SELECTOR, '[data-testid="ad-card-title"] h4') else None
                    link = item.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') if item.find_elements(By.CSS_SELECTOR, 'a') else None
                    price = item.find_element(By.CSS_SELECTOR, '[data-testid="ad-price"]').text if item.find_elements(By.CSS_SELECTOR, '[data-testid="ad-price"]') else None
                    location = item.find_element(By.CSS_SELECTOR, '[data-testid="location-date"]').text if item.find_elements(By.CSS_SELECTOR, '[data-testid="location-date"]') else None
                    image = item.find_element(By.CSS_SELECTOR, 'img').get_attribute('src') if item.find_elements(By.CSS_SELECTOR, 'img') else None
                    basic_ads.append({'title': title, 'link': link, 'price': price, 'location': location, 'image': image})
                except Exception:
                    continue

            # Extrair descrições em paralelo (até 4 abas abertas)
            results = []
            max_tabs = 4
            idx = 0
            while idx < len(basic_ads):
                batch = basic_ads[idx:idx+max_tabs]
                tab_handles = []
                for ad in batch:
                    link = ad['link']
                    if link:
                        driver.execute_script("window.open(arguments[0], '_blank');", link)
                        tab_handles.append(driver.window_handles[-1])
                    else:
                        tab_handles.append(None)
                for i, ad in enumerate(batch):
                    description = None
                    if tab_handles[i]:
                        try:
                            driver.switch_to.window(tab_handles[i])
                            time.sleep(random.uniform(1.0, 1.7))
                            try:
                                btn = driver.find_element(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Concordo')]")
                                btn.click()
                                time.sleep(0.4)
                            except Exception:
                                pass
                            try:
                                desc_elem = driver.find_element(By.CSS_SELECTOR, 'div[data-cy="ad_description"], div[data-testid="ad_description"]')
                                description = desc_elem.text.strip()
                            except Exception:
                                description = None
                        except Exception:
                            description = None
                    ad['description'] = description
                main_handle = driver.window_handles[0]
                for handle in tab_handles:
                    if handle and handle in driver.window_handles:
                        try:
                            driver.switch_to.window(handle)
                            driver.close()
                        except Exception:
                            pass
                if main_handle in driver.window_handles:
                    driver.switch_to.window(main_handle)
                time.sleep(random.uniform(0.5, 1.0))
                results.extend(batch)
                idx += max_tabs
            if not results:
                with open("olx_debug.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                self.logger.error("Nenhum anúncio encontrado! HTML salvo em olx_debug.html")
            return results

        try:
            driver.get(OLX_URL)
            if not wait_for_cloudflare(driver, timeout=40):
                self.logger.error("Cloudflare não ultrapassado!")
                driver.quit()
                return []
            accept_cookies(driver)
            all_ads = []
            page = 1
            while True:
                self.logger.info(f"Extraindo página {page}...")
                human_scroll_until_end(driver, max_scrolls=50)
                ads = extract_ads(driver)
                all_ads.extend(ads)
                # Remover duplicados por link
                seen = set()
                unique_ads = []
                for ad in all_ads:
                    if ad['link'] and ad['link'] not in seen:
                        unique_ads.append(ad)
                        seen.add(ad['link'])
                all_ads = unique_ads
                self.logger.info(f"Total acumulado: {len(all_ads)} anúncios.")
                if not go_to_next_page(driver):
                    break
                page += 1
        finally:
            driver.quit()

        # Converter para RawListing
        listings = []
        for ad in all_ads:
            listing = RawListing()
            listing.portal = "OLX"
            listing.title = ad.get('title')
            listing.price = ad.get('price')
            listing.area = None
            listing.location = ad.get('location')
            listing.description = ad.get('description')
            listing.link = ad.get('link')
            listing.published_date = None
            listings.append(listing)
        self.stats["listings_found"] = len(listings)
        return listings

    def _accept_cookies(self, page):
        """Aceitar modal de cookies se aparecer"""
        try:
            # OLX pode ter vários botões de consentimento
            selectors = [
                'button:has-text("Aceito")',
                'button:has-text("Concordo")',
                '#onetrust-accept-btn-handler',
                '[data-testid="uc-accept-all"]',
            ]
            for sel in selectors:
                if page.locator(sel).first.is_visible():
                    page.click(sel, timeout=2000)
                    self.logger.info("Cookies aceites")
                    break
        except Exception:
            pass

    def _build_search_url(self) -> str:
        """Construir URL de busca para OLX"""
        # OLX: apartamentos em Porto até MAX_PRICE
        return f"{self.BASE_URL}/imoveis/apartamentos/porto/?priceRange=0,{MAX_PRICE}"

    def _scrape_with_pagination(self, page, base_url: str) -> List[RawListing]:
        """Scrape com paginação, simulação de humano e anti-bot"""
        listings = []
        page_num = 1
        max_pages = 5

        while page_num <= max_pages:
            url = f"{base_url}&page={page_num}" if '?' in base_url else f"{base_url}?page={page_num}"
            if page_num == 1:
                url = base_url
            try:
                self.logger.info(f"Página {page_num}: {url[:80]}...")
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
                    self.logger.info(f"Nenhum listing na página {page_num}")
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
        """Fechar modais/cookies"""
        try:
            # OLX pode ter modal de cookies
            page.click('button:has-text("Concordo")', timeout=2000)
        except:
            pass
        
        try:
            # Fechar modal de login
            page.click('[aria-label*="Fechar"]', timeout=2000)
        except:
            pass

    def _extract_listings(self, page) -> List[RawListing]:
        """Extrair listings brutos"""
        listings = []
        
        try:
            # OLX usa divs com classes específicas
            # Procurar por elementos que contêm listings
            items = page.locator('[data-testid="listing"]').all()
            
            if not items:
                # Alternativa
                items = page.locator('a[href*="/imoveis/"]').all()
            
            self.logger.info(f"Total de items encontrados: {len(items)}")
            
            for idx, item in enumerate(items):
                try:
                    listing = self._parse_listing(item)
                    
                    if listing and listing.link:
                        listings.append(listing)
                    elif listing:
                        listings.append(listing)
                        
                except Exception as e:
                    self.logger.debug(f"Erro ao parsear item {idx}: {e}")
                    self.stats["errors"] += 1
                    continue
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair listings: {e}")
            self.stats["errors"] += 1
        
        return listings

    def _parse_listing(self, item) -> RawListing:
        """Parse um item em RawListing"""
        listing = RawListing()
        listing.portal = "OLX"
        
        try:
            # Link
            link_el = None
            if item.tag_name() == 'a':
                href = item.get_attribute('href')
                if href:
                    listing.link = href if href.startswith('http') else f"{self.BASE_URL}{href}"
            else:
                link_el = item.locator('a').first
                if link_el:
                    href = link_el.get_attribute('href')
                    if href:
                        listing.link = href if href.startswith('http') else f"{self.BASE_URL}{href}"
        except:
            pass
        
        # Robust title extraction: try h2/h3/a, fallback to first line
        try:
            title = None
            for selector in ['h2', 'h3', 'a']:
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
        
        # Preço e área + preço/m2
        try:
            text = item.inner_text()
            price_match = re.search(r'(\d[\d\s\.]*)\s*€', text)
            if price_match:
                price = price_match.group(1).replace(' ', '').replace('.', '')
                listing.price = price
            else:
                price = None
        except:
            price = None
        try:
            text = item.inner_text().lower()
            area_match = re.search(r'(\d+)\s*m²', text)
            if area_match:
                area = int(area_match.group(1))
                listing.area = f"{area} m²"
            else:
                area = None
        except:
            area = None
        # Preço por m2
        try:
            if price and area:
                price_m2 = int(price) / area
                listing.price_m2 = round(price_m2, 2)
        except:
            pass
        
        # Localização detalhada
        try:
            text = item.inner_text()
            # OLX geralmente coloca localização em uma linha separada
            lines = text.split('\n')
            found = None
            for line in lines:
                if any(loc in line.lower() for loc in ['porto', 'matosinhos', 'gondomar', 'maia', 'valongo', 'gaia', 'póvoa', 'espinho', 'lousada', 'penafiel']):
                    found = line.strip()
                    break
            if found:
                listing.location = found[:100]
        except:
            pass
        
        try:
            # Descrição
            listing.description = item.inner_text()[:500]
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
        # Data publicação
        try:
            inner_text = item.inner_text().lower()
            date_match = re.search(r'adicionado\s*(há\s*\d+\s*(?:dia|hora|semana|mês|ano)s?|ontem|hoje)', inner_text)
            if date_match:
                listing.published_date = date_match.group(1)
        except:
            pass
        # Atributos extra: garagem, elevador, terraço/varanda, condição
        try:
            inner_text = item.inner_text().lower()
            if any(x in inner_text for x in ['garagem', 'box']):
                listing.garage = True
            if 'elevador' in inner_text:
                listing.elevator = True
            if any(x in inner_text for x in ['terraço', 'varanda']):
                listing.terrace = True
            if 'novo' in inner_text:
                listing.condition = 'Novo'
            elif 'usado' in inner_text:
                listing.condition = 'Usado'
        except:
            pass
        
        return listing

    def _has_next_page(self, page) -> bool:
        """Verificar próxima página"""
        try:
            next_btn = page.locator('[aria-label="Próxima página"]').first
            return next_btn.is_visible()
        except:
            return False
        results = []
        try:
            # 1. Ninja Entry via Google masking
            target_url = "https://www.olx.pt/imoveis/apartamento-casa-a-venda/apartamentos-arrenda-venda/t2/porto/?search%5Bfilter_float_price%3Ato%5D=240000"
            self.ninja_entry(page, target_url)
            
            # Cookies handling with human jitter
            try:
                page.wait_for_selector('#onetrust-accept-btn-handler', timeout=5000)
                time.sleep(random.uniform(0.5, 1.5))
                page.click('#onetrust-accept-btn-handler')
                self.simulate_human(page)
            except: pass

            # Anti-bot response check
            if "houston" in page.url.lower():
                self.logger.error("OLX Ninja Entry Failed (Houston). Bot detected.")
                return []

            # 2. Dynamic Scroll and Loading
            page.evaluate("window.scrollBy({top: 800, behavior: 'smooth'})")
            time.sleep(random.uniform(2, 4))

            cards = page.locator('[data-cy="l-card"]').all()
            self.logger.info(f"Ninja found {len(cards)} entries on OLX")
            
            for item in cards:
                try:
                    if not item.is_visible(): continue

                    link_el = item.locator('a').first
                    link = link_el.get_attribute("href")
                    if not link: continue
                    if not link.startswith("http"): link = "https://www.olx.pt" + link

                    title = item.locator('[data-cy="ad-card-title"], h6').first.inner_text().strip()
                    price_text = item.locator('[data-testid="ad-price"]').first.inner_text().strip()
                    
                    # Scanning for Ninja insights
                    card_text = item.inner_text().lower()
                    
                    # Precision Transport Fix
                    transport = "Não"
                    if any(x in card_text for x in ["comboio", "estação de cp"]):
                        transport = "Comboio"
                    elif re.search(r'\bmetro\b', card_text):
                        transport = "Metro"

                    results.append({
                        "title": title, "price": price_text, "price_m2": "N/A", "area": "N/A",
                        "date": "N/A", "location": "Porto", "condition": "Usado",
                        "garage": "Sim" if "garagem" in card_text else "Não",
                        "elevator": "Sim" if "elevador" in card_text else "Não",
                        "terrace": "Sim" if any(x in card_text for x in ["terraço", "varanda"]) else "Não",
                        "transport": transport, "description": title, "link": link, "portal": "OLX"
                    })
                except: continue
        except Exception as e:
            self.logger.error(f"OLX Ninja Error: {e}")
            
        return results
