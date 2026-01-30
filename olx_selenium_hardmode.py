import time
import json
import random
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configurações
OLX_URL = "https://www.olx.pt/imoveis/apartamento-casa-a-venda/apartamentos-venda/porto/?search%5Bfilter_float_price:from%5D=30000&search%5Bfilter_float_price:to%5D=250000&search%5Bfilter_float_area_util:from%5D=80"
ORIG_PROFILE = r"C:/Users/Joaop/AppData/Local/Google/Chrome/User Data/Default"
TMP_PROFILE = r"C:/Users/Joaop/AGENTEV2/real_estate_bot/tmp_chrome_profile/Default"
TMP_PROFILE_ROOT = r"C:/Users/Joaop/AGENTEV2/real_estate_bot/tmp_chrome_profile"
OUTPUT_FILE = "olx_selenium_results.json"

# Copiar perfil real para pasta temporária
if os.path.exists(TMP_PROFILE):
    shutil.rmtree(TMP_PROFILE)
shutil.copytree(ORIG_PROFILE, TMP_PROFILE)

# Configurar Selenium
chrome_options = Options()
chrome_options.add_argument(f"--user-data-dir={TMP_PROFILE_ROOT}")
chrome_options.add_argument("--profile-directory=Default")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--remote-debugging-port=9222")

# Iniciar driver
print("[INFO] Iniciando Chrome com perfil real...")
driver = webdriver.Chrome(options=chrome_options)

def wait_for_cloudflare(driver, timeout=30):
    print("[INFO] Aguardando Cloudflare...")
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
        print("[INFO] Aceitou cookies.")
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
    # Seletor robusto para cards OLX
    items = driver.find_elements(By.CSS_SELECTOR, 'div[data-cy="l-card"][data-testid="l-card"]')
    # Pré-extrair dados básicos
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
        # Abrir abas
        for ad in batch:
            link = ad['link']
            if link:
                driver.execute_script("window.open(arguments[0], '_blank');", link)
                tab_handles.append(driver.window_handles[-1])
            else:
                tab_handles.append(None)
        # Extrair descrições
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
        # Fechar abas e voltar à principal
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
        print("[ERRO] Nenhum anúncio encontrado! HTML salvo em olx_debug.html")
    return results

try:
    driver.get(OLX_URL)
    if not wait_for_cloudflare(driver, timeout=40):
        print("[ERRO] Cloudflare não ultrapassado!")
        driver.quit()
        exit(1)
    accept_cookies(driver)
    all_ads = []
    page = 1
    while True:
        print(f"[INFO] Extraindo página {page}...")
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
        print(f"[INFO] Total acumulado: {len(all_ads)} anúncios.")
        if not go_to_next_page(driver):
            break
        page += 1
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_ads, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Resultados salvos em {OUTPUT_FILE}")
finally:
    driver.quit()
