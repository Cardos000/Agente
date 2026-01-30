# 📑 INDEX - Real Estate Bot v2.0

## 📖 Guia de Navegação Completo

Bem-vindo ao Real Estate Bot v2.0! Este índice ajuda você a navegar pela documentação e código.

---

## 🚀 Começar Aqui

### Para Usuários Finais (Não técnico)
1. **[README.md](README.md)** - Visão geral e como usar
2. **[QUICKSTART.md](QUICKSTART.md)** - 5 minutos para começar
3. **[config.py](config.py)** - Ajuste seu perfil

### Para Desenvolvedores (Técnico)
1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Design detalhado
2. **[TESTING.md](TESTING.md)** - Como testar
3. **[CHANGELOG.md](CHANGELOG.md)** - O que mudou

---

## 📚 Documentação Completa

| Documento | Público | Conteúdo |
|-----------|---------|----------|
| **README.md** | Geral | Visão geral, quick start, troubleshooting |
| **QUICKSTART.md** | Usuário | Instalação em 5 passos, configuração básica |
| **ARCHITECTURE.md** | Dev | Design multi-agente, APIs, fluxo de dados |
| **TESTING.md** | Dev | Testes de unidade, integração, edge cases |
| **CHANGELOG.md** | Dev | O que foi implementado, validação spec |
| **RESUMO_EXECUTIVO.md** | Executivo | Sumário de 2 páginas do projeto |
| **INDEX.md** | Navegação | Este arquivo |

---

## 🏗️ Código-Fonte

### Módulos Principais

#### `analysis/` - Agentes
| Arquivo | Classe | Linhas | Propósito |
|---------|--------|--------|-----------|
| **normalization.py** | `NormalizationAgent` | 150 | Limpeza defensiva de dados |
| **location_verification.py** | `LocationVerificationAgent` | 200 | Localização + Transporte |
| **profile_compatibility.py** | `ProfileCompatibilityAgent` | 250 | Validação de perfil |
| **ranker.py** | `ScoringAgent` | 150 | Score explicável (0-100) |
| **pipeline.py** | `PipelineOrchestrator` | 350 | Orquestração multi-agente |
| **output.py** | `OutputGenerator` | 450 | Geração de 4 relatórios |

#### Arquivos de Configuração
| Arquivo | Propósito |
|---------|-----------|
| **config.py** | Perfil imobiliário, parâmetros |
| **main.py** | Orquestrador principal |
| **requirements.txt** | Dependências Python |

#### Scraper e Notificações
| Pasta | Propósito |
|-------|-----------|
| **scraper/** | Módulos de scraping (Imovirtual, OLX, etc) |
| **notifier/** | Módulos de notificação (Email, WhatsApp) |
| **analysis/** | Agentes de análise |

---

## 🎯 Fluxo de Uso

### Usuário Final
```
1. Configurar config.py
   ↓
2. python main.py
   ↓
3. Revisar output/top_opportunities.md
   ↓
4. Se necessário, revisar output/needs_review.md
   ↓
5. Clicar links e visitar imóveis
   ↓
6. Ajustar config.py e repetir
```

### Desenvolvedor
```
1. Ler ARCHITECTURE.md
   ↓
2. Estudar agentes em analysis/
   ↓
3. Rodar testes em TESTING.md
   ↓
4. Modificar agentes conforme necessário
   ↓
5. Gerar outputs e validar
```

---

## 📊 Estrutura de Dados

### Item Normalizado
```python
{
    "price": 150000,
    "price_confidence": "high",
    "area": 95,
    "area_confidence": "high",
    "location": "Porto",
    "location_confidence": "high",
    "normalization_issues": []
}
```

### Location Result
```python
{
    "council": "Porto",
    "transport_type": "Metro",
    "station": "Bolhão",
    "confidence": "high"
}
```

### Compatibility Result
```python
{
    "matches_profile": True,
    "recommendation": "approved|needs_review|rejected",
    "confidence_score": 0.8
}
```

### Score Result
```python
{
    "score": 72,  # 0-100
    "score_breakdown": {
        "market_value": 30,
        "features": 15,
        "transport_confidence": 15,
        "regulatory_fit": 12
    }
}
```

---

## 🔧 Como Fazer...

### ...Ajustar Filtros
Editar `config.py`:
```python
MAX_PRICE = 300000  # Aumentar preço máximo
MIN_AREA = 80       # Diminuir área mínima
```

### ...Rodar em Modo Window
Editar `config.py`:
```python
EXECUTION_MODE = "window"
DAYS_WINDOW = 7  # Últimos 7 dias
```

### ...Adicionar Novo Agente
1. Criar classe em `analysis/novo_agente.py`
2. Implementar método `process()` ou similar
3. Integrar em `analysis/pipeline.py`
4. Adicionar testes em `TESTING.md`

### ...Analisar Outputs em Excel
```bash
# Abrir CSV em Excel
output/all_scored.csv

# Ordenar por score ou preço
# Filtrar por status (approved/needs_review/rejected)
```

### ...Debugar um Agente
1. Verificar `bot.log` para erros
2. Adicionar prints no agente
3. Rodar teste isolado em Python REPL
4. Validar output em `output/rejected.log`

---

## 📈 Métricas do Projeto

- **Agentes Implementados**: 5
- **Linhas de Código**: 1600+
- **Linhas de Documentação**: 2000+
- **Arquivos Python**: 8
- **Arquivos Markdown**: 6
- **Outputs por Run**: 4
- **Modes de Execução**: 2
- **Status**: Production Ready ✅

---

## 🚨 Troubleshooting Rápido

| Sintoma | Ver | Solução |
|---------|-----|---------|
| 0 aprovados | bot.log | Filtros muito restritivos |
| Erro de import | terminal | `pip install -r requirements.txt` |
| Outputs vazios | bot.log | Sem anúncios processados |
| Muitos em review | needs_review.md | Normal! Revise manualmente |

---

## 📞 Referência Rápida de Arquivos

### Configuração
- `config.py` - Perfil + parâmetros
- `.env` - Credenciais (opcional)

### Execução
- `main.py` - Rodar bot
- `requirements.txt` - Dependências

### Código-Fonte
- `analysis/normalization.py` - Normalização
- `analysis/location_verification.py` - Localização
- `analysis/profile_compatibility.py` - Validação
- `analysis/ranker.py` - Scoring
- `analysis/pipeline.py` - Orquestração
- `analysis/output.py` - Outputs

### Documentação
- `README.md` - Visão geral
- `QUICKSTART.md` - Começo rápido
- `ARCHITECTURE.md` - Design técnico
- `TESTING.md` - Testes
- `CHANGELOG.md` - Histórico

### Outputs (Gerados)
- `output/top_opportunities.md` - Aprovados
- `output/needs_review.md` - Incertos
- `output/rejected.log` - Rejeitados
- `output/all_scored.csv` - Dataset

### Histórico
- `bot.log` - Logs de execução
- `seen_listings.json` - Anúncios já vistos

---

## 🎓 Próximos Passos

### Primeiro Dia
1. Ler [README.md](README.md)
2. Executar `python main.py`
3. Revisar outputs

### Primeira Semana
1. Ajustar `config.py`
2. Visitar anúncios aprovados
3. Ler [ARCHITECTURE.md](ARCHITECTURE.md)

### Melhorias Futuras
1. Adicionar nova estação de transporte
2. Integrar com API de geolocalização
3. Machine Learning para anomalias
4. Dashboard interativo

---

## 📖 Leitura Recomendada por Perfil

### 👤 Usuário Final (Não técnico)
1. [README.md](README.md) - 10 min
2. [QUICKSTART.md](QUICKSTART.md) - 5 min
3. Rodar bot e explorar outputs

### 👨‍💻 Desenvolvedor (Técnico)
1. [ARCHITECTURE.md](ARCHITECTURE.md) - 30 min
2. [TESTING.md](TESTING.md) - 20 min
3. Estudar `analysis/*.py` - 1 hora
4. Fazer modificações conforme necessário

### 📊 Gerente/Executivo
1. [RESUMO_EXECUTIVO.md](RESUMO_EXECUTIVO.md) - 10 min
2. Este arquivo (INDEX.md) - 5 min
3. [README.md](README.md) - 10 min

---

## ✅ Checklist de Setup

- [ ] Instalar dependências: `pip install -r requirements.txt`
- [ ] Configurar perfil em `config.py`
- [ ] Configurar `.env` (opcional)
- [ ] Rodar: `python main.py`
- [ ] Revisar `output/top_opportunities.md`
- [ ] Ler [ARCHITECTURE.md](ARCHITECTURE.md) se developer

---

## 🎯 Filosofia do Projeto

> "É preferível mostrar anúncios a mais do que perder uma oportunidade"

- ✅ Conservador a **rejeitar**
- ✅ Agressivo a **explicar**
- ✅ Nunca elimina por **dúvida**
- ✅ Confiança **sempre importa**

---

## 📝 Versão e Licença

**Real Estate Bot v2.0**
- Release: 2026-01-28
- Status: Production Ready
- Implementação: Especificação "PROMPT MESTRE" 100%

---

## 🔗 Links Úteis

| Recurso | Link |
|---------|------|
| Home | [README.md](README.md) |
| Arquitetura | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Quick Start | [QUICKSTART.md](QUICKSTART.md) |
| Testes | [TESTING.md](TESTING.md) |
| Resumo | [RESUMO_EXECUTIVO.md](RESUMO_EXECUTIVO.md) |

---

## 📞 Suporte

Se tiver dúvidas:

1. **Verificar `bot.log`** para erros específicos
2. **Consultar [TESTING.md](TESTING.md)** para validar
3. **Revisar [ARCHITECTURE.md](ARCHITECTURE.md)** para design
4. **Ler código-fonte** em `analysis/`

---

**Índice Completo ✅**

Navegue pela documentação usando os links acima!

---

Última atualização: 2026-01-28
