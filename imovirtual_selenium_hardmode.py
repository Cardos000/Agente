import time
import json
import random
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configurações
IMOVIRTUAL_URL = "https://www.imovirtual.com/comprar/apartamento/porto/porto/?priceMin=50000&priceMax=250000&areaMin=80"
ORIG_PROFILE = r"C:/Users/Joaop/AppData/Local/Google/Chrome/User Data/Default"
TMP_PROFILE = r"C:/Users/Joaop/AGENTEV2/real_estate_bot/tmp_chrome_profile_imovirtual/Default"
TMP_PROFILE_ROOT = r"C:/Users/Joaop/AGENTEV2/real_estate_bot/tmp_chrome_profile_imovirtual"
OUTPUT_FILE = "imovirtual_selenium_results.json"

# Copiar perfil real para pasta temporária
if os.path.exists(TMP_PROFILE):
    shutil.rmtree(TMP_PROFILE)
shutil.copytree(ORIG_PROFILE, TMP_PROFILE)

# Configurar Selenium
chrome_options = Options()
chrome_options.add_argument(f"--user-data-dir={TMP_PROFILE_ROOT}")
chrome_options.add_argument("--profile-directory=Default")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--remote-debugging-port=9223")

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
        btn = driver.find_element(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Concordo') or contains(., 'Aceitar')]" )
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
        # Tentar encontrar cards por múltiplos seletores possíveis
        items = driver.find_elements(By.CSS_SELECTOR, 'article[data-cy="listing-item"], section > article, article')
        if len(items) == last_count:
            break
        last_count = len(items)
    time.sleep(3)

def go_to_next_page(driver):
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Próxima página"], a[aria-label="Next page"]')
        if next_btn.is_enabled():
            next_btn.click()
            time.sleep(random.uniform(2.5, 4.5))
            return True
    except Exception:
        pass
    return False

def extract_ads(driver):
    # Esperar explicitamente até os anúncios aparecerem
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-cy="listing-item"], section > article, article'))
        )
    except Exception:
        print("[ERRO] Nenhum anúncio encontrado após espera!")
        with open("imovirtual_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return []
    # Tentar múltiplos seletores para garantir robustez
    items = driver.find_elements(By.CSS_SELECTOR, 'article[data-cy="listing-item"], section > article, article')
    basic_ads = []
    for item in items:
        try:
            title = item.find_element(By.CSS_SELECTOR, 'h2, h3').text if item.find_elements(By.CSS_SELECTOR, 'h2, h3') else None
            link = item.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') if item.find_elements(By.CSS_SELECTOR, 'a') else None
            price = item.find_element(By.CSS_SELECTOR, '[data-cy="listing-price"], .offer-price, .price, .css-1n1x6u2').text if item.find_elements(By.CSS_SELECTOR, '[data-cy="listing-price"], .offer-price, .price, .css-1n1x6u2') else None
            location = item.find_element(By.CSS_SELECTOR, '[data-cy="listing-location"], .location, .css-1a4brun').text if item.find_elements(By.CSS_SELECTOR, '[data-cy="listing-location"], .location, .css-1a4brun') else None
            image = item.find_element(By.CSS_SELECTOR, 'img').get_attribute('src') if item.find_elements(By.CSS_SELECTOR, 'img') else None
            # Só adiciona se tiver título e link
            if title and link:
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
                        btn = driver.find_element(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Concordo') or contains(., 'Aceitar')]")
                        btn.click()
                        time.sleep(0.4)
                    except Exception:
                        pass
                    try:
                        desc_elem = driver.find_element(By.CSS_SELECTOR, '[data-cy="adPageAdDescription"]')
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
        # Guardar screenshot para debug visual
        try:
            driver.save_screenshot("imovirtual_debug.png")
            print("[DEBUG] Screenshot guardado em imovirtual_debug.png")
        except Exception as e:
            print(f"[ERRO] Falha ao guardar screenshot: {e}")
        with open("imovirtual_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("[ERRO] Nenhum anúncio encontrado! HTML salvo em imovirtual_debug.html")
    return results

try:
    driver.get(IMOVIRTUAL_URL)
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
