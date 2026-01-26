# EcoFashion Scorecard - Documentazione Tecnica

> 📂 **Nota**: La documentazione è stata riorganizzata in una struttura a cartelle più leggibile. Puoi consultare l'indice principale qui: [**docs/INDEX.md**](docs/INDEX.md).

Questa documentazione fornisce una panoramica dettagliata dell'architettura del backend, dei design pattern utilizzati e delle specifiche delle API REST.

## 1. Architettura della Codebase

Il progetto è strutturato seguendo i principi di separazione delle responsabilità e i design pattern del GoF (Gang of Four).

### Struttura dei File

```text
app/
├── api/                    # Definizione degli endpoint FastAPI (Router)
│   ├── auth.py             # Autenticazione (Google OAuth + JWT)
│   ├── config.py           # Gestione configurazioni (Observer)
│   └── products.py         # Gestione prodotti (Composite + Strategy + Decorator + Visitor + Adapter)
├── core/
│   ├── config.py           # Variabili d'ambiente e segreti
│   ├── database.py         # Configurazione SQLite e SQLAlchemy
│   ├── dependencies.py     # Dependency Injection e Sicurezza JWT
│   └── patterns/           # Implementazione pura dei design patterns
│       ├── adapter_facade.py   # Adapter per parsing file upload
│       ├── composite.py        # Gerarchia prodotti
│       ├── decorator.py        # Badge certificazioni
│       ├── observer.py         # Notifiche config
│       ├── strategy.py         # Algoritmi di scoring
│       └── visitor.py          # Generazione report
├── data/
│   └── example_products.csv # Template per upload CSV
├── models/
│   ├── db_models.py        # Modelli SQLAlchemy (User, Product, Component)
│   └── schemas.py          # Modelli Pydantic per validazione input/output
└── main.py                 # File di ingresso dell'applicazione (Middleware + Lifespan)
```

## 2. Persistenza Dati e Sicurezza

### Database SQLite

Il sistema utilizza SQLite per la persistenza dei dati. La configurazione è gestita tramite SQLAlchemy in `app/core/database.py`. I modelli ORM sono definiti in `app/models/db_models.py` e includono relazioni tra Utenti, Prodotti e Componenti.

### Autenticazione Google OAuth

L'accesso è protetto tramite Google OAuth2.

- Il flusso di login avviene tramite `/auth/google`.
- Dopo il successo, il sistema rilascia un **JWT (JSON Web Token)**.
- Ogni risorsa (Prodotto) è associata a un utente specifico (`user_id`).

## 3. Design Patterns Utilizzati

Il sistema implementa **6 pattern GoF**:

### F1. Composite (`composite.py`)

Gestisce la struttura gerarchica dei prodotti. Un prodotto può essere un `SimpleComponent` (foglia) o un `CompositeProduct` (contenitore).

**Integrazione DB**: I dati salvati su SQLite vengono mappati dinamicamente nella struttura Composite a runtime.

**Aggregazione Dati**: Il Composite aggrega i fattori di impatto dai figli:

- **Somma**: Energia, Acqua, Rifiuti.
- **Media Ponderata (sul peso)**: Riciclabilità, Contenuto Riciclato.

### F2. Strategy (`strategy.py`)

Permette di cambiare l'algoritmo di calcolo della sostenibilità a runtime:

- **HiggIndexStrategy**: Calcola un punteggio (0-100) basato sull'impatto ambientale normalizzato.
  - Considera CO2 (45%), Acqua (30%), Energia (25%).
- **CarbonFootprintStrategy**: Calcola l'impatto di CO2 stimato.
  - Parte da 100 e penalizza in base ai kg CO2/kg prodotto.
- **CircularEconomyStrategy**: Valuta la circolarità.
  - Valuta contenuto riciclato (50%) e riciclabilità (50%), con penalità per rifiuti.
- **CustomStrategy**: Permette all'utente di definire pesi personalizzati.

### F3. Decorator (`decorator.py`)

Aggiunge "badges" (es. `FairTradeBadge`, `VeganBadge`) ai prodotti. I badge decorano l'oggetto Composite influenzandone lo score.

**Applicazione**: I badge vengono applicati in fase di creazione del prodotto tramite il campo `badges` in `ProductCreate`.

**Modificatori**:

- `fairtrade`: -5.0 (bonus)
- `vegan`: -3.0 (bonus)
- `oekotex`: -4.0 (bonus)
- `non_compliant`: +10.0 (penale)

### F4. Adapter (`adapter_facade.py`)

Converte l'interfaccia di diverse sorgenti dati (file di input) in un'interfaccia comune per l'import di prodotti.

**Utilizzo**: L'endpoint `/products/upload` usa il pattern Adapter per supportare diversi formati file. Attualmente supportato: CSV.

### F5. Observer (`observer.py`)

Propaga le variazioni dei pesi di configurazione ai moduli attivi. Quando i pesi vengono aggiornati tramite `/config/weights`, tutti i moduli di scoring registrati vengono notificati.

### F6. Visitor (`visitor.py`)

Aggiunge nuove analisi (PDF Report) senza modificare le classi dei prodotti. Il `PdfReportVisitor` attraversa l'albero del prodotto e raccoglie i dati per generare il report PDF.

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
    - `badges` (list[string], opzionale): Lista di badge da applicare al prodotto (Decorator Pattern). Valori: `fairtrade`, `vegan`, `oekotex`, `non_compliant`. I badge influenzano il calcolo dell'`average_score`.
  - **Risposta (`ProductResponse`)**:
    - `id` (int): ID del prodotto creato.
    - `name` (string): Nome del prodotto.
    - `average_score` (float): **Calcolato alla creazione** come media delle 3 strategie standard, **influenzato dai badge applicati**.
    - `components` (list[`ComponentResponse`]):
      - `name`, `material`, `weight_kg`, `environmental_impact`.
      - `energy_consumption_mj`, `water_usage_liters`, `waste_generation_kg`, `recyclability_score`, `recycled_content_percentage`.

- **`GET /products/{id}`**
  - **Descrizione**: Recupera un singolo prodotto per ID.
  - **Risposta**: Oggetto `ProductResponse`.

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

- **`GET /products/report/pdf`**
  - **Descrizione**: Genera un report PDF di tutti i prodotti dell'utente usando il Visitor pattern.
  - **Risposta**: File PDF binario con header `Content-Disposition: attachment`.

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

### 4.3 Configuration API (`/config`)

Gestione dei pesi globali per i calcoli (Observer Pattern).

- **`GET /config/weights`**
  - **Risposta**:
    - `weights` (dict): Mappa dei pesi correnti (es. `{"material_sustainability": 0.3, ...}`).

- **`PUT /config/weights`**
  - **Body (`WeightUpdate`)**:
    - `weights` (dict[str, float]): Nuovi valori per i criteri (es. `{"carbon_footprint": 0.5}`).
  - **Effetto**: Notifica tutti i moduli di calcolo tramite Observer pattern.

---

## 5. Come Eseguire il Progetto

1. **Setup Ambiente**:
   - Assicurarsi di avere Python 3.11+.
   - Installare le dipendenze: `pip install -e "."`
   - Creare file `.env` partendo da `.env.example` e inserire le credenziali Google OAuth.

2. **Esecuzione**:
   - Avviare il server: `uvicorn app.main:app --reload`
   - Accedere a `http://127.0.0.1:8000/docs`.

3. **Caricamento Dati**:
   - Caricare il file `app/data/example_products.csv` tramite l'endpoint `/products/upload`.

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
