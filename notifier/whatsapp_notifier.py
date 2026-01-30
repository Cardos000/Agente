import requests
import logging
import urllib.parse
from config import WHATSAPP_NUMBER, WHATSAPP_API_KEY

class WhatsAppNotifier:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = "https://api.callmebot.com/whatsapp.php"

    def send_report(self, listings):
        if not listings:
            self.logger.info("No new listings to send via WhatsApp.")
            return

        if not WHATSAPP_NUMBER or not WHATSAPP_API_KEY:
            self.logger.warning("WhatsApp credentials not set in .env. Skipping WhatsApp.")
            return

        # 1. Sort by best Price/m2
        def get_price_m2(item):
            pm2 = item.get('price_m2', 'N/A')
            if isinstance(pm2, str) and '€/m²' in pm2:
                try:
                    return int(pm2.replace('€/m²', '').strip())
                except:
                    return 999999
            return 999999

        sorted_listings = sorted(listings, key=get_price_m2)
        
        # 2. Limit to Top 5 to avoid long messages
        top_listings = sorted_listings[:5]

        message = f"🏠 *Imobiliário Bot: Top {len(top_listings)} Deals*\n\n"
        
        for i, item in enumerate(top_listings, 1):
            title = item.get('title', 'N/A')[:40]
            price = item.get('price', 'N/A')
            area = item.get('area', 'N/A')
            pm2 = item.get('price_m2', 'N/A')
            loc = item.get('location', 'N/A')
            link = item.get('link', '#')
            garage = "🚗 (Garagem)" if item.get('garage') == 'Sim' else ""
            transport = "🚆" if item.get('transport') == 'Comboio' else "🚇" if item.get('transport') == 'Metro' else "📍"

            message += f"*{i}. {title}*\n"
            message += f"💰 {price} ({pm2})\n"
            message += f"📐 {area} {garage}\n"
            message += f"{transport} {loc}\n"
            message += f"🔗 {link}\n\n"

        message += "_Boas pesquisas!_ 🏠🚀"

        # 3. Send using CallMeBot
        params = {
            "phone": WHATSAPP_NUMBER,
            "text": message,
            "apikey": WHATSAPP_API_KEY
        }

        try:
            # We use a GET request for CallMeBot
            response = requests.get(self.base_url, params=params, timeout=30)
            if response.status_code == 200:
                self.logger.info(f"WhatsApp message sent to {WHATSAPP_NUMBER}")
            else:
                self.logger.error(f"Failed to send WhatsApp: {response.text}")
        except Exception as e:
            self.logger.error(f"WhatsApp Error: {e}")
