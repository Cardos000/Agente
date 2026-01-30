"""
Profile Compatibility Agent
Responsável por validar compatibilidade com perfil do utilizador.

Regra crítica: Só eliminar automaticamente se CONFIRMADO.
Se não confirmado → marcar para revisão manual.
"""

import logging
from typing import Dict, Any, List
from config import MIN_TYPOLOGY, MIN_AREA, MIN_PRICE, MAX_PRICE, AMP_COUNCILS

logger = logging.getLogger(__name__)


class ProfileCompatibilityAgent:
    """Valida compatibilidade com perfil imobiliário"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.min_typology = MIN_TYPOLOGY
        self.min_area = MIN_AREA
        self.min_price = MIN_PRICE
        self.max_price = MAX_PRICE
        self.amp_councils = set(c.lower() for c in AMP_COUNCILS)
    
    def validate(self, item: Dict[str, Any], location_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida compatibilidade do anúncio com perfil.
        
        Returns:
            {
                "matches_profile": bool,
                "meets_requirements": Dict[requirement -> bool],
                "confidence_score": float (0-1),
                "reasons": [str],
                "concerns": [str],
                "recommendation": "approved" | "needs_review" | "rejected"
            }
        """
        
        result = {
            "matches_profile": True,
            "meets_requirements": {},
            "confidence_score": 1.0,
            "reasons": [],
            "concerns": [],
            "recommendation": "approved"
        }
        
        # ==========================================
        # 1. VALIDAÇÃO: TIPOLOGIA
        # ==========================================
        typology = item.get("typology")
        typology_confidence = item.get("typology_confidence", "low")
        
        if typology is None:
            result["meets_requirements"]["tipologia"] = None
            result["concerns"].append("Tipologia não extraída")
            result["recommendation"] = "needs_review"
        else:
            # Extrair número da tipologia
            try:
                typology_num = int(typology.replace("T", ""))
                min_typology_num = int(self.min_typology.replace("T", ""))
                
                if typology_num >= min_typology_num:
                    result["meets_requirements"]["tipologia"] = True
                    result["reasons"].append(f"Tipologia {typology} ≥ {self.min_typology}")
                else:
                    result["meets_requirements"]["tipologia"] = False
                    result["matches_profile"] = False
                    result["reasons"].append(f"Tipologia {typology} < {self.min_typology}")
                    
                    if typology_confidence == "high":
                        result["recommendation"] = "rejected"
                    else:
                        result["recommendation"] = "needs_review"
                        result["concerns"].append("Tipologia abaixo do mínimo mas confiança baixa")
            
            except Exception as e:
                self.logger.warning(f"Erro ao validar tipologia {typology}: {e}")
                result["meets_requirements"]["tipologia"] = None
                result["concerns"].append("Tipologia mal formatada")
                result["recommendation"] = "needs_review"
        
        # ==========================================
        # 2. VALIDAÇÃO: ÁREA
        # ==========================================
        area = item.get("area")
        area_confidence = item.get("area_confidence", "low")
        
        if area is None:
            result["meets_requirements"]["área"] = None
            result["concerns"].append("Área não extraída")
            result["recommendation"] = "needs_review"
        else:
            if area >= self.min_area:
                result["meets_requirements"]["área"] = True
                result["reasons"].append(f"Área {area} m² ≥ {self.min_area} m²")
            else:
                result["meets_requirements"]["área"] = False
                result["matches_profile"] = False
                result["reasons"].append(f"Área {area} m² < {self.min_area} m²")
                
                if area_confidence == "high":
                    result["recommendation"] = "rejected"
                else:
                    result["recommendation"] = "needs_review"
                    result["concerns"].append("Área abaixo do mínimo mas confiança baixa")
        
        # ==========================================
        # 3. VALIDAÇÃO: PREÇO
        # ==========================================
        price = item.get("price")
        price_confidence = item.get("price_confidence", "low")
        
        if price is None:
            result["meets_requirements"]["preço"] = None
            result["concerns"].append("Preço não extraído")
            result["recommendation"] = "needs_review"
        else:
            if self.min_price <= price <= self.max_price:
                result["meets_requirements"]["preço"] = True
                result["reasons"].append(f"Preço {price}€ dentro do range [{self.min_price}-{self.max_price}]")
            else:
                result["meets_requirements"]["preço"] = False
                result["matches_profile"] = False
                
                if price < self.min_price:
                    result["reasons"].append(f"Preço {price}€ < mínimo {self.min_price}€")
                else:
                    result["reasons"].append(f"Preço {price}€ > máximo {self.max_price}€")
                
                if price_confidence == "high":
                    result["recommendation"] = "rejected"
                else:
                    result["recommendation"] = "needs_review"
                    result["concerns"].append("Preço fora do range mas confiança baixa")
        
        # ==========================================
        # 4. VALIDAÇÃO: LOCALIZAÇÃO (AMP)
        # ==========================================
        council = location_result.get("council")
        location_confidence = location_result.get("confidence", "low")
        
        if council is None:
            result["meets_requirements"]["localização_amp"] = None
            result["concerns"].append("Localização não confirmada")
            result["recommendation"] = "needs_review"
        else:
            if council.lower() in self.amp_councils:
                result["meets_requirements"]["localização_amp"] = True
                result["reasons"].append(f"Localização em {council} (AMP)")
            else:
                result["meets_requirements"]["localização_amp"] = False
                result["matches_profile"] = False
                result["reasons"].append(f"{council} fora da Área Metropolitana do Porto")
                
                if location_confidence == "high":
                    result["recommendation"] = "rejected"
                else:
                    result["recommendation"] = "needs_review"
                    result["concerns"].append("Localização fora AMP mas confiança baixa")
        
        # ==========================================
        # 5. VALIDAÇÃO: TRANSPORTE
        # ==========================================
        transport_validation = self._validate_transport(location_result)
        result["meets_requirements"]["transporte"] = transport_validation["meets_requirement"]
        result["reasons"].append(transport_validation["reason"])
        
        if not transport_validation["meets_requirement"]:
            if location_confidence == "high":
                result["recommendation"] = "rejected"
                result["matches_profile"] = False
            else:
                result["recommendation"] = "needs_review"
                result["concerns"].append("Transporte não confirmado - marcar para revisão")
        
        # ==========================================
        # 6. CALCULAR CONFIDENCE SCORE
        # ==========================================
        confirmed_requirements = sum(
            1 for v in result["meets_requirements"].values() 
            if v is True
        )
        total_requirements = len(result["meets_requirements"])
        
        if total_requirements > 0:
            result["confidence_score"] = confirmed_requirements / total_requirements
        
        # ==========================================
        # 7. DECISÃO FINAL
        # ==========================================
        if result["recommendation"] == "approved":
            if not result["matches_profile"]:
                # Se não faz match mas temos certeza → rejected
                if all(v is not None for v in result["meets_requirements"].values()):
                    result["recommendation"] = "rejected"
                else:
                    result["recommendation"] = "needs_review"
        
        return result
    
    def _validate_transport(self, location_result: Dict[str, Any]) -> Dict[str, Any]:
        """Valida requisito de transporte"""
        transport_type = location_result.get("transport_type", "Unknown")
        station = location_result.get("station")
        confidence = location_result.get("confidence", "low")
        
        if transport_type != "Unknown" and station:
            return {
                "meets_requirement": True,
                "reason": f"Acesso confirmado a {station} ({transport_type})"
            }
        else:
            return {
                "meets_requirement": False,
                "reason": f"Transporte não confirmado (confidence: {confidence})"
            }
