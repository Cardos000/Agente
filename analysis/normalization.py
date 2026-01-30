"""
Normalization Agent
Responsável por limpar e normalizar dados brutos do scraper com detecção de confiança.

Regras:
- Regex defensiva: se falhar → field = None (nunca crashar)
- Detectar erros comuns (preço < área → swap provável)
- Marcar confiança em cada campo: high | medium | low
"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NormalizationAgent:
    """Normaliza e limpa dados brutos do scraper"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def normalize(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um anúncio bruto e retorna dados normalizados com confiança.
        
        Args:
            raw_item: Dicionário com título, preço, área, localização, descrição, link, data
            
        Returns:
            normalized_item com campos marcados com confidence: high | medium | low
        """
        # Suporta tanto RawListing objects como dicts
        def get_field(obj, field):
            if hasattr(obj, field):
                return getattr(obj, field, "")
            elif isinstance(obj, dict):
                return obj.get(field, "")
            return ""
        
        normalized = {
            "title": get_field(raw_item, "title").strip() if get_field(raw_item, "title") else "",
            "link": get_field(raw_item, "link"),
            "date": get_field(raw_item, "published_date") or get_field(raw_item, "date"),
            "raw_data": raw_item,  # Guardar original para debug
            "normalization_issues": []
        }
        
        # Normalizar preço
        normalized["price"], normalized["price_confidence"] = self._normalize_price(
            get_field(raw_item, "price")
        )
        
        # Normalizar área
        normalized["area"], normalized["area_confidence"] = self._normalize_area(
            get_field(raw_item, "area")
        )
        
        # Detectar erro comum: preço < área (swap provável)
        if (normalized["price"] is not None and 
            normalized["area"] is not None and 
            normalized["price"] < 100 and 
            normalized["area"] > 1000):
            
            self.logger.warning(
                f"SWAP DETECTADO: {normalized['title']} - "
                f"preço ({normalized['price']}) < área ({normalized['area']})"
            )
            normalized["normalization_issues"].append("SWAP_DETECTED_PRICE_AREA")
            # Não fazer swap automático - marcar para revisão
        
        # Normalizar localização (manter textual, será processada por Location Agent)
        normalized["location"] = get_field(raw_item, "location").strip() if get_field(raw_item, "location") else ""
        normalized["location_confidence"] = (
            "high" if normalized["location"] and len(normalized["location"]) > 5 else "low"
        )
        
        # Normalizar descrição (truncar se muito grande)
        desc = get_field(raw_item, "description")
        desc = desc.strip() if desc else ""
        if len(desc) > 5000:
            normalized["description"] = desc[:5000]
            normalized["normalization_issues"].append("DESCRIPTION_TRUNCATED")
        else:
            normalized["description"] = desc
        
        # Normalizar tipologia se presente
        normalized["typology"], normalized["typology_confidence"] = self._normalize_typology(
            get_field(raw_item, "typology")
        )
        
        return normalized
    
    def _normalize_price(self, price_raw: str) -> tuple[Optional[int], str]:
        """
        Extrai preço numérico de string como '200.000 €' → 200000
        
        Returns:
            (price_int, confidence)
        """
        if not price_raw or not str(price_raw).strip():
            return None, "low"
        
        try:
            # Remover símbolos comuns
            price_str = str(price_raw).strip()
            price_str = re.sub(r'[€$£,.´`]', '', price_str)
            
            # Extrair números
            numbers = re.findall(r'\d+', price_str)
            
            if not numbers:
                return None, "low"
            
            # Heurística: se último número > 100, é preço inteiro
            # Se múltiplos números, usar padrão português (ponto = milhar, vírgula = decimal)
            if len(numbers) == 1:
                return int(numbers[0]), "high"
            
            # Múltiplos números: assume formato português
            price = int(''.join(numbers[:len(numbers)-1]))
            return price, "medium"
        
        except Exception as e:
            self.logger.debug(f"Erro ao normalizar preço '{price_raw}': {e}")
            return None, "low"
    
    def _normalize_area(self, area_raw: str) -> tuple[Optional[int], str]:
        """
        Extrai área de string como '250 m²' → 250
        
        Returns:
            (area_int, confidence)
        """
        if not area_raw or not str(area_raw).strip():
            return None, "low"
        
        try:
            area_str = str(area_raw).strip()
            
            # Remover símbolos m², m2, etc
            area_str = re.sub(r'[m²m2´`]', '', area_str)
            area_str = re.sub(r'[,.´`]', '', area_str)
            
            # Extrair números
            numbers = re.findall(r'\d+', area_str)
            
            if not numbers:
                return None, "low"
            
            # Usar primeiro número (geralmente é o principal)
            area = int(numbers[0])
            
            # Validação de sanidade
            if area < 10 or area > 1000:
                self.logger.warning(f"Área suspeita: {area} m²")
                return area, "medium"
            
            return area, "high"
        
        except Exception as e:
            self.logger.debug(f"Erro ao normalizar área '{area_raw}': {e}")
            return None, "low"
    
    def _normalize_typology(self, typology_raw: str) -> tuple[Optional[str], str]:
        """
        Normaliza tipologia: T0, T1, T2, T3, etc.
        
        Returns:
            (typology, confidence)
        """
        if not typology_raw or not str(typology_raw).strip():
            return None, "low"
        
        try:
            typology_str = str(typology_raw).strip().upper()
            
            # Padrão: T[número] ou similar
            match = re.search(r'T(\d+)', typology_str)
            if match:
                return f"T{match.group(1)}", "high"
            
            # Se tiver números, tentar extrair
            numbers = re.findall(r'\d+', typology_str)
            if numbers:
                return f"T{numbers[0]}", "medium"
            
            return None, "low"
        
        except Exception as e:
            self.logger.debug(f"Erro ao normalizar tipologia '{typology_raw}': {e}")
            return None, "low"
    
    def get_normalization_summary(self, items: list) -> Dict[str, Any]:
        """Retorna resumo de normalização de uma batch"""
        return {
            "total_items": len(items),
            "items_with_issues": sum(1 for i in items if i.get("normalization_issues")),
            "price_extraction_rate": sum(
                1 for i in items if i.get("price") is not None
            ) / len(items) if items else 0,
            "area_extraction_rate": sum(
                1 for i in items if i.get("area") is not None
            ) / len(items) if items else 0,
            "location_extraction_rate": sum(
                1 for i in items if i.get("location")
            ) / len(items) if items else 0,
        }
