import unicodedata
import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

def normalize_str(s: str) -> str:
    if not s:
        return ''
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-z0-9 ]', '', s)
    return s

def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def deduplicate_announcements(items: List[Dict], threshold: float = 0.88) -> Tuple[List[Dict], List[List[Dict]]]:
    """
    Agrupa anúncios muito semelhantes (mesmo imóvel) sem apagar nada.
    Retorna:
      - Lista de anúncios únicos (um por grupo, o mais completo)
      - Lista de grupos (cada grupo = anúncios considerados iguais)
    """
    groups = []
    used = set()
    for i, item in enumerate(items):
        if i in used:
            continue
        group = [item]
        norm_title = normalize_str(item.get('title', ''))
        norm_loc = normalize_str(item.get('location', ''))
        area = str(item.get('area', ''))
        price = str(item.get('price', ''))
        for j in range(i+1, len(items)):
            if j in used:
                continue
            other = items[j]
            if abs(len(norm_title) - len(normalize_str(other.get('title','')))) > 10:
                continue
            score = (
                0.5 * similar(norm_title, normalize_str(other.get('title','')))
                + 0.2 * similar(norm_loc, normalize_str(other.get('location','')))
                + 0.15 * (area == str(other.get('area','')))
                + 0.15 * (price == str(other.get('price','')))
            )
            if score >= threshold:
                group.append(other)
                used.add(j)
        used.add(i)
        groups.append(group)
    # Para cada grupo, escolher o anúncio mais completo (maior descrição)
    unique = [max(g, key=lambda x: len(str(x.get('description','')))) for g in groups]
    return unique, groups
