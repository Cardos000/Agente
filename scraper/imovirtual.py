
import os
import random
import time
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base import BaseScraper, RawListing
from config import MAX_PRICE, MIN_PRICE, MIN_AREA


class ImovirtualScraper(BaseScraper):
    """Scraper para Imovirtual.com via Selenium"""
    BASE_URL = "https://www.imovirtual.com"
    API_URL = "https://www.imovirtual.com/api/query"

    def scrape(self) -> List[RawListing]:
        """Entry point sem Playwright para Selenium."""
        return self.run(None)

    def run(self, page=None) -> List[RawListing]:
        """Scrape Imovirtual via Selenium (anti-bot)"""
        imovirtual_url = (
            f"{self.BASE_URL}/comprar/apartamento/porto/porto/"
            f"?priceMin={MIN_PRICE}&priceMax={MAX_PRICE}&areaMin={MIN_AREA}"
        )
        profile_root = os.path.join(os.path.dirname(__file__), '..', 'tmp_chrome_profile_imovirtual')
        profile_root = os.path.abspath(profile_root)
        profile_default = os.path.join(profile_root, 'Default')
        if not os.path.exists(profile_root):
            os.makedirs(profile_root, exist_ok=True)

        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={profile_root}")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        if self.headless:
            chrome_options.add_argument("--headless=new")

        driver = webdriver.Chrome(options=chrome_options)

        def wait_for_cloudflare(timeout=40):
            start = time.time()
            while time.time() - start < timeout:
                source = driver.page_source
                if "Checking your browser" not in source and "Cloudflare" not in source:
                    return True
                time.sleep(1)
            return False

        def accept_cookies():
            try:
                btn = driver.find_element(
                    By.XPATH,
                    "//button[contains(., 'Aceito') or contains(., 'Concordo') or contains(., 'Aceitar')]"
                )
                btn.click()
                time.sleep(2)
            except Exception:
                pass

        def human_scroll_until_end(max_scrolls=50):
            last_count = 0
            for _ in range(max_scrolls):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2.5, 4.5))
                items = driver.find_elements(By.CSS_SELECTOR, 'article[data-sentry-component="AdvertCard"]')
                if len(items) == last_count:
                    break
                last_count = len(items)
            time.sleep(2)

        def go_to_next_page():
            try:
                next_btn = driver.find_element(
                    By.CSS_SELECTOR,
                    'a[aria-label="Próxima página"], a[aria-label="Next page"]'
                )
                if next_btn.is_enabled():
                    next_btn.click()
                    time.sleep(random.uniform(2.5, 4.5))
                    return True
            except Exception:
                pass
            return False

        def extract_ads():
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-sentry-component="AdvertCard"]'))
                )
            except Exception:
                self.logger.error("Nenhum anúncio encontrado após espera")
                with open("imovirtual_debug.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                return []
            items = driver.find_elements(By.CSS_SELECTOR, 'article[data-sentry-component="AdvertCard"]')
            basic_ads = []
            for item in items:
                try:
                    title = None
                    title_el = item.find_elements(By.CSS_SELECTOR, '[data-cy="listing-item-title"]')
                    if title_el:
                        title = title_el[0].text.strip()
                    link = None
                    link_el = item.find_elements(By.CSS_SELECTOR, '[data-cy="listing-item-link"]')
                    if link_el:
                        link = link_el[0].get_attribute('href')
                        if link and link.startswith('/'):
                            link = f"{self.BASE_URL}{link}"
                    location = None
                    location_el = item.find_elements(By.CSS_SELECTOR, '[data-sentry-component="Address"]')
                    if location_el:
                        location = location_el[0].text.strip()
                    price = None
                    price_el = item.find_elements(By.CSS_SELECTOR, '[data-sentry-element="MainPrice"]')
                    if price_el:
                        price = price_el[0].text.strip()
                    area = None
                    area_el = item.find_elements(By.XPATH, './/span[contains(text(),"m²")]')
                    if area_el:
                        area = area_el[0].text.strip()
                    typology = None
                    typology_el = item.find_elements(By.XPATH, './/span[starts-with(normalize-space(), "T")]')
                    if typology_el:
                        typology = typology_el[0].text.strip()
                    if title and link:
                        basic_ads.append(
                            {
                                "title": title,
                                "link": link,
                                "price": price,
                                "location": location,
                                "area": area,
                                "typology": typology,
                            }
                        )
                except Exception:
                    continue
            return basic_ads

        try:
            driver.get(imovirtual_url)
            if not wait_for_cloudflare():
                self.logger.error("Cloudflare não ultrapassado")
                return []
            accept_cookies()
            all_ads = []
            page_num = 1
            while True:
                self.logger.info(f"Extraindo página {page_num}...")
                human_scroll_until_end()
                ads = extract_ads()
                all_ads.extend(ads)
                seen = set()
                unique_ads = []
                for ad in all_ads:
                    if ad['link'] and ad['link'] not in seen:
                        unique_ads.append(ad)
                        seen.add(ad['link'])
                all_ads = unique_ads
                self.stats["pages_fetched"] += 1
                self.logger.info(f"Total acumulado: {len(all_ads)} anúncios.")
                if not go_to_next_page():
                    break
                page_num += 1
        finally:
            driver.quit()

        listings = []
        for ad in all_ads:
            listing = RawListing()
            listing.portal = "Imovirtual"
            listing.title = ad.get('title')
            listing.price = ad.get('price')
            listing.area = ad.get('area')
            listing.location = ad.get('location')
            listing.description = None
            listing.link = ad.get('link')
            listing.published_date = None
            listings.append(listing)
        self.stats["listings_found"] = len(listings)
        return listings
