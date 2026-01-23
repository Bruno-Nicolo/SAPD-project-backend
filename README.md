# Analisi dei Requisiti: Progetto EcoFashion Scorecard

Il presente documento definisce i requisiti funzionali e non funzionali (FURPS+) del sistema EcoFashion Scorecard, con l'obiettivo di fornire una solida base per una progettazione orientata ai design patterns e ai principi SOLID. In questa repo verrà implementato solo il backend del progetto. Il frontend verrà implementato separatamente e chiamerà le API REST esposte da questo backend.

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

### F4. Normalizzazione Dati Supply-Chain (Data Integration)

- Il sistema deve interfacciarsi con provider di dati eterogenei (API REST di partner, database legacy di audit, file CSV di fornitori).
- La logica di business deve interagire con un'interfaccia di accesso ai dati unificata, ignorando le complessità di integrazione dei singoli provider.
- **Pattern suggerito:** Facade / Adapter.

### F5. Gestione del Ciclo di Vita della Scorecard (Lifecycle)

- Ogni scorecard deve seguire un workflow definito: Draft -> In Review -> Certified -> Deprecated.
- Il comportamento delle operazioni di modifica e visualizzazione deve variare drasticamente in base allo stato corrente dell'oggetto.
- **Pattern suggerito:** State.

## 2. Usabilità (Usability)

### U1. Configurazione Parametrica dei Pesi

- Gli amministratori devono poter configurare i pesi dei criteri di sostenibilità tramite un'interfaccia dedicata.
- Le variazioni di configurazione devono essere propagate istantaneamente ai moduli di calcolo attivi per garantire consistenza visiva.
- **Pattern suggerito:** Observer.

### U2. Procedura Guidata di Inserimento (Wizard)

- La creazione di un'entità "Prodotto Sostenibile" deve avvenire tramite un processo guidato che separi la validazione dei dati dalla rappresentazione finale dell'oggetto complesso.
- **Pattern suggerito:** Builder.

## 3. Affidabilità (Reliability)

### R1. Stima dei Dati Mancanti (AI Fallback)

- In caso di dati di audit incompleti, il sistema deve delegare a un modulo di "AI Estimation" la generazione di valori verosimili, garantendo la continuità del servizio di scoring.
- Il client non deve essere consapevole se il dato sia reale o stimato sinteticamente all'origine.
- **Pattern suggerito:** Proxy / Chain of Responsibility.

## 4. Prestazioni (Performance)

### P1. Caching dei Risultati Complessi

- Data la natura computazionalmente onerosa dei calcoli ricorsivi e delle chiamate AI, il sistema deve implementare un meccanismo di memorizzazione dei risultati per richieste identiche effettuate in brevi lassi di tempo.
- **Pattern suggerito:** Proxy (Virtual/Caching).

## 5. Manutenibilità (Supportability)

### S1. Estensibilità delle Operazioni (Analysis Tools)

- Deve essere possibile aggiungere nuove analisi sui dati (es. generazione report PDF, audit di conformità legale, export per bilancio sociale) senza modificare le classi dei componenti del prodotto.
- **Pattern suggerito:** Visitor.

### S2. Tracciabilità e Rollback

- Ogni comando che modifica i criteri di scoring deve essere incapsulato per permetterne la tracciabilità (logging) e l'eventuale annullamento (undo).
- **Pattern suggerito:** Command.
