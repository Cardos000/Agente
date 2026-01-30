"""
Location Verification Agent
Responsável por resolver localização textual imprecisa → concelho, coordenadas, estações.

Regras absolutas:
- Se não conseguir confirmar → confidence = low
- NUNCA inventar
- NUNCA eliminar anúncio por falha de localização
"""

import re
import logging
from typing import Dict, Any, Optional, List
from config import AMP_COUNCILS, COMBOIO_STATIONS, METRO_STATIONS

logger = logging.getLogger(__name__)


class LocationVerificationAgent:
    """Verifica e resolve localização com transporte associado"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.amp_councils = set(c.lower() for c in AMP_COUNCILS)
        self.metro_stations = set(s.lower() for s in METRO_STATIONS)
        self.comboio_stations = set(s.lower() for s in COMBOIO_STATIONS)
    
    def verify(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica localização e associa transporte.
        
        Returns:
            {
                "location_text": str,
                "council": str | None,
                "transport_type": "Comboio" | "Metro" | "Unknown",
                "station": str | None,
                "coordinates": [lat, lon] | None,
                "confidence": "high" | "medium" | "low",
                "method": "text" | "geo" | "mixed",
                "explanation": str
            }
        """
        location_text = item.get("location", "")
        title = item.get("title", "")
        description = item.get("description", "")
        
        # Combinar texto para análise
        full_text = f"{location_text} {title} {description}".lower()
        
        result = {
            "location_text": location_text,
            "council": None,
            "transport_type": "Unknown",
            "station": None,
            "coordinates": None,
            "confidence": "low",
            "method": None,
            "explanation": ""
        }
        
        # 1. Tentar encontrar concelho
        council = self._extract_council(full_text)
        if council:
            result["council"] = council
            result["explanation"] += f"Concelho detectado: {council}. "
        
        # 2. Tentar encontrar estação de transporte
        station, transport_type = self._find_transport_station(full_text)
        if station:
            result["station"] = station
            result["transport_type"] = transport_type
            result["explanation"] += f"Estação {transport_type}: {station}. "
            
            # Se encontrou estação → confidence alta
            if council:
                result["confidence"] = "high"
                result["method"] = "text"
            else:
                result["confidence"] = "medium"
                result["method"] = "text"
        else:
            result["explanation"] += "Nenhuma estação de transporte detectada. "
            result["confidence"] = "low"
            result["method"] = "text"
        
        # 3. Validação AMP
        if council and council.lower() not in self.amp_councils:
            result["explanation"] += f"AVISO: {council} fora da AMP. "
            result["confidence"] = "high"  # Confirmado que está fora
        
        # Se nada foi encontrado mas tem localização
        if not result["council"] and location_text:
            result["confidence"] = "low"
            result["explanation"] += "Localização textual não parsing. Marcar para revisão. "
        
        return result
    
    def _extract_council(self, text: str) -> Optional[str]:
        """Detecta concelho da AMP no texto"""
        for council in self.amp_councils:
            # Usar regex com word boundaries para evitar false positives
            pattern = r'\b' + re.escape(council) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return council.title()
        return None
    
    def _find_transport_station(self, text: str) -> tuple[Optional[str], str]:
        """
        Detecta estação de Comboio ou Metro.
        
        Returns:
            (station_name, transport_type)
        """
        # Metro (prioritário)
        for station in self.metro_stations:
            pattern = r'\b' + re.escape(station) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return station.title(), "Metro"
        
        # Comboio (Campanhã é crítico)
        for station in self.comboio_stations:
            pattern = r'\b' + re.escape(station) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return station.title(), "Comboio"
        
        return None, "Unknown"
    
    def extract_distance_hints(self, text: str) -> List[str]:
        """
        Extrai hints de distância do texto (para alertas de imprecisão).
        Ex: "a 5 minutos de Metro", "perto de Campanhã"
        """
        hints = []
        
        # Padrão: "X minutos de [Metro|Comboio|estação]"
        minute_patterns = re.findall(r'(\d+)\s*min(utos)?.*?(metro|comboio|estação|estacao)', text, re.IGNORECASE)
        for minutes, _, transport in minute_patterns:
            hints.append(f"{minutes}min de {transport}")
        
        # Padrão: "a X km de"
        km_patterns = re.findall(r'a\s*(\d+(?:[.,]\d+)?)\s*km\s*de\s*([^.,]+)', text, re.IGNORECASE)
        for km, location in km_patterns:
            hints.append(f"{km}km de {location.strip()}")
        
        return hints
    
    def validate_transport_requirement(self, item: Dict[str, Any], location_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida se cumpre requisito de transporte:
        - Comboio direto para Campanhã OU
        - Estação de Metro próxima
        
        Returns:
            {
                "meets_requirement": bool,
                "reason": str,
                "confidence": str
            }
        """
        transport_type = location_result.get("transport_type", "Unknown")
        station = location_result.get("station")
        location_confidence = location_result.get("confidence")
        
        result = {
            "meets_requirement": False,
            "reason": "",
            "confidence": location_confidence
        }
        
        if transport_type == "Comboio" and station:
            # Comboio válido (assume direto para Campanhã se mencionado)
            result["meets_requirement"] = True
            result["reason"] = f"Acesso a {station} (Comboio)"
        
        elif transport_type == "Metro" and station:
            # Metro válido
            result["meets_requirement"] = True
            result["reason"] = f"Acesso a {station} (Metro)"
        
        elif transport_type == "Unknown":
            result["meets_requirement"] = False
            result["reason"] = "Nenhum transporte confirmado"
            result["confidence"] = "low"
        
        return result
