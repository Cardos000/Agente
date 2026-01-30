import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

class OlxSeleniumSpider(scrapy.Spider):
    name = "olx_selenium"
    start_urls = ["https://www.olx.pt/imoveis/apartamentos/porto/?priceRange=0,250000"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        # Copia o perfil real para uma pasta temporária para evitar conflito
        import shutil, os
        orig_profile = r"C:/Users/Joaop/AppData/Local/Google/Chrome/User Data/Default"
        tmp_profile = r"C:/Users/Joaop/AGENTEV2/real_estate_bot/tmp_chrome_profile/Default"
        if os.path.exists(tmp_profile):
            shutil.rmtree(tmp_profile)
        shutil.copytree(orig_profile, tmp_profile)
        chrome_options.add_argument(f"--user-data-dir=C:/Users/Joaop/AGENTEV2/real_estate_bot/tmp_chrome_profile")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--remote-debugging-port=9222")
        self.driver = webdriver.Chrome(options=chrome_options)

    def parse(self, response):
        self.driver.get(self.start_urls[0])
        time.sleep(5)
        # Aceitar cookies se aparecer
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(., 'Aceito') or contains(., 'Concordo')]")
            btn.click()
            time.sleep(2)
        except Exception:
            pass
        # Scroll para carregar anúncios
        for _ in range(3):
            self.driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
        # Extrair anúncios
        items = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="listing"]')
        for item in items:
            try:
                title = item.text.split('\n')[0]
                link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                yield {'title': title, 'link': link}
            except Exception:
                continue
        self.driver.quit()
