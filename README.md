# Istruzioni per l'Avvio

## Prerequisiti

Prima di iniziare, assicurati di avere installato:

- **Python 3.11** o superiore
- **pip** (package manager per Python)
- Un account Google Cloud (per le credenziali OAuth2)

## Passaggi per la configurazione

1.  **Crea un ambiente virtuale** (consigliato per isolare le dipendenze):

    ```bash
    python -m venv .venv
    ```

2.  **Attiva l'ambiente virtuale**:
    - **macOS/Linux**:
      ```bash
      source .venv/bin/activate
      ```
    - **Windows**:
      ```bash
      .venv\Scripts\activate
      ```

3.  **Installa le dipendenze**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura le variabili d'ambiente**:
    - Copia il file di esempio:
      ```bash
      cp .env.example .env
      ```
    - Apri il file `.env` e configura i seguenti valori:
      - `GOOGLE_CLIENT_ID`: Il tuo Client ID da Google Cloud Console.
      - `GOOGLE_CLIENT_SECRET`: Il tuo Client Secret da Google Cloud Console.
      - `GOOGLE_REDIRECT_URI`: Solitamente `http://localhost:8000/auth/callback`.
      - `SECRET_KEY`: Una stringa casuale per firmare i token JWT.

## Avvio del Server

Per avviare il server in modalità sviluppo:

```bash
uvicorn app.main:app --reload
```

Il server sarà attivo all'indirizzo: `http://127.0.0.1:8000`

## Avvio con Docker

Se preferisci utilizzare Docker, puoi avviare il singolo container del backend:

1.  **Build dell'immagine**:

    ```bash
    docker build -t sapd-backend .
    ```

2.  **Avvio del container**:
    ```bash
    docker run -p 8000:8000 --env-file .env sapd-backend
    ```

## Documentazione API

Una volta avviato il server, puoi esplorare le API tramite l'interfaccia interattiva di Swagger:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Database

L'applicazione utilizza **SQLite**. Al primo avvio, verrà creato automaticamente il file `ecofashion.db` nella root della cartella backend.
