#!/usr/bin/env python
"""
Test script para scrapers
Executa independentemente dos scrapers para validação
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_single_scraper(scraper_name: str, headless: bool = True):
    """Testar um scraper específico"""
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTE: {scraper_name}")
    logger.info(f"{'='*80}\n")
    
    try:
        if scraper_name.lower() == "imovirtual":
            from scraper.imovirtual import ImovirtualScraper
            scraper = ImovirtualScraper(headless=headless)
        elif scraper_name.lower() == "idealista":
            from scraper.idealista import IdealistaScraper
            scraper = IdealistaScraper(headless=headless)
        elif scraper_name.lower() == "olx":
            from scraper.olx import OlxScraper
            scraper = OlxScraper(headless=headless)
        elif scraper_name.lower() == "casayes":
            from scraper.casayes import CasaYesScraper
            scraper = CasaYesScraper(headless=headless)
        elif scraper_name.lower() == "sapo" or scraper_name.lower() == "sapocasa":
            from scraper.sapocasa import SapoCasaScraper
            scraper = SapoCasaScraper(headless=headless)
        elif scraper_name.lower() == "supercasa":
            from scraper.supercasa import SuperCasaScraper
            scraper = SuperCasaScraper(headless=headless)
        else:
            logger.error(f"Scraper '{scraper_name}' não encontrado")
            return False
        
        # Executar
        listings = scraper.scrape()
        
        # Validar
        logger.info(f"\n{'='*80}")
        logger.info("RESULTADOS")
        logger.info(f"{'='*80}")
        logger.info(f"[OK] Scraper executado com sucesso")
        logger.info(f"   Listings extraídos: {len(listings)}")
        logger.info(f"   Pages fetched: {scraper.stats.get('pages_fetched', 0)}")
        logger.info(f"   Errors: {scraper.stats.get('errors', 0)}")
        
        # Mostrar sample
        if listings:
            logger.info(f"\n{'='*80}")
            logger.info("SAMPLE (primeiro listing):")
            logger.info(f"{'='*80}")
            sample = listings[0].to_dict()
            for key, value in sample.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("[AVISO] Nenhum listing foi extraido!")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERRO] Teste falhou: {e}", exc_info=True)
        return False


def test_orchestrator(headless: bool = True, scrapers: list = None):
    """Testar orchestrador de scrapers"""
    logger.info(f"\n{'='*80}")
    logger.info("TESTE: ORCHESTRADOR")
    logger.info(f"{'='*80}\n")
    
    try:
        from scraper.orchestrator import ScraperOrchestrator
        
        orchestrator = ScraperOrchestrator()
        all_listings, results = orchestrator.run(
            headless=headless,
            scrapers_to_run=scrapers
        )
        
        # Salvar resultados brutos
        orchestrator.save_raw_listings(all_listings, "raw_listings.json")
        
        logger.info(f"\n{'='*80}")
        logger.info("TESTE ORCHESTRADOR: SUCESSO")
        logger.info(f"{'='*80}")
        logger.info(f"Total de listings: {len(all_listings)}")
        logger.info(f"Tempo: {results['duration_seconds']:.2f}s")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERRO] Teste de orchestrador falhou: {e}", exc_info=True)
        return False


def main():
    """Main"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste de scrapers")
    parser.add_argument(
        "--scraper",
        help="Testar scraper específico (imovirtual, idealista, olx, casayes, sapo, supercasa)",
        type=str
    )
    parser.add_argument(
        "--headless",
        help="Executar em headless mode (sem interface)",
        action="store_true",
        default=True
    )
    parser.add_argument(
        "--no-headless",
        help="Executar COM interface (debug)",
        action="store_true"
    )
    parser.add_argument(
        "--all",
        help="Testar todos os scrapers via orchestrador",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    headless = not args.no_headless
    
    if args.scraper:
        # Teste único
        success = test_single_scraper(args.scraper, headless=headless)
        sys.exit(0 if success else 1)
    
    elif args.all:
        # Teste orchestrador
        success = test_orchestrator(headless=headless)
        sys.exit(0 if success else 1)
    
    else:
        # Mostrar ajuda
        parser.print_help()
        print("\nExemplos:")
        print("  python test_scrapers.py --scraper imovirtual")
        print("  python test_scrapers.py --scraper idealista --no-headless")
        print("  python test_scrapers.py --all")


if __name__ == "__main__":
    main()
