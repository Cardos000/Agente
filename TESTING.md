# 🧪 INSTRUÇÕES DE TESTES - Real Estate Bot v2.0

## Validação da Implementação

Esta seção descreve como testar e validar cada componente do sistema.

---

## ✅ Testes de Unidade por Agente

### 1️⃣ Normalization Agent

```python
# Teste manualmente em Python REPL
from analysis.normalization import NormalizationAgent

agent = NormalizationAgent()

# Teste 1: Extração de preço
raw_item = {
    "price": "180.000 €",
    "area": "95 m²",
    "title": "T2 Porto",
    "location": "Porto",
    "description": ""
}

result = agent.normalize(raw_item)

# Validar
assert result["price"] == 180000
assert result["price_confidence"] == "high"
assert result["area"] == 95
assert result["area_confidence"] == "high"
print("✅ Teste 1 passou")

# Teste 2: Erro comum (swap detection)
raw_item_swap = {
    "price": "50",  # Preço muito baixo
    "area": "2500",  # Área muito alta
    "title": "T2",
    "location": "Porto",
    "description": ""
}

result_swap = agent.normalize(raw_item_swap)
assert "SWAP_DETECTED" in result_swap["normalization_issues"]
print("✅ Teste 2 (SWAP) passou")

# Teste 3: Falha de regex (nunca crashar)
raw_item_bad = {
    "price": "PRICE_MISSING",
    "area": "AREA_MISSING",
    "title": "T2",
    "location": "Porto",
    "description": ""
}

result_bad = agent.normalize(raw_item_bad)
assert result_bad["price"] is None
assert result_bad["area"] is None
print("✅ Teste 3 (sem crash) passou")
```

### 2️⃣ Location Verification Agent

```python
from analysis.location_verification import LocationVerificationAgent

agent = LocationVerificationAgent()

# Teste 1: Detecção de metro
item_metro = {
    "location": "Porto",
    "title": "T2 perto de Metro Bolhão",
    "description": "A 5 min do Metro"
}

result = agent.verify(item_metro)

assert result["council"] == "Porto"
assert result["station"] == "Bolhão"
assert result["transport_type"] == "Metro"
assert result["confidence"] == "high"
print("✅ Metro test passou")

# Teste 2: Localização fora AMP
item_outside = {
    "location": "Covilhã",
    "title": "T2",
    "description": ""
}

result_outside = agent.verify(item_outside)
assert result_outside["council"] == "Covilhã"
assert result_outside["confidence"] == "high"
# Mas está fora da AMP, será rejeitado posteriormente
print("✅ Out of AMP test passou")

# Teste 3: Nunca inventa (low confidence se não confirma)
item_vague = {
    "location": "Perto de transporte",
    "title": "T2",
    "description": ""
}

result_vague = agent.verify(item_vague)
assert result_vague["transport_type"] == "Unknown"
assert result_vague["confidence"] == "low"
print("✅ No invention test passou")
```

### 3️⃣ Profile Compatibility Agent

```python
from analysis.profile_compatibility import ProfileCompatibilityAgent

agent = ProfileCompatibilityAgent()

# Teste 1: Anúncio que cumpre tudo
item_good = {
    "typology": "T2",
    "typology_confidence": "high",
    "area": 100,
    "area_confidence": "high",
    "price": 150000,
    "price_confidence": "high"
}

location_good = {
    "council": "Porto",
    "confidence": "high",
    "transport_type": "Metro",
    "station": "Bolhão"
}

result = agent.validate(item_good, location_good)
assert result["matches_profile"] == True
assert result["recommendation"] == "approved"
print("✅ Good item test passou")

# Teste 2: Preço fora mas confidence baixa (for review)
item_uncertain = {
    "typology": "T2",
    "typology_confidence": "high",
    "area": 100,
    "area_confidence": "high",
    "price": 300000,
    "price_confidence": "low"  # Baixa confiança
}

location_ok = {
    "council": "Porto",
    "confidence": "high",
    "transport_type": "Metro",
    "station": "Bolhão"
}

result = agent.validate(item_uncertain, location_ok)
assert result["recommendation"] == "needs_review"  # Para revisão, não rejeitado!
print("✅ Uncertain price test passou (anti-overfiltering)")

# Teste 3: T1 (tipologia baixa) rejeitado
item_bad = {
    "typology": "T1",
    "typology_confidence": "high",
    "area": 100,
    "area_confidence": "high",
    "price": 150000,
    "price_confidence": "high"
}

location_ok = {
    "council": "Porto",
    "confidence": "high",
    "transport_type": "Metro",
    "station": "Bolhão"
}

result = agent.validate(item_bad, location_ok)
assert result["recommendation"] == "rejected"
assert "Tipologia T1 < T2" in str(result["reasons"])
print("✅ Low typology test passou")
```

### 4️⃣ Scoring Agent

```python
from analysis.ranker import ScoringAgent

agent = ScoringAgent()

# Teste 1: Score explicável
item = {
    "price": 150000,
    "area": 100,
    "title": "T2 em Porto",
    "location": "Porto",
    "description": "Tem varanda"
}

location = {
    "council": "Porto",
    "transport_type": "Metro",
    "station": "Bolhão"
}

compatibility = {
    "meets_requirements": {
        "tipologia": True,
        "área": True,
        "preço": True,
        "localização_amp": True,
        "transporte": True
    }
}

result = agent.score(item, location, compatibility)

assert result["score"] > 0
assert result["score_breakdown"]["market_value"] > 0
assert result["score_breakdown"]["transport_confidence"] > 0
assert "price_m2" in result["details"]
print(f"✅ Score test passou (score: {result['score']}/100)")
```

### 5️⃣ Pipeline Orchestrator

```python
from analysis.pipeline import PipelineOrchestrator

orchestrator = PipelineOrchestrator()

# Teste com batch pequeno
raw_items = [
    {
        "title": "T2 Porto 1",
        "price": "150.000 €",
        "area": "95 m²",
        "location": "Porto",
        "description": "Com varanda, perto de Metro Bolhão",
        "link": "https://test1.com"
    },
    {
        "title": "T1 Porto 2",
        "price": "100.000 €",
        "area": "70 m²",
        "location": "Porto",
        "description": "",
        "link": "https://test2.com"
    }
]

result = orchestrator.process(raw_items)

# Validar output
assert "approved" in result
assert "needs_review" in result
assert "rejected" in result
assert "stats" in result

assert len(result["approved"]) >= 0
assert result["stats"]["total_processed"] == len(raw_items)
print("✅ Pipeline test passou")
print(f"   - Aprovados: {len(result['approved'])}")
print(f"   - Para revisão: {len(result['needs_review'])}")
print(f"   - Rejeitados: {len(result['rejected'])}")
```

---

## 🎯 Testes de Integração

### Test 1: Full Pipeline com Dados Reais Simulados

```bash
# Simular um run completo
python main.py
```

**Validar**:
- ✅ Bot.log contém 5 phases
- ✅ Diretório `output/` criado
- ✅ Arquivo `top_opportunities.md` existe
- ✅ Arquivo `needs_review.md` existe
- ✅ Arquivo `rejected.log` existe
- ✅ Arquivo `all_scored.csv` existe

### Test 2: Modes de Execução

**Test 2a: Mode = "new"**
```python
# config.py
EXECUTION_MODE = "new"

# Rodar
python main.py
# Todos os anúncios devem ser processados
```

**Test 2b: Mode = "window"**
```python
# config.py
EXECUTION_MODE = "window"
DAYS_WINDOW = 7

# Rodar
python main.py
# Apenas últimos 7 dias (se houver)
```

### Test 3: Histórico Persistente

```python
# Rodar primeira vez
python main.py  # Processa 100 anúncios

# Rodar segunda vez
python main.py  # Deve processar 0 com mode="new"

# Validar: seen_listings.json contém 100 entradas
import json
with open("seen_listings.json") as f:
    seen = json.load(f)
    assert len(seen) == 100  # 100 vistos
```

---

## 📊 Testes de Regressão

### Teste: Anti-Overfiltering

```python
# Scenario: Filtros muito restritivos
# config.py
MIN_PRICE = 200000
MAX_PRICE = 250000  # Range muito apertado

python main.py

# Validar: bot.log deve conter ALERTA
# ⚠️ AVISO: Pipeline muito restritivo!
```

### Teste: Taxa de Extração

Validar que:
- ✅ Taxa preço > 90%
- ✅ Taxa área > 90%
- ✅ Taxa localização > 80%
- ✅ Taxa transporte > 70%

(Logs mostram isso)

### Teste: Rejeição Automática vs Revisão

```python
# Cenário 1: Preço HIGH confidence, fora range
# → REJEITADO automaticamente

# Cenário 2: Preço LOW confidence, fora range  
# → PARA REVISÃO (anti-overfiltering!)

# Validar em bot.log que rejeições têm motivos claros
# Validar em needs_review.md que têm explicações
```

---

## 🔍 Testes Manuais

### Manual Test 1: Ler Output Markdown

```bash
cat output/top_opportunities.md
```

**Validar**:
- ✅ Anúncios têm score calculado
- ✅ Score breakdown é claro
- ✅ Cada motivo é explicado
- ✅ Links funcionam

### Manual Test 2: Analisar CSV em Excel

```bash
# Abrir em Excel
output/all_scored.csv
```

**Validar**:
- ✅ Colunas: status, score, price, area, location, transport, etc
- ✅ Pode ordenar por score
- ✅ Pode filtrar por status
- ✅ Pode analisar transportes

### Manual Test 3: Verificar Logs

```bash
tail -100 bot.log
```

**Validar**:
- ✅ 5 phases visíveis
- ✅ Estatísticas por stage
- ✅ Nenhum erro crítico
- ✅ Timestamps corretos

---

## 🚨 Edge Cases a Testar

### Edge Case 1: Anúncio sem preço
```python
raw_item = {
    "title": "T2 Porto",
    "price": "",  # Vazio
    "area": "95 m²",
    "location": "Porto",
    "description": ""
}
# Deve normalizar com price=None e confidence=low
# Deve marcar para review (não rejeitar)
```

### Edge Case 2: Localização errada
```python
raw_item = {
    "location": "Londres",  # Fora de Portugal!
    # Deve detectar que está fora da AMP
    # Deve rejeitar (ou marcar para review se confidence baixa)
}
```

### Edge Case 3: Descrição vaga de transporte
```python
raw_item = {
    "title": "T2",
    "description": "Perto de transporte"  # Vago!
    # Deve marcar como confidence=low
    # Deve marcar para review
}
```

### Edge Case 4: Preço < Área (SWAP)
```python
raw_item = {
    "price": "50",  # Preço baixo
    "area": "5000",  # Área alta
    # Deve detectar SWAP
    # Deve marcar normalization_issue
    # Não deve rejeitar automaticamente
}
```

### Edge Case 5: Duplicata
```python
# Mesmo link aparece 2x
# Modo new: segundo deve ser ignorado
# Modo window: ambos processados (dentro do window)
```

---

## 📈 Validação de Performance

### Teste: Velocidade

```python
import time

start = time.time()
python main.py
end = time.time()

duration = end - start
print(f"Processou em {duration:.2f}s")
# Esperado: < 1 min para 500 anúncios
```

### Teste: Memória

```bash
# Monitorar uso de memória
python -m memory_profiler main.py

# Esperado: < 500MB para 500 anúncios
```

---

## ✅ Checklist Final

Antes de usar em produção:

- [ ] Todos os testes de unidade passam
- [ ] Pipeline completo executa sem erros
- [ ] Outputs são gerados corretamente
- [ ] Logs têm informação útil
- [ ] Anti-overfiltering funciona (alguns em review)
- [ ] Score é consistente
- [ ] Taxa de extração > 90%
- [ ] config.py configurado corretamente
- [ ] .env configurado (se usar notificações)

---

## 🐛 Debugging

Se encontrar bugs:

1. **Verificar `bot.log`** para mensagens de erro
2. **Validar `filter_debug.json`** (se existir)
3. **Rodar test específico** do agente com dados debug
4. **Adicionar prints** no agente suspeito
5. **Revisar output** em `output/rejected.log`

---

## 📞 Suporte Rápido

| Sintoma | Solução |
|---------|---------|
| 0 aprovados | Ver bot.log, revisar config.py |
| Erro de import | `pip install -r requirements.txt` |
| bot.log vazio | Verificar permissões de arquivo |
| CSV vazio | Verificar se houve rejeitados/review |

---

**Testes Completos ✅**

Sistema pronto para validação!
