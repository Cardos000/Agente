"""
Pipeline Orchestrator
Coordena o fluxo multi-agente com logging anti-overfiltering obrigatório.

Fluxo:
1. Normalization: Limpar dados brutos
2. Location Verification: Resolver localização + transporte
3. Profile Compatibility: Validar contra perfil
4. Scoring: Calcular score explicável
5. Output: Gerar relatórios (top, needs_review, rejected)
"""

import logging
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
from analysis.normalization import NormalizationAgent
from analysis.location_verification import LocationVerificationAgent
from analysis.profile_compatibility import ProfileCompatibilityAgent
from analysis.ranker import ScoringAgent
from analysis.deduplication import deduplicate_announcements

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orquestra análise multi-agente com logging detalhado"""
    
    def __init__(self):
        self.normalization_agent = NormalizationAgent()
        self.location_agent = LocationVerificationAgent()
        self.compatibility_agent = ProfileCompatibilityAgent()
        self.scoring_agent = ScoringAgent()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Estatísticas
        self.stats = {
            "total_processed": 0,
            "approved": [],
            "needs_review": [],
            "rejected": [],
            "error_count": 0
        }
    
    def process(self, raw_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processa batch de anúncios através de todos os agentes.
        
        Returns:
            {
                "approved": [...],
                "needs_review": [...],
                "rejected": [...],
                "stats": {...}
            }
        """
        
        self.logger.info(f"[PIPELINE] Iniciando pipeline para {len(raw_items)} anuncios")
        
        normalized_items = []
        location_results = []
        compatibility_results = []
        final_items = []
        
        # ==========================================
        # STAGE 1: NORMALIZATION
        # ==========================================
        self.logger.info("[STAGE 1] Normalizando dados brutos...")
        
        for item in raw_items:
            try:
                normalized = self.normalization_agent.normalize(item)
                normalized_items.append(normalized)
            except Exception as e:
                item_title = item.title if hasattr(item, 'title') else item.get('title', 'Desconhecido')
                self.logger.error(f"Erro ao normalizar {item_title}: {e}")
                self.stats["error_count"] += 1
        
        norm_summary = self.normalization_agent.get_normalization_summary(normalized_items)
        self.logger.info(f"  [OK] {len(normalized_items)}/{len(raw_items)} normalizados")
        self.logger.info(f"    - Taxa extracao preco: {norm_summary['price_extraction_rate']:.1%}")
        self.logger.info(f"    - Taxa extração área: {norm_summary['area_extraction_rate']:.1%}")
        self.logger.info(f"    - Taxa extração localização: {norm_summary['location_extraction_rate']:.1%}")
        
        # ==========================================
        # DEDUPLICAÇÃO CONSERVADORA (agrupamento)
        # ==========================================
        self.logger.info("[DEDUPLICACAO] Agrupando anúncios semelhantes...")
        unique_items, duplicate_groups = deduplicate_announcements(normalized_items)
        self.logger.info(f"  [OK] {len(unique_items)} anúncios únicos após deduplicação (de {len(normalized_items)})")
        

        # Salvar grupos de duplicados para revisão manual (converter RawListing para dict)
        def listing_to_dict(x):
            if hasattr(x, 'to_dict'):
                return x.to_dict()
            elif isinstance(x, dict):
                return x
            elif hasattr(x, '__dict__'):
                return dict(x.__dict__)
            return str(x)

        serializable_groups = []
        for group in duplicate_groups:
            serializable_group = [listing_to_dict(item) for item in group]
            serializable_groups.append(serializable_group)
        with open('debug_duplicate_groups.json', 'w', encoding='utf-8') as f:
            json.dump(serializable_groups, f, ensure_ascii=False, indent=2)

        # Usar unique_items no pipeline a partir daqui
        normalized_items = unique_items
        
        # ==========================================
        # STAGE 2: LOCATION VERIFICATION
        # ==========================================
        self.logger.info("[STAGE 2] Verificando localizacao e transporte...")
        
        for item in normalized_items:
            try:
                location_result = self.location_agent.verify(item)
                location_results.append(location_result)
                
                # Extrair distance hints para alertas
                distance_hints = self.location_agent.extract_distance_hints(
                    item.get("description", "") + " " + item.get("title", "")
                )
                if distance_hints:
                    location_result["distance_hints"] = distance_hints
                
            except Exception as e:
                self.logger.error(f"Erro ao verificar localização {item.get('title')}: {e}")
                location_results.append({
                    "location_text": item.get("location"),
                    "council": None,
                    "transport_type": "Unknown",
                    "station": None,
                    "confidence": "low",
                    "method": None,
                    "explanation": f"ERRO: {str(e)}"
                })
                self.stats["error_count"] += 1
        
        transport_summary = self._analyze_transport_distribution(location_results)
        self.logger.info(f"  [OK] {len(location_results)} localizacoes verificadas")
        self.logger.info(f"    - Metro: {transport_summary['metro']}")
        self.logger.info(f"    - Comboio: {transport_summary['comboio']}")
        self.logger.info(f"    - Incertos: {transport_summary['incertos']}")
        
        # ==========================================
        # STAGE 3: PROFILE COMPATIBILITY
        # ==========================================
        self.logger.info("[STAGE 3] Validando perfil...")
        
        for item, location_result in zip(normalized_items, location_results):
            try:
                compatibility_result = self.compatibility_agent.validate(item, location_result)
                compatibility_results.append(compatibility_result)
            except Exception as e:
                self.logger.error(f"Erro ao validar perfil {item.get('title')}: {e}")
                compatibility_results.append({
                    "matches_profile": False,
                    "meets_requirements": {},
                    "confidence_score": 0,
                    "reasons": [f"ERRO: {str(e)}"],
                    "concerns": [],
                    "recommendation": "needs_review"
                })
                self.stats["error_count"] += 1
        
        # Contar recomendações
        approved_count = sum(1 for c in compatibility_results if c["recommendation"] == "approved")
        review_count = sum(1 for c in compatibility_results if c["recommendation"] == "needs_review")
        rejected_count = sum(1 for c in compatibility_results if c["recommendation"] == "rejected")
        
        self.logger.info(f"  [OK] Perfil validado")
        self.logger.info(f"    - [OK] Aprovados (pre-score): {approved_count}")
        self.logger.info(f"    - [REVISAO] Para revisao: {review_count}")
        self.logger.info(f"    - [REJEITADO] Rejeitados: {rejected_count}")
        
        # ==========================================
        # STAGE 4: SCORING
        # ==========================================
        self.logger.info("[STAGE 4] Calculando scores...")
        
        scored_items = self.scoring_agent.process_batch(
            normalized_items, location_results, compatibility_results
        )
        
        # Agregar informações
        for i, (item, compatibility, location) in enumerate(
            zip(scored_items, compatibility_results, location_results)
        ):
            item["compatibility_result"] = compatibility
            item["location_result"] = location
        
        self.logger.info(f"  [OK] Scores calculados")
        
        # ==========================================
        # STAGE 5: CATEGORIZACAO FINAL
        # ==========================================
        self.logger.info("[STAGE 5] Categorizando resultados...")
        
        for item in scored_items:
            recommendation = item["compatibility_result"]["recommendation"]
            
            if recommendation == "approved" and item["score"] >= 40:
                # Apenas e "approved" se score > 40
                self.stats["approved"].append(item)
                item["final_status"] = "approved"
            elif recommendation == "needs_review" or item["score"] < 40:
                self.stats["needs_review"].append(item)
                item["final_status"] = "needs_review"
            else:
                self.stats["rejected"].append(item)
                item["final_status"] = "rejected"
        
        self.stats["total_processed"] = len(scored_items)
        
        self.logger.info(f"  [OK] Categorizacao concluida")
        self.logger.info(f"    - [OK] Boas oportunidades: {len(self.stats['approved'])}")
        self.logger.info(f"    - [INCERTOS] Para revisao: {len(self.stats['needs_review'])}")
        self.logger.info(f"    - [REJEITADO] Rejeitados: {len(self.stats['rejected'])}")
        self.logger.info(f"    - [ERROS] Erros: {self.stats['error_count']}")
        
        # ==========================================
        # REGRA FINAL ANTI-OVERFILTERING
        # ==========================================
        self.logger.info("[VALIDACAO] VALIDACAO ANTI-OVERFILTERING...")
        
        if len(self.stats["approved"]) == 0 and len(self.stats["needs_review"]) == 0:
            self.logger.warning("[AVISO] Pipeline resultou em 0 aprovados e 0 para revisao!")
            self.logger.warning("    Isto pode indicar filtros muito restritivos.")
            self.logger.warning("    Recomendação: Revisar critérios de compatibilidade.")
        
        if self.stats["error_count"] > len(raw_items) * 0.1:
            self.logger.warning(f"[AVISO] {self.stats['error_count']} erros (>{10*len(raw_items)}%)")
        
        return {
            "approved": self.stats["approved"],
            "needs_review": self.stats["needs_review"],
            "rejected": self.stats["rejected"],
            "stats": {
                "total_processed": self.stats["total_processed"],
                "approved_count": len(self.stats["approved"]),
                "needs_review_count": len(self.stats["needs_review"]),
                "rejected_count": len(self.stats["rejected"]),
                "error_count": self.stats["error_count"],
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _analyze_transport_distribution(self, location_results: List[Dict]) -> Dict[str, int]:
        """Analisa distribuição de tipos de transporte"""
        metro = sum(1 for r in location_results if r.get("transport_type") == "Metro")
        comboio = sum(1 for r in location_results if r.get("transport_type") == "Comboio")
        incertos = sum(1 for r in location_results if r.get("transport_type") == "Unknown")
        
        return {
            "metro": metro,
            "comboio": comboio,
            "incertos": incertos
        }
