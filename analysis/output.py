"""
Output Module (Modo C3)
Gera relatórios estruturados:
- top_opportunities.md
- needs_review.md
- rejected.log
- all_scored.csv
"""

import os
import csv
import logging
from typing import List, Dict, Any
from datetime import datetime
import json
from config import (
    OUTPUT_DIR, TOP_OPPORTUNITIES_FILE, NEEDS_REVIEW_FILE,
    REJECTED_LOG_FILE, ALL_SCORED_CSV
)

logger = logging.getLogger(__name__)


class OutputGenerator:
    """Gera outputs estruturados em modo C3"""
    
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Cria diretório output se não existir"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"Criado diretório: {self.output_dir}")
    
    def generate_all(self, pipeline_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera todos os outputs.
        
        Returns:
            {
                "top_opportunities": filepath,
                "needs_review": filepath,
                "rejected_log": filepath,
                "all_scored_csv": filepath
            }
        """
        
        results = {}
        
        # 1. Top Opportunities
        results["top_opportunities"] = self.generate_top_opportunities(
            pipeline_result["approved"]
        )
        
        # 2. Needs Review
        results["needs_review"] = self.generate_needs_review(
            pipeline_result["needs_review"]
        )
        
        # 3. Rejected Log
        results["rejected_log"] = self.generate_rejected_log(
            pipeline_result["rejected"]
        )
        
        # 4. All Scored CSV
        results["all_scored_csv"] = self.generate_all_scored_csv(
            pipeline_result["approved"] +
            pipeline_result["needs_review"] +
            pipeline_result["rejected"]
        )
        
        return results
    
    def generate_top_opportunities(self, approved_items: List[Dict[str, Any]]) -> str:
        """Gera top_opportunities.md"""
        
        filepath = os.path.join(self.output_dir, TOP_OPPORTUNITIES_FILE)
        
        content = "# [OK] Boas Oportunidades Imobiliarias\n\n"
        content += f"**Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f"**Total encontradas:** {len(approved_items)}\n\n"
        
        if len(approved_items) == 0:
            content += "[AVISO] Nenhuma boa oportunidade encontrada nesta analise.\n\n"
            content += "💡 **Próximos passos:**\n"
            content += "- Revisar critérios de preço\n"
            content += "- Considerar localizações alternativas\n"
            content += "- Aguardar mais anúncios\n"
        else:
            # Ordenar por score (descendente)
            sorted_items = sorted(approved_items, key=lambda x: x.get("score", 0), reverse=True)
            
            for idx, item in enumerate(sorted_items, 1):
                content += self._format_opportunity_card(item, idx)
            
            # Sumário estatístico
            content += self._generate_summary_stats(sorted_items)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"[OK] Gerado: {filepath}")
        return filepath
    
    def generate_needs_review(self, review_items: List[Dict[str, Any]]) -> str:
        """Gera needs_review.md com justificações detalhadas"""
        
        filepath = os.path.join(self.output_dir, NEEDS_REVIEW_FILE)
        
        content = "# [REVISAO] Anuncios Pendentes de Revisao Manual\n\n"
        content += f"**Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f"**Total para revisar:** {len(review_items)}\n\n"
        
        content += "## Por que está aqui?\n\n"
        content += "Estes anúncios **não foram eliminados automaticamente** porque:\n"
        content += "- Informação insuficiente ou incerta\n"
        content += "- Pelo menos um requisito não foi confirmado\n"
        content += "- Requer validação manual do utilizador\n\n"
        content += "[INFO] **Principio:** Preferimos VOCE revisar do que perder uma oportunidade!\n\n"
        
        if len(review_items) == 0:
            content += "[OK] Nenhum anuncio pendente! Excelente!\n"
        else:
            # Agrupar por motivo
            grouped = self._group_by_review_reason(review_items)
            
            for reason, items in grouped.items():
                content += f"\n## {reason} ({len(items)})\n\n"
                
                for item in sorted(items, key=lambda x: x.get("score", 0), reverse=True):
                    content += self._format_review_card(item)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"[OK] Gerado: {filepath}")
        return filepath
    
    def generate_rejected_log(self, rejected_items: List[Dict[str, Any]]) -> str:
        """Gera rejected.log com razões de rejeição"""
        
        filepath = os.path.join(self.output_dir, REJECTED_LOG_FILE)
        
        content = "# [REJEITADOS] Anuncios Rejeitados (Log Detalhado)\n\n"
        content += f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f"Total rejeitados: {len(rejected_items)}\n\n"
        
        # Agrupar por razão principal
        grouped = self._group_by_rejection_reason(rejected_items)
        
        for reason, items in sorted(grouped.items(), key=lambda x: -len(x[1])):
            content += f"## {reason} ({len(items)} anúncios)\n\n"
            
            for item in items:
                compatibility = item.get("compatibility_result", {})
                content += f"**{item.get('title')}**\n"
                content += f"- Link: {item.get('link')}\n"
                content += f"- Preço: {item.get('price')} € | Área: {item.get('area')} m²\n"
                
                if compatibility.get("reasons"):
                    content += f"- Motivos:\n"
                    for r in compatibility["reasons"]:
                        content += f"  - {r}\n"
                
                content += "\n"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"[REJEITADO] Gerado: {filepath}")
        return filepath
    
    def generate_all_scored_csv(self, all_items: List[Dict[str, Any]]) -> str:
        """Gera CSV com todos os anúncios e scores"""
        
        filepath = os.path.join(self.output_dir, ALL_SCORED_CSV)
        
        # Preparar dados
        rows = []
        for item in sorted(all_items, key=lambda x: x.get("score", 0), reverse=True):
            compatibility = item.get("compatibility_result", {})
            location = item.get("location_result", {})
            score_details = item.get("score_details", {})
            
            row = {
                "status": item.get("final_status", "unknown"),
                "score": item.get("score", 0),
                "title": item.get("title", ""),
                "price": item.get("price", ""),
                "area_m2": item.get("area", ""),
                "price_m2": score_details.get("price_m2", ""),
                "location": item.get("location", ""),
                "council": location.get("council", ""),
                "transport": location.get("transport_type", "Unknown"),
                "station": location.get("station", ""),
                "typology": item.get("typology", ""),
                "confidence_score": compatibility.get("confidence_score", 0),
                "link": item.get("link", ""),
                "date": item.get("date", ""),
            }
            rows.append(row)
        
        # Escrever CSV
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                fieldnames = list(rows[0].keys()) if rows else []
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            self.logger.info(f"[OK] Gerado: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Erro ao gerar CSV: {e}")
            return filepath
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _format_opportunity_card(self, item: Dict[str, Any], index: int) -> str:
        """Formata card de oportunidade"""
        
        score = item.get("score", 0)
        score_breakdown = item.get("score_breakdown", {})
        score_details = item.get("score_details", {})
        location = item.get("location_result", {})
        
        # Determinar emoji baseado em score
        if score >= 80:
            emoji = "[EXCELENTE]"
            quality = "EXCELENTE"
        elif score >= 60:
            emoji = "[BOM]"
            quality = "MUY BOM"
        elif score >= 40:
            emoji = "[OK]"
            quality = "BOM"
        else:
            emoji = "[MARGINAL]"
            quality = "MARGINAL"
        
        card = f"\n## {emoji} #{index} - {item.get('title')}\n\n"
        card += f"**Score Total: {score}/100** ({quality})\n\n"
        
        # Breakdown de score
        card += "**Analise de Score:**\n"
        card += f"- 💰 Valor de Mercado: {score_breakdown.get('market_value', 0)}/50 pts\n"
        if score_details.get("price_vs_benchmark"):
            card += f"  - {score_details['price_vs_benchmark']}\n"
        
        card += f"- 🏠 Amenidades: {score_breakdown.get('features', 0)}/20 pts\n"
        if score_details.get("features_found"):
            for feature in score_details["features_found"]:
                card += f"  - {feature}\n"
        
        card += f"- [TRANSPORTE] Transporte: {score_breakdown.get('transport_confidence', 0)}/15 pts\n"
        if score_details.get("transport_info"):
            card += f"  - {score_details['transport_info']}\n"
        
        card += f"- [OK] Compatibilidade: {score_breakdown.get('regulatory_fit', 0)}/15 pts\n"
        
        # Informacoes principais
        card += "\n**Detalhes do Imovel:**\n"
        price = item.get('price')
        price_str = f"€{price:,}" if isinstance(price, (int, float)) else f"€{price if price else 'N/A'}"
        card += f"- **Preco:** {price_str}\n"
        card += f"- **Area:** {item.get('area')} m2\n"
        card += f"- **Tipologia:** {item.get('typology', 'N/A')}\n"
        card += f"- **Localizacao:** {item.get('location', 'N/A')}\n"
        
        if location.get("station"):
            card += f"- **Transporte:** {location['transport_type']} - {location['station']}\n"
        
        card += f"- **Link:** [{item.get('title')}]({item.get('link')})\n"
        card += f"- **Data:** {item.get('date', 'N/A')}\n\n"
        
        return card
    
    def _format_review_card(self, item: Dict[str, Any]) -> str:
        """Formata card de revisao"""
        
        compatibility = item.get("compatibility_result", {})
        location = item.get("location_result", {})
        
        card = f"\n### {item.get('title')}\n"
        price = item.get('price', 'N/A')
        price_str = f"€{price:,}" if isinstance(price, (int, float)) else f"€{price}"
        card += f"- **Preco:** {price_str}\n"
        card += f"- **Area:** {item.get('area', 'N/A')} m2\n"
        card += f"- **Localizacao:** {item.get('location', 'N/A')}\n"
        card += f"- **Score (incompleto):** {item.get('score', 0)}/100\n"
        
        card += f"\n**Por que esta em revisao:**\n"
        if compatibility.get("concerns"):
            for concern in compatibility["concerns"]:
                card += f"- [AVISO] {concern}\n"
        
        if location.get("explanation"):
            card += f"- [LOCALIZACAO] {location['explanation']}\n"
        
        card += f"\n**Link:** [{item.get('title')}]({item.get('link')})\n"
        card += f"**Data:** {item.get('date', 'N/A')}\n\n"
        
        return card
    
    def _group_by_review_reason(self, items: List[Dict]) -> Dict[str, List]:
        """Agrupa items por razao de revisao"""
        
        grouped = {}
        
        for item in items:
            compatibility = item.get("compatibility_result", {})
            
            if compatibility.get("concerns"):
                primary_reason = compatibility["concerns"][0]
            else:
                primary_reason = "Outros critérios"
            
            if primary_reason not in grouped:
                grouped[primary_reason] = []
            grouped[primary_reason].append(item)
        
        return grouped
    
    def _group_by_rejection_reason(self, items: List[Dict]) -> Dict[str, List]:
        """Agrupa items por razão de rejeição"""
        
        grouped = {}
        
        for item in items:
            compatibility = item.get("compatibility_result", {})
            
            # Extrair primeira razão
            if compatibility.get("reasons"):
                primary_reason = compatibility["reasons"][0]
            else:
                primary_reason = "Razão desconhecida"
            
            if primary_reason not in grouped:
                grouped[primary_reason] = []
            grouped[primary_reason].append(item)
        
        return grouped
    
    def _generate_summary_stats(self, items: List[Dict]) -> str:
        """Gera sumário estatístico"""
        
        stats = "\n\n---\n\n## [STATS] Sumario Estatistico\n\n"
        
        if not items:
            return stats
        
        # Preço
        prices = [item.get("price") for item in items if item.get("price")]
        if prices:
            stats += f"**Preço:**\n"
            stats += f"- Mínimo: €{min(prices):,}\n"
            stats += f"- Máximo: €{max(prices):,}\n"
            stats += f"- Médio: €{sum(prices)//len(prices):,}\n\n"
        
        # Área
        areas = [item.get("area") for item in items if item.get("area")]
        if areas:
            stats += f"**Área:**\n"
            stats += f"- Mínima: {min(areas)} m²\n"
            stats += f"- Máxima: {max(areas)} m²\n"
            stats += f"- Média: {sum(areas)//len(areas)} m²\n\n"
        
        # Score
        scores = [item.get("score", 0) for item in items]
        stats += f"**Scores:**\n"
        stats += f"- Melhor: {max(scores)}/100\n"
        stats += f"- Médio: {sum(scores)//len(scores)}/100\n\n"
        
        return stats
