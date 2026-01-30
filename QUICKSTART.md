# 🚀 QUICKSTART - Real Estate Bot v2

## ⚡ Instalação Rápida

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar `.env` (se usar Email/WhatsApp)
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha
EMAIL_RECIPIENT=destinatario@gmail.com

WHATSAPP_NUMBER=+351912345678
WHATSAPP_API_KEY=sua_key
```

### 3. Rodar Bot
```bash
python main.py
```

---

## 📁 Estrutura de Saída

```
output/
├── top_opportunities.md    ← 👉 LEIA ISTO PRIMEIRO
├── needs_review.md        ← Revise manualmente
├── rejected.log           ← Para auditoria
└── all_scored.csv         ← Análise detalhada

bot.log                     ← Logs de execução
seen_listings.json          ← Histórico
```

---

## ⚙️ Configuração Rápida (`config.py`)

```python
# PREÇO (€)
MIN_PRICE = 60000
MAX_PRICE = 250000

# TIPOLOGIA
MIN_TYPOLOGY = "T2"
MIN_AREA = 90  # m²

# MODO DE EXECUÇÃO
EXECUTION_MODE = "new"  # ou "window"
DAYS_WINDOW = 7  # Se usar "window"
```

---

## 🎯 Seu Perfil Padrão

- **Tipologia**: T2 ou superior
- **Área**: 90+ m²
- **Preço**: 60-250k €
- **Localização**: Área Metropolitana do Porto
  - Com acesso a **Comboio direto (Campanhã)**
  - OU **Estação de Metro próxima**

---

## 📊 Entender os Outputs

### ✅ `top_opportunities.md`
Anúncios COM BOA NOTA (score ≥40)
- Mostram score breakdown (porquê são bons)
- Links diretos
- **Próximo passo**: Clicar e visitar

### ⚠️ `needs_review.md`
Anúncios INCERTOS (informação faltante)
- Não foram rejeitados (pode haver oportunidade!)
- Mostram o que é incerto
- **Próximo passo**: Você decide (aceitar/rejeitar)

### ❌ `rejected.log`
Anúncios FORA DO PERFIL
- Mostram motivo específico de rejeição
- Para saber o que foi filtrado

### 📊 `all_scored.csv`
Todos os dados em Excel format
- Filtrar/ordenar conforme quiser
- Fazer análises adicionais

---

## 🔍 Ler os Logs

```bash
tail -f bot.log
```

Procure por:
- `✅ Boas oportunidades: X` (quantas boas opções)
- `⚠️ Para revisão: X` (incertos)
- `❌ Rejeitados: X` (eliminados)

---

## 🛡️ Princípio Chave

**Preferimos mostrar a mais do que perder uma oportunidade.**

Se há dúvida → Vai para "needs_review"
Se há certeza que não cumpre → Apenas então vai para "rejected"

---

## 💡 Dicas

### Muitos para revisão?
- Talvez a descrição de transporte é vaga no portal
- Considere aceitar alguns (pode valer a pena visitar)

### Poucos aprovados?
- Filtros podem estar muito restritivos
- Revise `config.py` (aumentar preço máx, diminuir área mín, etc)

### Quero analisar X anúncios novamente?
```python
# config.py
EXECUTION_MODE = "window"
DAYS_WINDOW = 7  # Últimos 7 dias
```

---

## 🚨 Erros Comuns

| Erro | Solução |
|------|---------|
| `ModuleNotFoundError: analysis` | Certifique que está na pasta raiz |
| `ImportError: playwright` | `pip install playwright` + `playwright install` |
| 0 aprovados sempre | Revisar filtros em `config.py` |
| Logs em branco | Verificar `bot.log` (arquivo de log) |

---

## 📞 Suporte Rápido

1. Verificar `bot.log` para erro específico
2. Revisar `config.py` para limites
3. Rodar novamente com `EXECUTION_MODE = "window"` para re-análise

---

## 🎓 Próximos Passos

1. **Primeira execução**: `python main.py`
2. **Revisar outputs**: Especialmente `top_opportunities.md`
3. **Ajustar filtros** conforme necessário em `config.py`
4. **Clicar links** e visitar propriedades
5. **Feedback**: Anúncios bons que foram rejeitados? Ajuste config!

---

**Boa sorte! 🏡**
