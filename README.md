# 🏠 Real Estate Bot v2.0

**Sistema inteligente de análise imobiliária com arquitetura multi-agente**

> "É preferível mostrar anúncios a mais do que perder uma boa oportunidade"

---

## 🎯 O Que É

Um agente imobiliário pessoal (não SaaS) que:

1. 🔍 **Scrapa** anúncios de portais (Imovirtual, OLX, etc)
2. 🧹 **Normaliza** dados com confiança
3. 📍 **Verifica** localização e transporte
4. ✅ **Valida** compatibilidade com seu perfil
5. 🎯 **Calcula** score explicável
6. 📤 **Gera** 4 relatórios estruturados

---

## 🚀 Começar Rapidamente

### 1. Instalar
```bash
pip install -r requirements.txt
```

### 2. Rodar
```bash
python main.py
```

### 3. Revisar Outputs
```
output/top_opportunities.md     ← Boas oportunidades
output/needs_review.md          ← Incertos (para revisar)
output/rejected.log             ← Rejeitados
output/all_scored.csv           ← Tudo em CSV
```

---

## 📋 Seu Perfil

Configurado em `config.py`:

```python
# Tipologia
T2+                    # Mínimo T2
Área: ≥90 m²

# Preço
60.000 € - 250.000 €

# Localização
Área Metropolitana do Porto (AMP)
Com:
  • Comboio direto para Campanhã, OU
  • Estação de Metro próxima

# Nice-to-have (bónus, não filtram)
Garagem, Varanda, Terraço
```

---

## 🏗️ Arquitetura Multi-Agente

```
ANÚNCIOS BRUTOS
      ↓
[1] NORMALIZATION      → Limpeza defensiva
[2] LOCATION           → Localização + Transporte
[3] PROFILE            → Validação
[4] SCORING            → Score explicável
[5] PIPELINE           → Orquestração
[6] OUTPUT             → 4 relatórios
      ↓
ANÚNCIOS CATEGORIZADOS
```

---

## 📊 Score Explicável (0-100)

| Componente | Max | O Que Mede |
|-----------|-----|-----------|
| **Valor de Mercado** | 50 | €/m² vs benchmark local |
| **Amenidades** | 20 | Garagem, varanda, terraço |
| **Transporte** | 15 | Confirmado? |
| **Fit Regulatório** | 15 | Requisitos ok? |

---

## 🛡️ Princípio Anti-Overfiltering

**Filosofia central**: Qualquer dúvida = Para revisão manual

```python
# ❌ NUNCA rejeita por ausência
if not confirmed:
    mark_for_review()  # Deixa você decidir

# ✅ SÓ rejeita se HIGH confidence
if confidence == "high" and not meets_requirement:
    reject()
```

---

## 📁 Outputs Detalhados

### 📄 `top_opportunities.md`
Anúncios COM BOA NOTA

```markdown
## ⭐ #1 - T2 em Porto

**Score Total: 75/100**

**Análise:**
- Valor de Mercado: 35/50 (7% abaixo)
- Amenidades: 15/20 (Varanda + Terraço)
- Transporte: 15/15 (Metro confirmado)
- Fit: 10/15 (Maioria confirmada)

**Detalhes:**
- Preço: €150.000
- Área: 95 m²
- Transporte: Metro Bolhão
- [Ver Anúncio](https://...)
```

### ⚠️ `needs_review.md`
Anúncios COM INFORMAÇÃO INCERTA

```markdown
## Preço Incerto (3)

### T2 em Porto
- Preço: Não confirmado
- Localização: Porto
- Por que está aqui: Preço fora do range mas confiança baixa
- [Ver Anúncio](https://...)
```

### ❌ `rejected.log`
Anúncios FORA DO PERFIL

```
## Tipologia < T2 (4)
T1 em Porto - REJEITADO: Tipologia T1 < T2

## Preço > 250k (8)
T3 luxo em Porto - REJEITADO: Preço 350.000€ > máximo
```

### 📊 `all_scored.csv`
Tudo em formato Excel

```
status,score,title,price,area,location,transport,station
approved,75,T2 Porto,150000,95,Porto,Metro,Bolhão
needs_review,45,T2 Maia,180000,90,Maia,Unknown,
rejected,0,T1 Porto,100000,70,Porto,Metro,
```

---

## 🔄 Modos de Execução

### `mode = "new"` (padrão)
Processa apenas anúncios novos
```python
EXECUTION_MODE = "new"
```

### `mode = "window"`
Processa últimos X dias
```python
EXECUTION_MODE = "window"
DAYS_WINDOW = 7
```

---

## 📝 Logging Detalhado

Arquivo `bot.log` mostra:

```
📡 FASE 1: SCRAPING - 142 anúncios coletados
📋 STAGE 1: NORMALIZATION - 98.6% taxa preço
🗺️  STAGE 2: LOCATION - 85% confirmados
✅ STAGE 3: COMPATIBILITY - 5 aprovados, 8 review
🎯 STAGE 4: SCORING - scores calculados
📤 STAGE 5: OUTPUT - 4 arquivos
✅ HISTÓRICO - 142 atualizados

📊 RESUMO:
✅ 5 boas oportunidades
⚠️ 8 para revisão
❌ 129 rejeitados
```

---

## 🔍 Exemplo Real

**Anúncio bruto Imovirtual**:
```
"T2 em Porto - 95 m² - 180.000 € - Perto do Metro Bolhão"
```

**Processamento**:
1. ✅ Normaliza: T2 (confirmado), 95m² (confirmado), 180k€ (confirmado)
2. ✅ Localiza: Porto (confirmado), Metro Bolhão (confirmado)
3. ✅ Valida: T2 ≥ T2 ✓, 95 ≥ 90 ✓, 180k em 60-250k ✓, Metro ✓
4. 🎯 Score: 72/100 (bom preço + transporte + amenidades)
5. 📤 Output: Aprovado com explicação

---

## 💡 Como Usar

### Primeira Vez
1. `python main.py`
2. Abrir `output/top_opportunities.md`
3. Clicar links e visitar imóveis
4. Dar feedback

### Se Poucos Aprovados
1. Revisar `bot.log` para motivos
2. Ajustar `config.py` (preço máx, área mín, etc)
3. Rodar novamente

### Se Muitos em Review
1. Isso é NORMAL! (anti-overfiltering funciona)
2. Revisar manualmente os que interessam
3. Pode aceitar alguns

---

## 📚 Documentação

- **QUICKSTART.md** - 5 minutos para começar
- **ARCHITECTURE.md** - Design técnico completo
- **TESTING.md** - Como testar cada agente
- **CHANGELOG.md** - Histórico de implementação
- **RESUMO_EXECUTIVO.md** - Visão executiva

---

## 🛠️ Configuração

### Editar seu perfil (`config.py`)

```python
# Preço (€)
MIN_PRICE = 60000
MAX_PRICE = 250000

# Área (m²)
MIN_AREA = 90

# Tipologia
MIN_TYPOLOGY = "T2"

# Modo
EXECUTION_MODE = "new"  # ou "window"
DAYS_WINDOW = 7
```

### Email/WhatsApp (opcional, `.env`)

```
SMTP_SERVER=smtp.gmail.com
EMAIL_SENDER=seu@email.com
EMAIL_PASSWORD=sua_senha

WHATSAPP_NUMBER=+351912345678
WHATSAPP_API_KEY=sua_key
```

---

## 📊 Estatísticas

Cada run mostra:
- Total processado
- Boas oportunidades (aprovadas)
- Incertos (para revisão)
- Rejeitados
- Taxa de extração
- Distribuição de transporte

---

## 🚨 Princípio de Ouro

> **Se há dúvida, marca para revisão manual.**

Preferimos você revisar 10 anúncios questionáveis do que perder 1 boa oportunidade.

---

## 📞 Troubleshooting

| Problema | Solução |
|----------|---------|
| 0 aprovados | Ver `bot.log`, revisar `config.py` |
| Erros de import | `pip install -r requirements.txt` |
| Outputs vazios | Verificar se houve anúncios |
| Muitos rejeitados | Aumentar `MAX_PRICE`, diminuir `MIN_AREA` |

---

## ✨ Features

- ✅ Multi-agente (5 agentes especializados)
- ✅ Defensive (nunca elimina por ausência)
- ✅ Explicável (score com breakdown)
- ✅ Transparente (logging detalhado)
- ✅ Persistente (histórico mantido)
- ✅ Flexível (modos new/window)
- ✅ Estruturado (4 outputs diferentes)

---

## 🎓 Próximos Passos

1. **Executar**: `python main.py`
2. **Revisar**: `output/top_opportunities.md`
3. **Visitar**: Clique nos links dos imóveis
4. **Feedback**: Ajuste `config.py` conforme resultado
5. **Repetir**: Execuções periódicas

---

## 📦 Versão

**v2.0.0** - Implementação completa da especificação "PROMPT MESTRE"

- ✅ 5 agentes + 1 orquestrador
- ✅ 4 outputs estruturados
- ✅ Logging detalhado
- ✅ Anti-overfiltering
- ✅ Documentação completa

---

## 🏁 Status

**Production Ready** ✅

Testado e pronto para uso imediato.

---

## 📖 Leia Primeiro

👉 **QUICKSTART.md** para começar em 5 minutos

---

**Boa sorte na busca por casa! 🏡**

Desenvolvido com ❤️ para análise inteligente de imóveis.

*"Preferimos mostrar a mais do que perder uma oportunidade"*
