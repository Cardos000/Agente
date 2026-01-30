"""
Scoring Agent - Explicável
Responsável por calcular score de oportunidade com breakdown detalhado.

Score máximo: 100 pontos
- Market Value: 0-50 (comparação com benchmark local)
- Features: 0-20 (garagem, varanda, terraço)
- Transport Confidence: 0-15 (confirmação de acesso)
- Regulatory Fit: 0-15 (confiança nos requisitos)
"""

import csv
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ScoringAgent:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Market benchmarks (€/m² - 2024/2025)
        self.MARKET_AVERAGES = {
            "Porto": 3500,
            "Matosinhos": 3200,
            "Maia": 2600,
            "Vila Nova de Gaia": 2600,
            "Gondomar": 1950,
            "Valongo": 1850,
            "Ermesinde": 2000,
            "Rio Tinto": 2100,
            "Penafiel": 1650,
            "Lousada": 1550,
            "Póvoa de Varzim": 2400,
            "Espinho": 2800
        }
    
    def score(self, item: Dict[str, Any], location_result: Dict[str, Any], 
              compatibility_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula score explicável para um imóvel.
        
        Returns:
            {
                "score": 0-100,
                "score_breakdown": {
                    "market_value": score,
                    "features": score,
                    "transport_confidence": score,
                    "regulatory_fit": score
                },
                "details": {
                    "price_m2": float,
                    "price_vs_benchmark": str,
                    "features_found": [str],
                    "transport_info": str,
                    "confidence_notes": [str]
                }
            }
        """
        
        breakdown = {
            "market_value": 0,
            "features": 0,
            "transport_confidence": 0,
            "regulatory_fit": 0
        }
        
        details = {
            "price_m2": None,
            "price_vs_benchmark": None,
            "features_found": [],
            "transport_info": None,
            "confidence_notes": []
        }
        
        # ==========================================
        # 1. MARKET VALUE (0-50 pts)
        # ==========================================
        price = item.get("price")
        area = item.get("area")
        
        if price is not None and area is not None and area > 30:
            price_m2 = price / area
            details["price_m2"] = price_m2
            
            # Determinar benchmark local
            location_text = (item.get("location", "") + " " + 
                           item.get("title", "") + " " + 
                           item.get("description", "")).lower()
            
            benchmark = 2800
            for city, val in self.MARKET_AVERAGES.items():
                if city.lower() in location_text:
                    benchmark = val
                    break
            
            # Calcular diferença
            pct_diff = (price_m2 - benchmark) / benchmark
            details["price_vs_benchmark"] = f"{pct_diff:+.1%} vs {benchmark}€/m²"
            
            # Scoring baseado em comparação
            if pct_diff < -0.25:
                breakdown["market_value"] = 50  # GOLD
            elif pct_diff < -0.15:
                breakdown["market_value"] = 40  # VERY GOOD
            elif pct_diff < -0.05:
                breakdown["market_value"] = 30  # GOOD
            elif pct_diff < 0.10:
                breakdown["market_value"] = 20  # FAIR
            elif pct_diff < 0.25:
                breakdown["market_value"] = 10  # ABOVE
            else:
                breakdown["market_value"] = 0   # WAY ABOVE
        else:
            details["confidence_notes"].append("Preço/Área não disponíveis para cálculo")
        
        # ==========================================
        # 2. FEATURES (0-20 pts)
        # ==========================================
        description = (item.get("description", "") + " " + item.get("title", "")).lower()
        
        # Garagem
        if any(word in description for word in ["garagem", "garage", "garaje", "parking"]):
            breakdown["features"] += 7
            details["features_found"].append("Garagem")
        
        # Varanda
        if any(word in description for word in ["varanda", "balcon", "balcony"]):
            breakdown["features"] += 5
            details["features_found"].append("Varanda")
        
        # Terraço
        if any(word in description for word in ["terraço", "terrase", "terrace", "pátio"]):
            breakdown["features"] += 8
            details["features_found"].append("Terraço")
        
        if not details["features_found"]:
            details["features_found"].append("Nenhum extra detectado")
        
        # ==========================================
        # 3. TRANSPORT CONFIDENCE (0-15 pts)
        # ==========================================
        transport_type = location_result.get("transport_type", "Unknown")
        station = location_result.get("station")
        location_confidence = location_result.get("confidence", "low")
        
        if transport_type == "Comboio" and station:
            breakdown["transport_confidence"] = 15
            details["transport_info"] = f"Comboio {station} - ALTA CONFIANÇA"
        elif transport_type == "Metro" and station:
            breakdown["transport_confidence"] = 12
            details["transport_info"] = f"Metro {station} - ALTA CONFIANÇA"
        elif location_confidence == "medium":
            breakdown["transport_confidence"] = 5
            details["transport_info"] = "Transporte incerto - marcar para revisão"
        else:
            breakdown["transport_confidence"] = 0
            details["transport_info"] = "Transporte não confirmado"
        
        # ==========================================
        # 4. REGULATORY FIT (0-15 pts)
        # ==========================================
        compatibility = compatibility_result.get("meets_requirements", {})
        
        confirmed_count = sum(1 for v in compatibility.values() if v is True)
        total_count = len(compatibility)
        
        if total_count > 0:
            fit_percentage = confirmed_count / total_count
            if fit_percentage == 1.0:
                breakdown["regulatory_fit"] = 15
                details["confidence_notes"].append("[OK] Todos os requisitos confirmados")
            elif fit_percentage >= 0.75:
                breakdown["regulatory_fit"] = 10
                details["confidence_notes"].append("[PARCIAL] Maioria dos requisitos confirmada")
            elif fit_percentage >= 0.5:
                breakdown["regulatory_fit"] = 5
                details["confidence_notes"].append("[PARCIAL] Alguns requisitos nao confirmados")
            else:
                breakdown["regulatory_fit"] = 0
                details["confidence_notes"].append("[REJEITADO] Varios requisitos nao atendem")
        
        # ==========================================
        # SCORE FINAL
        # ==========================================
        total_score = sum(breakdown.values())
        
        return {
            "score": total_score,
            "score_breakdown": breakdown,
            "details": details
        }
    
    def process_batch(self, items: list, location_results: list, 
                     compatibility_results: list) -> list:
        """Processa batch de itens com scores"""
        
        scored_items = []
        
        for item, loc_result, compat_result in zip(items, location_results, compatibility_results):
            score_result = self.score(item, loc_result, compat_result)
            
            item.update({
                "score": score_result["score"],
                "score_breakdown": score_result["score_breakdown"],
                "score_details": score_result["details"]
            })
            
            scored_items.append(item)
        
        # Ordenar por score
        scored_items.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return scored_items
