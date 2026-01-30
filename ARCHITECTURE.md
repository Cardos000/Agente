# 🏗️ Arquitetura Multi-Agente - Real Estate Bot

## Visão Geral

O sistema implementa a especificação "PROMPT MESTRE" com uma arquitetura **multi-agente defensiva**, onde cada agente é responsável por uma tarefa específica, com logging detalhado e princípio **anti-overfiltering** obrigatório.

---

## 📋 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SCRAPER (Imovirtual, OLX, etc)                   │
│                      ↓ HTML bruto + parsing                         │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│         1️⃣ NORMALIZATION AGENT (analysis/normalization.py)         │
│   • Limpar símbolos (€, m², etc)                                    │
│   • Normalizar números                                              │
│   • Detectar erros comuns (preço < área → swap)                   │
│   • Marcar confiança: high | medium | low                          │
│   ✓ Nunca crasha: regex defensiva                                  │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│    2️⃣ LOCATION VERIFICATION AGENT (analysis/location_verification) │
│   • Resolver localização textual → concelho                         │
│   • Encontrar estação de Comboio/Metro                             │
│   • Validar AMP (Área Metropolitana do Porto)                      │
│   • Retornar: station, transport_type, confidence                  │
│   ✓ Nunca inventa: low confidence se incerto                       │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│   3️⃣ PROFILE COMPATIBILITY AGENT (analysis/profile_compatibility)  │
│   • Validar T2+ (tipologia)                                         │
│   • Área ≥ 90 m²                                                    │
│   • Preço 60-250k €                                                 │
│   • AMP + Transporte confirmado                                     │
│   ✓ Só rejeita se CONFIRMADO (high confidence)                     │
│   ⚠️ Incerteza → marcar para revisão manual                        │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│       4️⃣ SCORING AGENT (analysis/ranker.py)                        │
│   Calcula score explicável (0-100):                                 │
│   • Valor de Mercado: 0-50 (€/m² vs benchmark local)              │
│   • Amenidades: 0-20 (garagem, varanda, terraço)                  │
│   • Confiança Transporte: 0-15 (se confirmado)                    │
│   • Fit Regulatório: 0-15 (confiança nos requisitos)              │
│   ✓ Explicável: cada ponto tem razão clara                        │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│         5️⃣ PIPELINE ORCHESTRATOR (analysis/pipeline.py)            │
│   • Coordena todos os agentes                                       │
│   • Logging detalhado de cada stage                                │
│   • REGRA ANTI-OVERFILTERING: alertas se 0 aprovados             │
│   • Categoriza: approved | needs_review | rejected                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│        6️⃣ OUTPUT GENERATOR (analysis/output.py) - MODO C3          │
│   Gera 4 arquivos:                                                  │
│   📄 top_opportunities.md (aprovados)                              │
│   📄 needs_review.md (incertos com explicação)                    │
│   📄 rejected.log (rejeitados com motivo)                         │
│   📊 all_scored.csv (todos os dados para análise)                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Agentes Detalhados

### 1️⃣ Normalization Agent (`analysis/normalization.py`)

**Responsabilidade**: Limpar dados brutos com confiança

```python
from analysis.normalization import NormalizationAgent

agent = NormalizationAgent()
normalized = agent.normalize(raw_item)

# Retorna:
{
    "price": 150000,              # int | None
    "price_confidence": "high",   # Baseado em extração
    "area": 100,                  # int | None
    "area_confidence": "high",
    "location": "Porto, Miragaia",
    "location_confidence": "high",
    "typology": "T2",
    "typology_confidence": "high",
    "normalization_issues": []    # Flags de problemas detectados
}
```

**Regras**:
- ✅ Regex defensiva: nunca crashar
- ✅ Se extração falha → field = None
- ✅ Detecta swaps (preço < 100 e área > 1000)
- ⚠️ **Não rejeita**: apenas marca confidence e issues

---

### 2️⃣ Location Verification Agent (`analysis/location_verification.py`)

**Responsabilidade**: Resolver localização e encontrar transporte

```python
from analysis.location_verification import LocationVerificationAgent

agent = LocationVerificationAgent()
location_result = agent.verify(item)

# Retorna:
{
    "location_text": "Porto",
    "council": "Porto",            # Concelho detectado
    "transport_type": "Metro",     # "Comboio" | "Metro" | "Unknown"
    "station": "Bolhão",
    "confidence": "high",          # high | medium | low
    "method": "text",              # "text" | "geo" | "mixed"
    "explanation": "Metro Bolhão detectado em Porto"
}
```

**Regras Absolutas**:
- ✅ Se não confirma → confidence = "low"
- ✅ **NUNCA inventa** estações
- ✅ **NUNCA elimina** por falha de localização
- ✅ Valida se está em AMP (Área Metropolitana do Porto)

**Estações Reconhecidas**:
- **Comboio**: Campanhã, Porto
- **Metro**: Todas as linhas A-F (20+ estações)

---

### 3️⃣ Profile Compatibility Agent (`analysis/profile_compatibility.py`)

**Responsabilidade**: Validar contra perfil imobiliário

```python
from analysis.profile_compatibility import ProfileCompatibilityAgent

agent = ProfileCompatibilityAgent()
compat_result = agent.validate(item, location_result)

# Retorna:
{
    "matches_profile": False,     # bool
    "meets_requirements": {
        "tipologia": True,
        "área": True,
        "preço": False,           # ❌ Fora do range
        "localização_amp": True,
        "transporte": None        # Incerto
    },
    "confidence_score": 0.8,      # 0-1: % de requisitos confirmados
    "reasons": [
        "Tipologia T2 ≥ T2",
        "Preço 300.000€ > máximo 250.000€"
    ],
    "concerns": [
        "Transporte não confirmado - marcar para revisão"
    ],
    "recommendation": "needs_review"  # approved | needs_review | rejected
}
```

**Decisão de Rejeição**:
- ❌ **Rejeitar AUTOMATICAMENTE se**:
  - Tipologia < T2 (confirmada com alta confiança)
  - Área < 90 m² (confirmada com alta confiança)
  - Preço fora 60-250k € (confirmada com alta confiança)
  - Fora da AMP (confirmado com alta confiança)
  - Sem transporte confirmado (alta confiança de inexistência)

- ⚠️ **PARA REVISÃO se**:
  - Informação ausente ou confidence baixa/medium
  - Pelo menos um requisito não confirmado

---

### 4️⃣ Scoring Agent (`analysis/ranker.py`)

**Responsabilidade**: Calcular score explicável (0-100)

```python
from analysis.ranker import ScoringAgent

agent = ScoringAgent()
score_result = agent.score(item, location_result, compatibility_result)

# Retorna:
{
    "score": 68,                  # 0-100
    "score_breakdown": {
        "market_value": 30,       # 0-50 (vs benchmark local)
        "features": 15,           # 0-20 (garagem, varanda, terraço)
        "transport_confidence": 15, # 0-15 (confirmado?)
        "regulatory_fit": 8       # 0-15 (requisitos ok?)
    },
    "details": {
        "price_m2": 1500.0,
        "price_vs_benchmark": "+7.1% vs 1400€/m²",
        "features_found": ["Varanda", "Terraço"],
        "transport_info": "Metro Bolhão - ALTA CONFIANÇA",
        "confidence_notes": [...]
    }
}
```

**Scoring Detalhado**:

| Componente | Máx | Critério |
|-----------|-----|----------|
| **Valor de Mercado** | 50 | Preço/m² vs benchmark local |
| | 50 | > 25% abaixo (GOLD) |
| | 40 | 15-25% abaixo (VERY GOOD) |
| | 30 | 5-15% abaixo (GOOD) |
| | 20 | ±5% (FAIR) |
| | 10 | 5-25% acima |
| | 0 | > 25% acima |
| **Amenidades** | 20 | Garagem (+7), Varanda (+5), Terraço (+8) |
| **Transporte** | 15 | Comboio/Metro confirmado |
| **Fit Regulatório** | 15 | % de requisitos confirmados |

---

### 5️⃣ Pipeline Orchestrator (`analysis/pipeline.py`)

**Responsabilidade**: Coordenar todos os agentes com logging

```python
from analysis.pipeline import PipelineOrchestrator

orchestrator = PipelineOrchestrator()
result = orchestrator.process(raw_items)

# Retorna:
{
    "approved": [...],        # Score ≥ 40 e sem red flags
    "needs_review": [...],    # Incertos
    "rejected": [...],        # Fora do perfil (confirmado)
    "stats": {
        "total_processed": 50,
        "approved_count": 5,
        "needs_review_count": 8,
        "rejected_count": 37,
        "error_count": 0,
        "timestamp": "2026-01-28T15:30:00"
    }
}
```

**Logging Obrigatório**:
Cada stage (normalization, location, compatibility, scoring) gera:
- ✅ Contagem de sucesso
- ℹ️ Taxa de extração/confirmação
- ⚠️ Alertas de overfiltering (se 0 aprovados)
- 🚨 Erros com detalhe

---

### 6️⃣ Output Generator (`analysis/output.py`) - MODO C3

**Gera 4 outputs**:

#### 📄 `output/top_opportunities.md`
Anúncios aprovados com score ≥ 40:
- Score e breakdown explicado
- Preço/m² vs benchmark
- Amenidades encontradas
- Link direto
- Sumário estatístico

#### 📄 `output/needs_review.md`
Anúncios com informação incerta:
- Agrupados por motivo
- Explicação de por que está em revisão
- Link direto para você revisar manualmente

#### 📄 `output/rejected.log`
Anúncios rejeitados:
- Agrupados por razão de rejeição
- Motivos específicos
- Para auditoria

#### 📊 `output/all_scored.csv`
Dataset completo:
- Status, score, detalhes
- Para análise em Excel/Python
- Permite post-processing

---

## 🛡️ REGRA ANTI-OVERFILTERING

**Princípio**: "É preferível mostrar a mais do que perder uma oportunidade"

### Implementação

1. **Nunca elimina por ausência de informação**
   ```python
   # ❌ ERRADO
   if not location_confirmed:
       reject()  # NUNCA!
   
   # ✅ CERTO
   if not location_confirmed:
       mark_for_review()  # Deixar utilizador decidir
   ```

2. **Confidence Scores**
   - Se `confidence == "high"` → pode rejeitar automaticamente
   - Se `confidence == "medium"` → marcar para revisão
   - Se `confidence == "low"` → SEMPRE para revisão

3. **Alertas de Over-filtering**
   ```
   ⚠️ AVISO: Pipeline resultou em 0 aprovados e 0 para revisão!
      Isto pode indicar filtros muito restritivos.
      Recomendação: Revisar critérios de compatibilidade.
   ```

4. **Estatísticas Transparentes**
   Cada run mostra:
   - Taxa de extração (preço, área, etc)
   - % de anúncios para revisão
   - Motivos principais de rejeição

---

## 📊 Perfil Imobiliário (Definição em `config.py`)

```python
# TIPOLOGIA
MIN_TYPOLOGY = "T2"  # Mínimo T2
MIN_AREA = 90        # m²

# PREÇO
MIN_PRICE = 60000    # €
MAX_PRICE = 250000   # €

# LOCALIZAÇÃO
AMP_COUNCILS = [
    "Porto", "Matosinhos", "Maia", "Gondomar", "Valongo",
    "Ermesinde", "Rio Tinto", "Penafiel", "Lousada",
    "Vila Nova de Gaia", "Espinho", "Póvoa de Varzim"
]

# TRANSPORTE (Requisito Obrigatório)
COMBOIO_STATIONS = ["Campanhã", "Porto"]
METRO_STATIONS = [20+ estações das linhas A-F]

# NICE-TO-HAVE (Nunca filtram, apenas bónus)
NICE_TO_HAVE = {
    "garagem": 5,
    "varanda": 3,
    "terraço": 4
}
```

---

## 🚀 Modos de Execução

### `EXECUTION_MODE = "new"`
Processa **apenas anúncios novos** (não em `seen_listings.json`)
- Ideal para runs contínuas
- Histórico mantido de forma persistente

### `EXECUTION_MODE = "window"`
Processa anúncios dos **últimos X dias** (configurável)
- Útil para "re-análise" periódica
- Combina novos + revisão de recentes

---

## 🔄 Como Usar

### Basic Run
```python
python main.py
```
Processa tudo com modo "new"

### Com Configuração Customizada
```python
# config.py
EXECUTION_MODE = "window"
DAYS_WINDOW = 7  # Últimos 7 dias
```

### Outputs Gerados
```
output/
├── top_opportunities.md   (Boas oportunidades)
├── needs_review.md        (Para revisar manualmente)
├── rejected.log           (Rejeitados + motivos)
└── all_scored.csv         (Dataset completo)

bot.log                     (Logs detalhados)
seen_listings.json          (Histórico de processados)
```

---

## 📝 Logging Detalhado

Cada run gera `bot.log` com:

```
2026-01-28 15:30:45 - RealEstateBot - INFO - 🤖 REAL ESTATE BOT - INICIANDO PIPELINE
2026-01-28 15:30:45 - RealEstateBot - INFO - 📡 FASE 1: SCRAPING DE PORTAIS
2026-01-28 15:30:52 - RealEstateBot - INFO - ✓ Scraping concluído: 142 anúncios coletados
2026-01-28 15:30:52 - RealEstateBot - INFO - 📋 STAGE 1: Normalizando dados brutos...
2026-01-28 15:30:52 - NormalizationAgent - INFO - ✓ 142/142 normalizados
2026-01-28 15:30:52 - NormalizationAgent - INFO -     - Taxa extração preço: 98.6%
2026-01-28 15:30:52 - LocationVerificationAgent - INFO - 🗺️  STAGE 2: Verificando localização...
...
2026-01-28 15:30:56 - PipelineOrchestrator - INFO - ✅ VALIDAÇÃO ANTI-OVERFILTERING...
2026-01-28 15:30:56 - PipelineOrchestrator - INFO - 📊 RESUMO FINAL
```

---

## 🎯 Exemplo de Fluxo Completo

**Entrada**: Anúncio bruto do Imovirtual
```json
{
    "title": "T2 em Porto",
    "price": "180.000 €",
    "area": "95 m²",
    "location": "Porto, Miragaia",
    "description": "Apto com varanda a 10 min de Metro Bolhão",
    "link": "https://...",
    "date": "2026-01-28"
}
```

**Saída Final**:
```markdown
## ⭐ #2 - T2 em Porto

**Score Total: 72/100** (MUY BOM)

**Análise de Score:**
- 💰 Valor de Mercado: 30/50 pts
  - +7.1% vs 3500€/m² (Porto)
- 🏠 Amenidades: 5/20 pts
  - Varanda
- 🚇 Transporte: 15/15 pts
  - Metro Bolhão - ALTA CONFIANÇA
- ✅ Compatibilidade: 15/15 pts

**Detalhes do Imóvel:**
- **Preço:** €180,000
- **Área:** 95 m²
- **Tipologia:** T2
- **Localização:** Porto, Miragaia
- **Transporte:** Metro - Bolhão
- **Link:** [T2 em Porto](https://...)
- **Data:** 2026-01-28
```

---

## 🔍 Troubleshooting

### "0 aprovados, 0 para revisão"
- Filtros muito restritivos
- Revisar `config.py` (preço min/max, tipologia, etc)
- Logs mostram razões específicas

### "Taxa de extração baixa (<80%)"
- Portal mudou estrutura HTML
- Atualizar regex em `normalization.py`
- Revisar `bot.log` para erros específicos

### "Muitos para revisão manual"
- Normalizar mais agentes
- Melhorar Location Verification (adicionar estações)
- Diminuir confiança de "low" para automatizar mais

---

## 📚 Referências Rápidas

| Arquivo | Propósito |
|---------|----------|
| `config.py` | Perfil + parâmetros globais |
| `main.py` | Orquestrador principal |
| `analysis/normalization.py` | Limpeza dados |
| `analysis/location_verification.py` | Localização + transporte |
| `analysis/profile_compatibility.py` | Validação perfil |
| `analysis/ranker.py` | Scoring explicável |
| `analysis/pipeline.py` | Coordenação multi-agente |
| `analysis/output.py` | Geração de relatórios |

---

## ✨ Próximas Melhorias (Roadmap)

- [ ] Integração com API de Geolocalização (coords → estação)
- [ ] ML para detecção de anomalias em preço
- [ ] Histórico de preços por local
- [ ] Notificações em tempo real (Email/WhatsApp)
- [ ] Dashboard interativo
- [ ] Multi-portal unificado

---

**Filosofia Final**: 🛡️ Conservador a REJEITAR, Agressivo a EXPLICAR.

Qualquer dúvida = Marcado para revisão manual pelo utilizador.
