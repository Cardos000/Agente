"""
REAL ESTATE BOT - MAIN ORCHESTRATOR
Arquitetura Multi-Agente com Anti-Overfiltering

Fluxo:
1. Scraper → Anúncios brutos
2. Normalization Agent → Limpeza e confiança
3. Location Verification Agent → Localização + Transporte
4. Profile Compatibility Agent → Validação de perfil
5. Scoring Agent → Cálculo de score
6. Output Generator → Relatórios C3
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from config import (
    SEEN_LISTINGS_FILE, EXECUTION_MODE, DAYS_WINDOW,
    MIN_PRICE, MAX_PRICE, MIN_AREA, MIN_TYPOLOGY
)
from scraper.orchestrator import ScraperOrchestrator
from analysis.pipeline import PipelineOrchestrator
from analysis.output import OutputGenerator

# ==========================================
# LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RealEstateBot")


class RealEstateBotMain:
    """Orquestrador principal do sistema"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pipeline = PipelineOrchestrator()
        self.output_gen = OutputGenerator()
        self.seen_listings = self._load_seen_listings()
    
    def _load_seen_listings(self) -> Dict[str, str]:
        """Carrega histórico de anúncios vistos"""
        if os.path.exists(SEEN_LISTINGS_FILE):
            try:
                with open(SEEN_LISTINGS_FILE, "r") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception as e:
                self.logger.warning(f"Erro ao carregar seen_listings: {e}")
                return {}
        return {}
    
    def _save_seen_listings(self):
        """Guarda histórico de anúncios vistos"""
        with open(SEEN_LISTINGS_FILE, "w") as f:
            json.dump(self.seen_listings, f, indent=2, ensure_ascii=False)
    
    def _should_process_item(self, item: Dict[str, Any], date_str: str) -> bool:
        """
        Determina se item deve ser processado baseado no modo de execução.
        
        Modos:
        - "new": Apenas novos (não em seen_listings)
        - "window": Últimos X dias
        """
        
        link = item.link if hasattr(item, 'link') else item.get("link", "")
        
        # Se já foi visto, não processar
        if link in self.seen_listings:
            return False
        
        # Modo "new" - processar tudo que é novo
        if EXECUTION_MODE == "new":
            return True
        
        # Modo "window" - verificar data
        if EXECUTION_MODE == "window":
            try:
                item_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                cutoff_date = datetime.now() - timedelta(days=DAYS_WINDOW)
                return item_date > cutoff_date
            except Exception as e:
                self.logger.warning(f"Erro ao parsing data {date_str}: {e}")
                return True  # Em dúvida, processar
        
        return True
    
    def _filter_raw_listings(self, raw_listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtra listing brutos por modo de execução"""
        
        filtered = []
        
        for item in raw_listings:
            # Suporta tanto RawListing objects como dicts
            link = item.link if hasattr(item, 'link') else item.get("link", "")
            date = item.published_date if hasattr(item, 'published_date') else item.get("date", "")
            
            # Validação básica
            if not link:
                self.logger.debug("Item sem link, ignorando")
                continue
            
            # Aplicar modo de execução
            if not self._should_process_item(item, date):
                self.logger.debug(f"Item {link} já visto, ignorando")
                continue
            
            filtered.append(item)
        
        return filtered
    
    def run(self):
        """Executa pipeline completo"""
        
        self.logger.info("=" * 60)
        self.logger.info("[BOT] REAL ESTATE BOT - INICIANDO PIPELINE")
        self.logger.info(f"   Modo: {EXECUTION_MODE}")
        self.logger.info("=" * 60)
        
        # ==========================================
        # FASE 1: SCRAPING
        # ==========================================
        self.logger.info("\n[FASE 1] SCRAPING DE PORTAIS")
        
        try:
            orchestrator = ScraperOrchestrator()
            raw_listings, scraper_stats = orchestrator.run(headless=True)
            self.logger.info(f"[OK] Scraping concluido: {len(raw_listings)} anuncios coletados")
        except KeyboardInterrupt:
            self.logger.warning("Scraping interrompido pelo utilizador")
            raw_listings = []
        except Exception as e:
            self.logger.error(f"Erro de scraping: {e}")
            raw_listings = []
        
        if not raw_listings:
            self.logger.warning("[AVISO] Nenhum dado coletado. Abortando.")
            return
        
        # ==========================================
        # FASE 2: FILTRAGEM POR MODO
        # ==========================================
        self.logger.info(f"\n[FASE 2] FILTRAGEM POR MODO ({EXECUTION_MODE})")
        
        filtered_listings = self._filter_raw_listings(raw_listings)
        self.logger.info(f"[OK] {len(filtered_listings)}/{len(raw_listings)} anuncios a processar")
        
        if not filtered_listings:
            self.logger.info("[INFO] Nenhum anuncio novo para processar")
            return
        
        # ==========================================
        # FASE 3: PIPELINE MULTI-AGENTE
        # ==========================================
        self.logger.info("\n[FASE 3] PIPELINE MULTI-AGENTE")
        
        pipeline_result = self.pipeline.process(filtered_listings)
        
        # ==========================================
        # FASE 4: GERAÇÃO DE OUTPUTS (C3)
        # ==========================================
        self.logger.info("\n[FASE 4] GERAÇÃO DE OUTPUTS (C3)")
        
        output_files = self.output_gen.generate_all(pipeline_result)
        
        for output_type, filepath in output_files.items():
            self.logger.info(f"[OK] Gerado: {filepath}")
        
        # ==========================================
        # FASE 5: ATUALIZAR HISTÓRICO
        # ==========================================
        self.logger.info("\n[FASE 5] ATUALIZAR HISTÓRICO")
        
        all_processed = (
            pipeline_result["approved"] +
            pipeline_result["needs_review"] +
            pipeline_result["rejected"]
        )
        
        for item in all_processed:
            link = item.get("link")
            if link:
                self.seen_listings[link] = {
                    "status": item.get("final_status", "unknown"),
                    "score": item.get("score", 0),
                    "date_processed": datetime.now().isoformat(),
                    "title": item.get("title", "")
                }
        
        self._save_seen_listings()
        self.logger.info(f"[OK] Historico atualizado ({len(self.seen_listings)} total)")
        
        # ==========================================
        # RESUMO FINAL
        # ==========================================
        stats = pipeline_result["stats"]
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("[RESUMO] FINAL")
        self.logger.info("=" * 60)
        self.logger.info(f"Total processado: {stats['total_processed']}")
        self.logger.info(f"[APROVADO] {stats['approved_count']}")
        self.logger.info(f"[REVISAO] {stats['needs_review_count']}")
        self.logger.info(f"[REJEITADO] {stats['rejected_count']}")
        self.logger.info(f"[ERROS] {stats['error_count']}")
        self.logger.info("=" * 60)
        
        # ==========================================
        # PRÓXIMOS PASSOS
        # ==========================================
        self.logger.info("\n[PROXIMOS] PASSOS:")
        self.logger.info(f"1. Consulte {output_files['top_opportunities']}")
        
        if stats['needs_review_count'] > 0:
            self.logger.info(f"2. Revise {output_files['needs_review']}")
        
        self.logger.info(f"3. Analise {output_files['all_scored_csv']}")
        
        # ==========================================
        # NOTIFICAÇÕES
        # ==========================================
        if stats['approved_count'] > 0:
            self.logger.info("\n[NOTIFICACAO] ENVIANDO...")
            self._send_notifications(pipeline_result["approved"])
        
        self.logger.info("\n[SUCESSO] PIPELINE CONCLUIDO")
    
    def _send_notifications(self, approved_items: List[Dict]):
        """Envia notificacoes de oportunidades"""
        
        if len(approved_items) == 0:
            return
        
        try:
            from notifier.whatsapp_notifier import WhatsAppNotifier
            messenger = WhatsAppNotifier()
            
            for item in approved_items[:5]:  # Top 5
                try:
                    messenger.send_opportunity(item)
                    self.logger.debug(f"Notificação enviada para {item.get('title')}")
                except Exception as e:
                    self.logger.warning(f"Erro ao notificar {item.get('title')}: {e}")
        
        except ImportError:
            self.logger.info("[INFO] Modulo WhatsApp nao disponivel, notificacoes desativadas")
        except Exception as e:
            self.logger.warning(f"Erro ao enviar notificações: {e}")


def main():
    """Entry point"""
    bot = RealEstateBotMain()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.warning("\n[INTERRUPÇÃO] Bot interrompido pelo utilizador")
    except Exception as e:
        logger.error(f"Erro crítico: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
