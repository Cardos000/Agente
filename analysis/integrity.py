import re
import logging

class IntegrityEngine:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Lista de concelhos permitidos
        self.ALLOWED_CONCELHOS = [
            'porto', 'matosinhos', 'maia', 'vila nova de gaia', 'gondomar',
            'valongo', 'ermesinde', 'rio tinto', 'penafiel', 'lousada', 
            'paredes', 'paços de ferreira', 'santo tirso',
            'póvoa de varzim', 'vila do conde', 'trofa',
            'espinho', 'santa maria da feira', 'arouca', 'celorico de basto'
        ]
        
        # Estações Chave (Hubs)
        self.RAIL_HUBS = {
            "CP": [
                "campanhã", "contumil", "rio tinto", "ermesinde", "valongo", 
                "paredes", "cete", "penafiel", "caíde", "livração", "meinedo",
                "lousado", "lordelo", "vizela", "guimarães", "nine",
                "general torres", "pedras rubras", "vila do conde", "póvoa de varzim",
                "granja", "espinho", "silvalde", "coimbrões", "esmoriz"
            ],
            
            "METRO": [
                "estádio do dragão", "campanhã", "heroísmo", "vasco da gama",
                "contumil", "fânzeres", "venda nova", "rio tinto",
                "bolhão", "trindade", "casa da música", "carolina michaelis",
                "senhor de matosinhos", "brito capelo", "matosinhos sul",
                "senhora da hora", "sete bicas", "viso", "ramalde",
                "francos", "fórum maia", "zona industrial", "ismai",
                "mandim", "pedras rubras", "lidador", "vila do conde",
                "azurara", "varziela", "mindelo", "modivas",
                "salgueiros", "fonte do cuco", "custóio", "custódio",
                "ipo", "polo universitário", "hospital são joão",
                "marquês", "aliados", "são bento", "jardim do morro",
                "general torres", "câmara de gaia", "santo ovídio"
            ]
        }
        
        # Palavras-chave de risco (para eliminar lixo automaticamente)
        self.RISK_KEYWORDS = [
            'ocupado', 'inquilino problemático', 'judicial', 'penhora',
            'ruína', 'para demolir', 'em ruínas', 'reconstrução total',
            'indiviso', 'parte de moradia', 'permuta'
        ]
        
        self.PORTAGENS_ZONES = [
            'vila do conde', 'póvoa de varzim', 'espinho', 'santa maria da feira',
            'arouca', 'vila nova de famalicão', 'santo tirso', 'lousada', 'penafiel'
        ]

    def process(self, raw_data):
        validated = []
        rejected_location = 0
        rejected_risk = 0
        # rejected_no_transport = 0 # Desativado: não queremos rejeitar por isto
        
        self.logger.info("=== INTEGRITY ENGINE: Starting Validation ===")
        
        for item in raw_data:
            # 1. Validação de Localização (Mantém-se estrita)
            if not self.validate_location(item):
                rejected_location += 1
                self.logger.debug(f"[Location Rejected] {item.get('location', 'N/A')}")
                continue
            
            # 2. Validação de Risco (Mantém-se estrita)
            if self.is_high_risk(item):
                rejected_risk += 1
                continue
            
            # 3. Validação de Transporte (CORRIGIDO: Agora é permissivo)
            transport_type = self.validate_transit(item)
            
            if transport_type == "Não":
                # Em vez de rejeitar, marcamos como Indefinido
                transport_type = "Indefinido / Carro"
                # Apenas registamos para debug, mas aprovamos o item
                self.logger.debug(f"[Transport Warning] {item.get('title', '')[:30]} - Sem transporte claro.")
            
            item['transport'] = transport_type
            item['portagens'] = self.check_portagens(item)
            
            validated.append(item)
        
        self.logger.info("=== VALIDATION SUMMARY ===")
        self.logger.info(f"Approved: {len(validated)}")
        self.logger.info(f"Rejected (Location): {rejected_location}")
        self.logger.info(f"Rejected (Risk): {rejected_risk}")
        self.logger.info(f"Total Processed: {len(raw_data)}")
        
        return validated

    def validate_location(self, item):
        location = item.get('location', '').lower()
        title = item.get('title', '').lower()
        # description = item.get('description', '').lower() # Descrição pode ter ruído
        
        full_text = f"{location} {title}"
        
        # Lista negra de distritos distantes para evitar falsos positivos
        OUTSIDE_AMP = [
            'lisboa', 'setúbal', 'almada', 'cascais', 'sintra', 'loures',
            'braga', 'barcelos', 'viana do castelo', 'felgueiras', 'amarante',
            'aveiro', 'águeda', 'ílhavo', 'ovar',
            'coimbra', 'figueira da foz', 'leiria',
            'viseu', 'lamego', 'peso da régua'
        ]
        
        # Se contiver uma cidade proibida no título/localização, rejeita logo
        if any(city in full_text for city in OUTSIDE_AMP):
            return False
        
        # Verifica se está na nossa lista permitida
        if any(concelho in full_text for concelho in self.ALLOWED_CONCELHOS):
            return True
        
        # Permite "Porto" genérico
        if 'porto' in full_text:
            return True
        
        return False

    def is_high_risk(self, item):
        # Verifica Título e Descrição
        text = (item.get('title', '') + " " + item.get('description', '')).lower()
        
        # Se for T0 ou T1 no título, rejeita (baseado na tua config anterior)
        title_upper = item.get('title', '').upper()
        if 'T0' in title_upper or 'T1' in title_upper:
            return True

        for keyword in self.RISK_KEYWORDS:
            if keyword in text:
                self.logger.info(f"[RISK DETECTED] '{keyword}' in: {item.get('title', 'No title')[:40]}")
                return True
        
        return False

    def validate_transit(self, item):
        # Combina tudo para procurar keywords
        full_text = (item.get('location', '') + " " + item.get('title', '') + " " + item.get('description', '')).lower()
        
        # 1. Procura estações exatas (CP)
        cp_keywords = ['comboio', ' cp ', 'estação de comboios', 'linha de comboio']
        for kw in cp_keywords:
            if kw in full_text:
                for station in self.RAIL_HUBS["CP"]:
                    if station in full_text:
                        return f"Comboio ({station.title()})"
                return "Comboio (Genérico)"
        
        # 2. Procura estações exatas (Metro)
        for station in self.RAIL_HUBS["METRO"]:
            if station in full_text and len(station) > 4: # Evita matches curtos falsos
                return f"Metro ({station.title()})"
        
        # 3. Procura menções genéricas (CORREÇÃO IMPORTANTE)
        # Regex para apanhar "metro", "metropolitano", mas ignorar "metro quadrado"
        if re.search(r'\bmetro(politano)?\b', full_text):
            # Se a palavra metro aparecer, verificamos se não é "metros quadrados" ou distância
            if not re.search(r'\d+\s*m(etros)?\s*(quadrados|²)', full_text) and "sem metro" not in full_text:
                return "Metro (Genérico)"

        return "Não"

    def check_portagens(self, item):
        location = item.get('location', '').lower()
        
        if any(zone in location for zone in self.PORTAGENS_ZONES):
            return "Sim"
        
        no_toll_zones = ['porto', 'matosinhos', 'maia', 'gondomar', 'valongo', 
                         'ermesinde', 'rio tinto', 'vila nova de gaia']
        if any(zone in location for zone in no_toll_zones):
            return "Não"
        
        return "Possível"