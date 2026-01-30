"""
Script para testar scraping apenas do OLX e guardar resultado em olx_raw.json
"""
from scraper.orchestrator import ScraperOrchestrator

if __name__ == "__main__":
    orchestrator = ScraperOrchestrator()
    listings, stats = orchestrator.run(headless=True, scrapers_to_run=["OLX"])
    orchestrator.save_raw_listings(listings, filepath="olx_raw.json")
    print(f"Extraídos {len(listings)} anúncios do OLX. Estatísticas:")
    print(stats["scrapers"].get("OLX", {}))
    print("Primeiro anúncio:")
    if listings:
        print(listings[0].to_dict())
    else:
        print("Nenhum anúncio extraído.")
