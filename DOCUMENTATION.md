# EcoFashion Scorecard - Documentazione Tecnica

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

### F1. Composite (`composite.py`)

Gestisce la struttura gerarchica dei prodotti. Un prodotto può essere un `SimpleComponent` (foglia) o un `CompositeProduct` (contenitore). Calcola l'impatto ambientale ricorsivamente.
**Integrazione DB**: I dati salvati su SQLite vengono mappati dinamicamente nella struttura Composite a runtime.

### F2. Strategy (`strategy.py`)

Permette di cambiare l'algoritmo di calcolo della sostenibilità a runtime (`HiggIndexStrategy`, `CarbonFootprintStrategy`, `CircularEconomyStrategy`).

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

### Auth API (`/auth`) [NEW]

- **GET `/auth/google`**: Inizia il login.
- **GET `/auth/callback`**: Riceve il token da Google e rilascia JWT.
- **GET `/auth/me`**: Info utente corrente.

### Products API (`/products`) [UPDATED]

- **GET `/products/`**: Lista i prodotti dell'utente autenticato.
- **POST `/products/upload`**: Crea prodotti in massa tramite file **CSV**.
- **POST `/products/`**: Crea un singolo prodotto complesso.
- **POST `/products/{id}/score`**: Calcola lo score con una strategia.
- **GET `/products/{id}/report/pdf`**: Genera report.

### Altre API

- **`/scorecards`**: Gestione del ciclo di vita via State Pattern.
- **`/config`**: Configurazione pesi via Command e Observer.
- **`/supply-chain`**: Accesso dati via Facade e Proxy.

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
