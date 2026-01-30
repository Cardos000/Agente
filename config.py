import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# PERFIL IMOBILIÁRIO (IMUTÁVEL)
# ==========================================
# Tipologia
MIN_TYPOLOGY = "T2"
MIN_AREA = 90  # m²

# Preço (€)
MIN_PRICE = 60000
MAX_PRICE = 250000

# Localização - Área Metropolitana do Porto (AMP)
AMP_COUNCILS = [
    "Porto", "Matosinhos", "Maia", "Gondomar", "Valongo", 
    "Ermesinde", "Rio Tinto", "Penafiel", "Lousada", 
    "Vila Nova de Gaia", "Espinho", "Póvoa de Varzim"
]

# Transporte - Requisitos de acesso (CRÍTICO)
# Comboio: Campanhã ou equivalente
# Metro: Estações da Linha A, B, C, D, E, F
COMBOIO_STATIONS = ["Campanhã", "Porto"]
METRO_STATIONS = [
    # Linha A (Médio Tejo - Senhor de Matosinhos)
    "Senhor de Matosinhos", "Matosinhos Sul", "Matosinhos", "Moreira", "Maia", "Madalena",
    # Linha B (Estadio - Hospital de São João)
    "Estádio do Dragão", "Pólo Universitário", "Hospital de São João",
    # Linha C (Luchadores - Hospital de São João)
    "Campanhã", "Bolhão", "Trindade", "Aliados", "Pessoa",
    # Linha D (Santo Ovídio - Pólo Universitário)
    "Santo Ovídio", "General Torres", "Devesas", "Vilanova", 
    # Linha E (Vilarinha - Maia)
    "Vilarinha", "Dragão", "Maia",
    # Linha F (Vilar do Conde - Santo Ovídio)
    "Vilar do Conde"
]

# Nice-to-have (nunca filtram, apenas influenciam score)
NICE_TO_HAVE = {
    "garagem": 5,      # +5 pontos
    "varanda": 3,      # +3 pontos
    "terraço": 4       # +4 pontos
}

# ==========================================
# SCRAPER SETTINGS
# ==========================================
HEADLESS = True
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ==========================================
# OUTPUT SETTINGS
# ==========================================
SEEN_LISTINGS_FILE = "seen_listings.json"
OUTPUT_DIR = "output"
TOP_OPPORTUNITIES_FILE = "top_opportunities.md"
NEEDS_REVIEW_FILE = "needs_review.md"
REJECTED_LOG_FILE = "rejected.log"
ALL_SCORED_CSV = "all_scored.csv"

# ==========================================
# EMAIL NOTIFIER
# ==========================================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# ==========================================
# WHATSAPP NOTIFIER
# ==========================================
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")

# ==========================================
# EXECUTION MODES
# ==========================================
EXECUTION_MODE = "new"  # "new" | "window" (últimos X dias)
DAYS_WINDOW = 7  # Usado quando EXECUTION_MODE = "window"
