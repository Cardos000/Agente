# SCRAPERS - Documentação Técnica

## 🎯 Princípios de Design

Cada scraper é uma **entidade independente** responsável APENAS por:

1. **Navigação e Paginação**: Ir para URLs, clicar em botões "Próxima"
2. **Anti-Bot Evasion**: Delays aleatórios, headers realistas, cookies
3. **Extração RAW**: Dados brutos, SEM interpretação
4. **Logging Detalhado**: O que foi feito, quantos listings, erros

### ❌ O que NÃO fazer nos scrapers

```python
# ❌ NÃO FAZER ISTO:

# Filtrar por preço
if price > 250000:
    skip()  # ERRADO!

# Validar área mínima
if area < 90:
    skip()  # ERRADO!

# Aplicar lógica de negócio
if not has_metro:
    mark_as_rejected()  # ERRADO!

# Interpretar campos
transport = "Confirmado" if metro_found else "Incerto"  # ERRADO!
```

### ✅ O que fazer nos scrapers

```python
# ✅ FAZER ISTO:

# Extrair dados brutos
listing.title = article.inner_text()
listing.price = article.find("span.price").text
listing.area = article.find("span.area").text

# Retornar None se não conseguir
if not found:
    listing.area = None  # Não pular, deixar None

# Logar o que aconteceu
self.logger.info(f"Página 1: 15 listings extraídos")
self.logger.error(f"Falha ao extrair preço, continuando...")
```

---

## 📦 Estrutura Base

### Classe `RawListing`

```python
class RawListing:
    title: Optional[str]         # Título do anúncio
    price: Optional[str]         # Preço como string ("123456" ou "123 456 €")
    area: Optional[str]          # Área como string ("95 m²" ou "95")
    location: Optional[str]      # Localização/Bairro
    description: Optional[str]   # Descrição completa
    link: Optional[str]          # URL do anúncio
    published_date: Optional[str] # Data (se disponível)
    portal: Optional[str]        # Nome do portal (ex: "Imovirtual")
```

**Campos podem ser `None`** - isso é normal e esperado!

### Classe `BaseScraper`

Todos os scrapers herdam de `BaseScraper`:

```python
class MyPortalScraper(BaseScraper):
    
    def __init__(self, headless=True, delay_range=(2, 5)):
        super().__init__(headless, delay_range)
        # Configuração específica do portal
    
    def run(self, page) -> List[RawListing]:
        """IMPLEMENTAR: navegar, extrair, retornar listings"""
        pass
```

---

## 🔌 Métodos Disponíveis no BaseScraper

### `_random_delay()`
```python
# Espera N segundos aleatório entre min e max (configurável)
self._random_delay()  # Espera 2-5s por padrão
```

### `_safe_extract(text, pattern=None)`
```python
# Extração defensiva - retorna None se falhar
price = self._safe_extract("235 000 €", r'(\d+)')  # Retorna "235"
title = self._safe_extract(None)  # Retorna None

# Sem regex
text = self._safe_extract("  hello  ")  # Retorna "hello"
```

### Logging
```python
self.logger.info("Página 1 processada")      # Info
self.logger.warning("Sem próxima página")    # Aviso
self.logger.error("Timeout ao carregar")     # Erro
self.logger.debug("Detail: item skipped")    # Debug
```

### Estatísticas
```python
self.stats["pages_fetched"]  # Contador de páginas
self.stats["listings_found"]  # Total de listings
self.stats["errors"]          # Contador de erros
```

---

## 📋 Exemplo: Implementar um Novo Scraper

```python
from .base import BaseScraper, RawListing
from typing import List
from config import MAX_PRICE

class MyPortalScraper(BaseScraper):
    """Scraper para MyPortal.pt"""
    
    BASE_URL = "https://myportal.pt"
    
    def run(self, page) -> List[RawListing]:
        """Scrape MyPortal com paginação"""
        all_listings = []
        
        try:
            url = self._build_search_url()
            self.logger.info("Iniciando scrape MyPortal")
            
            listings = self._scrape_with_pagination(page, url)
            all_listings.extend(listings)
            self.stats["listings_found"] = len(all_listings)
            
        except Exception as e:
            self.logger.error(f"Erro: {e}")
            self.stats["errors"] += 1
        
        return all_listings
    
    def _build_search_url(self) -> str:
        """Construir URL"""
        return f"{self.BASE_URL}/search?price_max={MAX_PRICE}"
    
    def _scrape_with_pagination(self, page, base_url: str) -> List[RawListing]:
        """Paginar e extrair"""
        listings = []
        page_num = 1
        
        while page_num <= 5:  # Max 5 páginas
            url = f"{base_url}&page={page_num}" if page_num > 1 else base_url
            
            try:
                self.logger.info(f"Página {page_num}")
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                self.stats["pages_fetched"] += 1
                
                self._random_delay()
                
                page_listings = self._extract_listings(page)
                
                if not page_listings:
                    break
                
                listings.extend(page_listings)
                
                if not self._has_next_page(page):
                    break
                
                page_num += 1
                
            except Exception as e:
                self.logger.warning(f"Erro na página {page_num}: {e}")
                self.stats["errors"] += 1
                break
        
        return listings
    
    def _extract_listings(self, page) -> List[RawListing]:
        """Extrair listings da página"""
        listings = []
        
        try:
            items = page.locator('.listing-item').all()
            self.logger.info(f"Total de items: {len(items)}")
            
            for idx, item in enumerate(items):
                try:
                    listing = self._parse_listing(item)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    self.logger.debug(f"Erro ao parsear {idx}: {e}")
                    self.stats["errors"] += 1
                    continue
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair: {e}")
            self.stats["errors"] += 1
        
        return listings
    
    def _parse_listing(self, item) -> RawListing:
        """Parse um item em RawListing"""
        listing = RawListing()
        listing.portal = "MyPortal"
        
        # Link
        try:
            link_el = item.locator('a').first
            if link_el:
                href = link_el.get_attribute('href')
                if href:
                    listing.link = href if href.startswith('http') else f"{self.BASE_URL}{href}"
        except:
            pass
        
        # Título
        try:
            text = item.inner_text()
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                listing.title = lines[0][:200]
        except:
            pass
        
        # Preço
        try:
            text = item.inner_text()
            price_match = re.search(r'(\d[\d\s\.]*)\s*€', text)
            if price_match:
                listing.price = price_match.group(1).replace(' ', '').replace('.', '')
        except:
            pass
        
        # Área
        try:
            text = item.inner_text().lower()
            area_match = re.search(r'(\d+)\s*m²', text)
            if area_match:
                listing.area = f"{area_match.group(1)} m²"
        except:
            pass
        
        return listing
    
    def _has_next_page(self, page) -> bool:
        """Verificar próxima página"""
        try:
            next_btn = page.locator('a:has-text("Próxima")').first
            return next_btn.is_visible()
        except:
            return False
```

---

## 🧪 Testando Scrapers

### Teste Individual

```bash
# Testar Imovirtual
python test_scrapers.py --scraper imovirtual

# Testar com interface (debug)
python test_scrapers.py --scraper idealista --no-headless

# Testar SAPO
python test_scrapers.py --scraper sapo
```

### Teste Completo (Todos)

```bash
# Rodar todos os scrapers via orchestrador
python test_scrapers.py --all

# Resultado: raw_listings.json com todos os dados
```

---

## 🎭 Orchestrador

### Uso Programático

```python
from scraper.orchestrator import ScraperOrchestrator

orchestrator = ScraperOrchestrator()

# Executar todos
all_listings, results = orchestrator.run(headless=True)

# Executar apenas alguns
listings, results = orchestrator.run(
    headless=True,
    scrapers_to_run=["Imovirtual", "Idealista", "OLX"]
)

# Salvar em JSON
orchestrator.save_raw_listings(listings, "raw.json")

# Ver resultados
print(f"Total: {results['total_listings']}")
print(f"Tempo: {results['duration_seconds']:.2f}s")
for portal, stats in results['scrapers'].items():
    print(f"{portal}: {stats['listings_found']} listings")
```

---

## 📊 Saída dos Scrapers

### RawListing.to_dict()

Cada listing retorna um dicionário:

```json
{
  "title": "Apartamento T2 no Porto",
  "price": "150000",
  "area": "95 m²",
  "location": "Porto",
  "description": "Apartamento com cozinha...",
  "link": "https://portal.pt/listing/123",
  "published_date": "há 2 dias",
  "portal": "Imovirtual",
  "scraped_at": "2025-01-28T10:30:45.123456"
}
```

### Arquivo raw_listings.json

Quando salvo via `orchestrator.save_raw_listings()`:

```json
[
  { "title": "...", "price": "...", ... },
  { "title": "...", "price": "...", ... },
  ...
]
```

---

## 🚨 Anti-Bot & Evasion

### Configurado Automaticamente

```python
# Headers aleatórios (fake-useragent)
# Viewports aleatórios
# Delays aleatórios (2-5s por padrão)
# Stealth mode (playwright-stealth)
# Locale PT-PT
# Timezone Europe/Lisbon
```

### Configuração Personalizada

```python
scraper = ImovirtualScraper(
    headless=True,
    delay_range=(3, 8)  # 3-8 segundos entre requisições
)
```

---

## 🔍 Debugging

### Salvando HTML em Erro

Se precisar debugar HTML que não foi parseado:

```python
try:
    item_text = item.inner_text()
except:
    # Salvar HTML para debug
    with open(f"debug_{idx}.html", "w") as f:
        f.write(item.content())
```

### Executar com Interface

```bash
python test_scrapers.py --scraper imovirtual --no-headless
```

Abre browser real para ver o que está acontecendo.

---

## 📈 Monitoramento

### Logs

Todos os scrapers loggam em:
- Console (stdout)
- bot.log (se configurado em logging.basicConfig)

### Formato de Log

```
[ImovirtualScraper] 2025-01-28 10:30:45,123 - INFO - Página 1: 15 listings...
[ImovirtualScraper] 2025-01-28 10:30:50,456 - WARNING - Sem próxima página
[OlxScraper] 2025-01-28 10:35:12,789 - ERROR - Timeout ao carregar URL
```

### Estatísticas Capturadas

Cada scraper rastreia:
- `pages_fetched`: Quantas páginas foram visitadas
- `listings_found`: Total de listings extraídos
- `errors`: Número de erros (não fatal)

---

## ⚠️ Tratamento de Erros

### Filosofia: Continuar Sempre

```python
# ✅ Se uma página falhar, continua na próxima
# ✅ Se um item falhar, continua no próximo
# ✅ Se um portal falhar, tenta o próximo
# ❌ NÃO parar por falta de dados
# ❌ NÃO parar por parse error
```

### Exemplos

```python
try:
    price = parse_price(item)
except:
    price = None  # Continuar, não falhar
    self.logger.debug("Falha ao extrair preço, continuando...")

try:
    page.goto(url, timeout=60000)
except:
    self.logger.warning(f"Timeout em {url}")
    self.stats["errors"] += 1
    continue  # Próxima página
```

---

## 🔗 Integração com Pipeline

Os scrapers são **inputs** para o pipeline de análise:

```
Scrapers (RAW)
    ↓
Normalization Agent (limpeza com confidence)
    ↓
Location Verification (validação de localização)
    ↓
Profile Compatibility (check contra perfil)
    ↓
Scoring Agent (pontuação 0-100)
    ↓
Output Generator (markdown + CSV)
```

**Os scrapers NÃO fazem nenhuma dessas transformações.**

---

## 📝 Checklist para Novo Scraper

- [ ] Herda de `BaseScraper`
- [ ] Implementa `run(page) -> List[RawListing]`
- [ ] Tem método `_build_search_url()`
- [ ] Tem método `_scrape_with_pagination()`
- [ ] Tem método `_extract_listings()`
- [ ] Tem método `_parse_listing()`
- [ ] Tem método `_has_next_page()`
- [ ] Usa `_random_delay()` entre navegações
- [ ] Loga com `self.logger`
- [ ] Incrementa `self.stats`
- [ ] Retorna lista de `RawListing`
- [ ] Nunca filtra por business logic
- [ ] Nunca descard a por missing data
- [ ] Tratamento de erro defensivo (try/except)
- [ ] Testado com `python test_scrapers.py --scraper nome`

---

## 🎯 Performance

### Timeout de Página

```python
page.goto(url, timeout=60000)  # 60 segundos máximo
```

Se portal for muito lento, aumentar:

```python
page.goto(url, timeout=120000)  # 2 minutos
```

### Limite de Páginas

Por padrão, máximo 5 páginas por scraper:

```python
max_pages = 5  # Mudar se necessário
while page_num <= max_pages:
    ...
```

### Delay Entre Requisições

```python
self.delay_range = (2, 5)  # 2-5 segundos padrão

# Para portal sensível:
scraper = ImovirtualScraper(delay_range=(5, 10))
```

---

## 🚀 Deployment

### Uso em Produção

```python
from scraper.orchestrator import ScraperOrchestrator

orchestrator = ScraperOrchestrator()
listings, stats = orchestrator.run(headless=True)

# Processar listings com pipeline
for listing in listings:
    # Passa para Normalization Agent
    pass
```

### Agendamento (Cron)

```bash
# Rodar diariamente às 7:00
0 7 * * * /usr/bin/python3 /path/to/main.py
```

---

**Versão**: 1.0  
**Última Atualização**: 28 Jan 2025  
**Status**: Production Ready
