# EcoFashion Scorecard - Documentazione Tecnica

> 📂 **Nota**: La documentazione è stata riorganizzata in una struttura a cartelle più leggibile. Puoi consultare l'indice principale qui: [**docs/INDEX.md**](docs/INDEX.md).

Questa documentazione fornisce una panoramica dettagliata dell'architettura del backend, dei design pattern utilizzati e delle specifiche delle API REST.

## 1. Architettura della Codebase

Il progetto è strutturato seguendo i principi di separazione delle responsabilità e i design pattern del GoF (Gang of Four).

### Struttura dei File

```text
app/
├── api/                    # Definizione degli endpoint FastAPI (Router)
│   ├── auth.py             # Autenticazione (Google OAuth + JWT) [NEW]
│   ├── config.py           # Gestione configurazioni (Observer + Command)
│   ├── products.py         # Gestione prodotti (Composite + Strategy + Decorator + Visitor + SQLite) [UPDATED]
│   ├── scorecards.py       # Ciclo di vita (State)
│   └── supply_chain.py     # Integrazione dati (Facade + Adapter + Proxy + Chain)
├── core/
│   ├── database.py         # Configurazione SQLite e SQLAlchemy [NEW]
│   ├── dependencies.py     # Dependency Injection e Sicurezza [NEW]
│   └── patterns/           # Implementazione pura dei design patterns
│       ├── adapter_facade.py
│       ├── builder.py
│       ├── command.py
│       ├── composite.py
│       ├── decorator.py
│       ├── observer.py
│       ├── proxy_chain.py
│       ├── state.py
│       ├── strategy.py
│       └── visitor.py
├── data/
│   ├── mock_data.json      # Dataset di test in formato JSON [NEW]
│   └── example_products.csv # Template per upload CSV [NEW]
├── models/
│   ├── db_models.py        # Modelli SQLAlchemy (User, Product, Component) [NEW]
│   └── schemas.py          # Modelli Pydantic per validazione input/output [UPDATED]
└── main.py                 # File di ingresso dell'applicazione (Middleware + Lifespan) [UPDATED]
```

## 2. Persistenza Dati e Sicurezza

### Database SQLite

Il sistema utilizza SQlite per la persistenza dei dati. La configurazione è gestita tramite SQLAlchemy in `app/core/database.py`. I modelli ORM sono definiti in `app/models/db_models.py` e includono relazioni tra Utenti, Prodotti e Componenti.

### Autenticazione Google OAuth

L'accesso è protetto tramite Google OAuth2.

- Il flusso di login avviene tramite `/auth/google`.
- Dopo il successo, il sistema rilascia un **JWT (JSON Web Token)**.
- Ogni risorsa (Prodotto, Scorecard) è associata a un utente specifico (`user_id`).

## 3. Design Patterns Utilizzati

Gestisce la struttura gerarchica dei prodotti. Un prodotto può essere un `SimpleComponent` (foglia) o un `CompositeProduct` (contenitore).
**Integrazione DB**: I dati salvati su SQLite vengono mappati dinamicamente nella struttura Composite a runtime.
**Aggregazione Dati**: Il Composite aggrega i fattori di impatto dai figli:

- **Somma**: Energia, Acqua, Rifiuti.
- **Media Ponderata (sul peso)**: Riciclabilità, Contenuto Riciclato.

Permette di cambiare l'algoritmo di calcolo della sostenibilità a runtime:

- **HiggIndexStrategy**: Calcola un punteggio (0-100) basato sull'impatto ambientale normalizzato.
  - _Formula:_ `Score = 100 - (Energy*0.5 + Water*0.01 + Waste*10.0)` (normalizzato per kg).
- **CarbonFootprintStrategy**: Calcola l'impatto di CO2 stimato.
  - _Formula:_ `Score = 100 - (Energy * 0.15) * 3.0` (normalizzato per kg, assumendo 0.15kg CO2/MJ).
- **CircularEconomyStrategy**: Valuta la circolarità.
  - _Formula:_ `Score = Recyclability * 60 + RecycledContent * 40` (punteggio 0-100).
- **CustomStrategy**: Permette all'utente di definire pesi personalizzati.
  - _Formula:_ `Score = 100 - (ImpattoPesato) + (BonusPesato)`.

### F3. Decorator (`decorator.py`)

Aggiunge "badges" (es. `FairTradeBadge`, `VeganBadge`) ai prodotti. I badge decorano l'oggetto Composite influenzandone lo score.

### F4. Facade & Adapter (`adapter_facade.py`)

La `SupplyChainFacade` unifica l'accesso a fonti dati eterogenee tramite `Adapter` specifici.

### F5. State (`state.py`)

Gestisce il workflow della scorecard: `Draft` -> `In Review` -> `Certified` -> `Deprecated`.

### U1. Observer (`observer.py`)

Propaga le variazioni dei pesi di configurazione ai moduli attivi.

### U2. Builder (`builder.py`)

Guida la creazione passo-passo di oggetti complessi.

### R1. Chain of Responsibility (`proxy_chain.py`)

Gestisce il fallback su stime AI in caso di dati supply-chain mancanti.

### P1. Proxy (`proxy_chain.py`)

Implementa il caching dei risultati computazionalmente onerosi.

### S1. Visitor (`visitor.py`)

Aggiunge nuove analisi (PDF, Compliance) senza modificare le classi dei prodotti.

### S2. Command (`command.py`)

Incapsula le modifiche ai pesi permettendo Undo/Redo.

## 4. Specifiche API

Ogni richiesta che richiede autenticazione deve includere l'header HTTP `Authorization: Bearer <JWT_TOKEN>`.

### 4.1 Auth API (`/auth`)

Gestisce l'autenticazione tramite Google OAuth 2.0.

- **`GET /auth/google`**
  - **Descrizione**: Inizia il flusso di login reindirizzando a Google.
  - **Risposta**: Reindirizzamento (302) a Google.

- **`GET /auth/callback`**
  - **Descrizione**: Endpoint di callback per Google OAuth.
  - **Risposta**: Reindirizzamento al frontend con il JWT token nell'URL (`?token=...`).

- **`GET /auth/me`**
  - **Descrizione**: Restituisce le informazioni dell'utente autenticato.
  - **Risposta (`UserResponse`)**:
    - `id` (int): ID univoco dell'utente.
    - `email` (string): Email dell'utente.
    - `name` (string): Nome completo dell'utente.

---

### 4.2 Products API (`/products`)

Gestione del catalogo prodotti e analisi di sostenibilità.

- **`GET /products/`**
  - **Descrizione**: Lista tutti i prodotti creati dall'utente corrente.
  - **Risposta**: Una lista di oggetti `ProductResponse`.

- **`POST /products/`**
  - **Descrizione**: Crea un nuovo prodotto complesso.
  - **Body (`ProductCreate`)**:
    - `name` (string): Nome del prodotto.
    - `components` (list[`ComponentCreate`]): Lista di componenti base.
      - `name` (string): Nome del componente.
      - `material` (string): Materiale. Vedi [Materiali Supportati](#materiali-supportati).
      - `weight_kg` (float): Peso in **chilogrammi**.
      - `energy_consumption_mj` (float, opzionale): Consumo energetico in MJ.
      - `water_usage_liters` (float, opzionale): Consumo idrico in litri.
      - `waste_generation_kg` (float, opzionale): Rifiuti prodotti in kg.
      - `recyclability_score` (float, opzionale): Indice di riciclabilità (0.0 - 1.0).
      - `recycled_content_percentage` (float, opzionale): % di materiale riciclato (0.0 - 1.0).
  - **Risposta (`ProductResponse`)**:
    - `id` (int): ID del prodotto creato.
    - `name` (string): Nome del prodotto.
    - `average_score` (float): **Calcolato alla creazione** come media delle 3 strategie standard.
    - `components` (list[`ComponentResponse`]):
      - `name`, `material`, `weight_kg`, `environmental_impact`.
      - `energy_consumption_mj`, `water_usage_liters`, `waste_generation_kg`, `recyclability_score`, `recycled_content_percentage`.

- **`DELETE /products/{id}`**
  - **Descrizione**: Elimina definitivamente un prodotto e i suoi componenti.
  - **Risposta**: JSON di conferma (`{"message": "Product deleted successfully"}`).

- **`POST /products/upload`**
  - **Descrizione**: Caricamento bulk tramite file CSV.
  - **Request**: `multipart/form-data` con campo `file` (CSV).
  - **Formato CSV**: `product_name, component_name, material, weight_kg`
  - **Nota**: L'impatto ambientale viene calcolato automaticamente dal materiale.

- **`POST /products/{id}/score`**
  - **Descrizione**: Calcola lo score di sostenibilità usando una strategia specifica.
  - **Body (`ScoringRequest`)**:
    - `strategy` (string): Uno tra `higg_index`, `carbon_footprint`, `circular_economy`, `custom`.
    - `custom_weights` (dict, opzionale): Pesi per la strategia `custom` (es. `{"energy": 5.0}`).
  - **Risposta (`ScoreResponse`)**:
    - `strategy` (string): La strategia utilizzata.
    - `score` (float): Il punteggio finale calcolato.

- **`POST /products/{id}/badges`**
  - **Descrizione**: Applica un badge (Decorator) al prodotto per influenzarne lo score.
  - **Body (`BadgeApply`)**:
    - `badge_type` (string): Uno tra `fairtrade`, `vegan`, `oekotex`, `non_compliant`.

- **`GET /products/{id}/report/pdf`** | **`/compliance`** | **`/social`**
  - **Descrizione**: Genera report specifici usando il Visitor pattern.
  - **Risposta**: JSON contenente i dati del report generato.

#### Materiali Supportati

Il sistema calcola automaticamente l'impatto ambientale basandosi sul materiale specificato. I materiali supportati includono:

| Categoria               | Materiali                                                                   | Impatto (kg CO2 eq/kg) |
| ----------------------- | --------------------------------------------------------------------------- | ---------------------- |
| **Fibre Naturali**      | `cotton`, `organic_cotton`, `linen`, `hemp`, `wool`, `silk`                 | 3.5 - 15.0             |
| **Fibre Sintetiche**    | `polyester`, `recycled_polyester`, `nylon`, `acrylic`, `elastane`           | 5.0 - 12.0             |
| **Fibre Rigenerate**    | `viscose`, `lyocell`, `modal`                                               | 4.5 - 7.0              |
| **Pelle e Alternative** | `leather`, `vegan_leather`, `faux_leather`                                  | 8.0 - 17.0             |
| **Altri Materiali**     | `rubber`, `metal`, `plastic`, `recycled_plastic`, `wood`, `bamboo`, `glass` | 2.0 - 15.0             |

Per materiali non riconosciuti, viene applicato un impatto di default di **10.0 kg CO2 eq/kg**.

---

### 4.3 Scorecards API (`/scorecards`)

Gestione del ciclo di vita della certificazione (State Pattern).

- **`POST /scorecards/`**
  - **Body (`ScorecardCreate`)**:
    - `product_name` (string): Nome del prodotto.
    - `score` (float): Score di partenza.
  - **Risposta (`ScorecardResponse`)**:
    - `scorecard_id` (uuid): ID della scorecard.
    - `state` (string): Stato iniziale (sempre `Draft`).

- **`POST /scorecards/{id}/submit-review`** | **`/certify`** | **`/deprecate`** | **`/edit`**
  - **Descrizione**: Avanza o arretra lo stato della scorecard. I passaggi validi sono definiti dallo State Pattern.
  - **Stati possibili (`state`)**:
    - `Draft`: Bozza iniziale (modificabile).
    - `InReview`: In fase di revisione (bloccato o torna a Draft).
    - `Certified`: Certificato ufficialmente (non modificabile).
    - `Deprecated`: Obsoleto (stato finale).

---

### 4.4 Configuration API (`/config`)

Gestione dei pesi globali per i calcoli (Observer + Command Pattern).

- **`GET /config/weights`**
  - **Risposta**:
    - `weights` (dict): Mappa dei pesi correnti (es. `{"material_sustainability": 0.3, ...}`).

- **`PUT /config/weights`**
  - **Body (`WeightUpdate`)**:
    - `weights` (dict[str, float]): Nuovi valori per i criteri (es. `{"carbon_footprint": 0.5}`).
  - **Effetto**: Notifica tutti i moduli di calcolo e salva l'azione per l'`undo`.

- **`POST /config/weights/undo`** / **`redo`**
  - **Descrizione**: Annulla o ripristina l'ultima modifica ai pesi.

- **`GET /config/weights/history`**
  - **Descrizione**: Recupera la cronologia delle modifiche (Command History).

---

### 4.5 Supply Chain API (`/supply-chain`)

Integrazione dati esterni (Facade, Adapter, Proxy, Chain).

- **`GET /supply-chain/supplier/{provider}/{id}`**
  - **Parametri**: `provider` (es. `rest_api`, `legacy_db`), `id` (ID fornitore).
  - **Descrizione**: Recupera dati da sistemi esterni tramite Facade.
  - **Risposta**:
    - `provider` (string): Nome del provider interrogato.
    - `supplier_id` (string): ID del fornitore.
    - `data` (dict): Dati grezzi restituiti dall'adapter.

- **`GET /supply-chain/data/{id}`**
  - **Descrizione**: Recupera dati con fallback automatico. Se il dato non esiste nel DB, viene generata una stima AI (Chain of Responsibility). I risultati sono memorizzati in cache (Proxy).
  - **Risposta**:
    - `supplier_id` (string): ID del fornitore.
    - `supplier_name` (string): Nome del fornitore (o "AI Estimated").
    - `carbon_footprint_kg` (float): Valore dell'impatto (reale o stimato).
    - `source` (string, opzionale): Indica se il dato è `real` o `ai_estimated`.

- **`POST /supply-chain/cache/invalidate`**
  - **Descrizione**: Svuota la cache del Proxy.

## 5. Come Eseguire il Progetto

1. **Setup Ambiente**:
   - Assicurarsi di avere Python 3.11+.
   - Installare le dipendenze: `pip install -e "."`
   - Creare file `.env` partendo da `.env.example` e inserire le credenziali Google OAuth.

2. **Esecuzione**:
   - Avviare il server: `uvicorn app.main:app --reload`
   - Accedere a `http://127.0.0.1:8000/docs`.

3. **Caricamento Dati Mock**:
   - Usare lo script: `python scripts/load_mock_data.py` (richiede server attivo).
   - O caricare il file `app/data/example_products.csv` tramite l'endpoint `/products/upload`.

## 6. Guida all'Input dei Dati

Per ottenere punteggi accurati, è importante inserire i dati ambientali riferiti all'**intero componente** (non per kg, a meno che il componente pesi esattamente 1kg). Il sistema normalizzerà automaticamente i valori in base al peso.

### Range Tipici per Materiali Comuni (Riferimento 1kg di Tessuto)

| Parametro   | Unità    | Cotone        | Poliestere | Viscosa   | Note                            |
| ----------- | -------- | ------------- | ---------- | --------- | ------------------------------- |
| **Energia** | MJ/kg    | 40 - 60       | 100 - 125  | 100 - 130 | Include processamento e tintura |
| **Acqua**   | Litri/kg | 2000 - 10000+ | 50 - 100   | 400 - 600 | Molto alto per cotone irrigato  |
| **Rifiuti** | kg/kg    | 0.1 - 0.5     | 0.05 - 0.2 | 0.2 - 0.5 | Scarti di taglio e produzione   |

### Esempio di Inserimento

Per una T-Shirt di **200g (0.2kg)** in Cotone:

- **Energy**: ~10 MJ (50 MJ/kg \* 0.2)
- **Water**: ~540 L (2700 L/kg \* 0.2)
- **Waste**: ~0.04 kg (0.2 kg/kg \* 0.2)
- **Recyclability**: 1.0 (Alta)
- **Recycled Content**: 0.0 (Vergine)

_Nota: Se i valori inseriti sono 0, lo score risultante per Higg/Carbon sarà 100 (impatto nullo)._
