# Analisi dei Requisiti: Progetto EcoFashion Scorecard

Il presente documento definisce i requisiti funzionali e non funzionali (FURPS+) del sistema EcoFashion Scorecard, con l'obiettivo di fornire una solida base per una progettazione orientata ai design patterns e ai principi SOLID. In questa repo viene implementato il backend del progetto, con persistenza su **database SQLite** e autenticazione integrata.

## 1. Requisiti Funzionali (Functionality)

### F1. Gestione Gerarchica dei Prodotti (Bill of Materials)

- Il sistema deve gestire capi di abbigliamento complessi composti da sub-componenti (es. tessuto, fodera, bottoni).
- Ogni componente deve poter essere valutato individualmente o come parte di un aggregato, permettendo calcoli di impatto ricorsivi.
- **Pattern suggerito:** Composite.

### F2. Motore di Valutazione Multicriterio (Scoring Engine)

- Il sistema deve supportare diversi algoritmi di calcolo della sostenibilità (es. Higg Index, Carbon Footprint Focus, Circular Economy Score).
- Gli utenti devono poter cambiare la strategia di calcolo a runtime per confrontare diversi schemi di rating.
- **Pattern suggerito:** Strategy.

### F3. Arricchimento Dinamico delle Informazioni (Product Tagging)

- Deve essere possibile aggiungere "badges" o certificazioni (es. FairTrade, Vegan, Oeko-Tex) ai prodotti senza alterare la struttura delle classi base o del database.
- Tali badge possono influenzare il calcolo finale dello score aggiungendo bonus o malus.
- **Pattern suggerito:** Decorator.

### F4. Normalizzazione e Importazione Dati (Data Integration)

- Il sistema deve supportare l'importazione massiva di dati tramite **file CSV**.
- Il sistema deve interfacciarsi con provider di dati eterogenei (API REST di partner, database legacy di audit).
- La logica di business deve interagire con un'interfaccia di accesso ai dati unificata.
- **Pattern suggerito:** Facade / Adapter.

### F5. Gestione del Ciclo di Vita della Scorecard (Lifecycle)

- Ogni scorecard deve seguire un workflow definito: Draft -> In Review -> Certified -> Deprecated.
- Il comportamento delle operazioni cambia in base allo stato corrente.
- **Pattern suggerito:** State.

### F6. Sicurezza e Multi-utenza [NEW]

- L'accesso al sistema è protetto tramite **Google OAuth2**.
- Ogni utente ha accesso solo ai propri prodotti e scorecard.
- Il sistema gestisce sessioni sicure tramite JWT (JSON Web Tokens).

## 2. Usabilità (Usability)

### U1. Configurazione Parametrica dei Pesi

- Gli amministratori devono poter configurare i pesi dei criteri di sostenibilità.
- Le variazioni devono essere propagate istantaneamente ai moduli di calcolo attivi.
- **Pattern suggerito:** Observer.

### U2. Procedura Guidata di Inserimento (Wizard)

- La creazione di un'entità "Prodotto Sostenibile" deve avvenire tramite un processo guidato.
- **Pattern suggerito:** Builder.

## 3. Affidabilità (Reliability)

### R1. Stima dei Dati Mancanti (AI Fallback)

- In caso di dati incompleti, il sistema delega a un modulo di "AI Estimation" la generazione di valori verosimili.
- **Pattern suggerito:** Proxy / Chain of Responsibility.

## 4. Prestazioni (Performance)

### P1. Caching dei Risultati Complessi

- Il sistema deve implementare un meccanismo di memorizzazione dei risultati per calcoli onerosi.
- **Pattern suggerito:** Proxy (Virtual/Caching).

## 5. Manutenibilità (Supportability)

### S1. Estensibilità delle Operazioni (Analysis Tools)

- Deve essere possibile aggiungere nuove analisi (es. report PDF, audit legali) senza modificare le classi base.
- **Pattern suggerito:** Visitor.

### S2. Tracciabilità e Rollback

- Ogni comando di modifica deve essere incapsulato per permetterne la tracciabilità e l'annullamento.
- **Pattern suggerito:** Command.

---

## Guide di Installazione e Setup

Per istruzioni dettagliate su come configurare, eseguire e testare il progetto, consulta la [Documentazione Tecnica](DOCUMENTATION.md).
