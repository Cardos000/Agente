"""
Orchestrador de scrapers - Coordena execução de múltiplos scrapers
"""

import logging
from typing import List, Dict
from datetime import datetime
import json

from .imovirtual import ImovirtualScraper
from .idealista import IdealistaScraper
from .olx import OlxScraper
from .casayes import CasaYesScraper
from .sapocasa import SapoCasaScraper
from .supercasa import SuperCasaScraper
from .base import RawListing


class ScraperOrchestrator:
    """Coordena execução de todos os scrapers"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.scrapers = [
            ("Imovirtual", ImovirtualScraper()),
            ("Idealista", IdealistaScraper()),
            ("OLX", OlxScraper()),
            ("CasaYes", CasaYesScraper()),
            ("SAPO Casa", SapoCasaScraper()),
            ("SuperCasa", SuperCasaScraper()),
        ]
        self.results = {
            "total_listings": 0,
            "scrapers": {},
            "started_at": None,
            "ended_at": None,
            "duration_seconds": 0
        }

    def _setup_logger(self) -> logging.Logger:
        """Configurar logger"""
        logger = logging.getLogger("ScraperOrchestrator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[ORCHESTRATOR] %(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def run(self, headless=True, scrapers_to_run: List[str] = None) -> Dict:
        """
        Executar todos os scrapers (ou apenas os especificados)
        
        Args:
            headless: Se True, executa em background
            scrapers_to_run: Lista de nomes de scrapers para executar.
                           Se None, executa todos.
        
        Returns:
            Dict com resultados e estatísticas
        """
        self.results["started_at"] = datetime.now().isoformat()
        
        self.logger.info("=" * 80)
        self.logger.info("INICIANDO ORCHESTRADOR DE SCRAPERS")
        self.logger.info("=" * 80)
        
        if scrapers_to_run:
            self.logger.info(f"Scrapers selecionados: {scrapers_to_run}")
        else:
            self.logger.info(f"Executando todos os {len(self.scrapers)} scrapers")
        
        all_listings = []
        
        for name, scraper in self.scrapers:
            # Pular se não foi selecionado
            if scrapers_to_run and name not in scrapers_to_run:
                self.logger.info(f"[SKIP] Pulando {name}")
                continue
            
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"[SCRAPING] Iniciando scraper: {name}")
            self.logger.info(f"{'='*80}")
            
            try:
                # Executar scraper
                scraper.headless = headless
                listings = scraper.scrape()
                
                # Registrar resultados
                self.results["scrapers"][name] = {
                    "status": "success",
                    "listings_found": len(listings),
                    "pages_fetched": scraper.stats.get("pages_fetched", 0),
                    "errors": scraper.stats.get("errors", 0)
                }
                
                all_listings.extend(listings)
                
                self.logger.info(f"[OK] {name}: {len(listings)} listings extraidos")
                self.logger.info(f"   Páginas: {scraper.stats.get('pages_fetched', 0)}")
                self.logger.info(f"   Erros: {scraper.stats.get('errors', 0)}")
                
            except Exception as e:
                self.logger.error(f"[ERRO] {name} falhou: {e}", exc_info=True)
                self.results["scrapers"][name] = {
                    "status": "failed",
                    "error": str(e),
                    "listings_found": 0
                }
        
        # Consolidar resultados
        self.results["ended_at"] = datetime.now().isoformat()
        self.results["total_listings"] = len(all_listings)
        
        # Calcular duração
        try:
            started = datetime.fromisoformat(self.results["started_at"])
            ended = datetime.fromisoformat(self.results["ended_at"])
            self.results["duration_seconds"] = (ended - started).total_seconds()
        except:
            pass
        
        # Log final
        self.logger.info(f"\n{'='*80}")
        self.logger.info("RESUMO FINAL")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Total de listings extraídos: {self.results['total_listings']}")
        self.logger.info(f"Tempo total: {self.results['duration_seconds']:.2f}s")
        self.logger.info(f"Scrapers OK: {sum(1 for s in self.results['scrapers'].values() if s['status'] == 'success')}")
        self.logger.info(f"Scrapers FALHADOS: {sum(1 for s in self.results['scrapers'].values() if s['status'] == 'failed')}")
        self.logger.info(f"{'='*80}\n")
        
        return all_listings, self.results

    def save_raw_listings(self, listings: List[RawListing], filepath: str = "raw_listings.json"):
        """Salvar listings brutos em JSON para debug/análise"""
        try:
            data = [listing.to_dict() for listing in listings]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"[OK] {len(listings)} listings salvos em {filepath}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar listings: {e}")
