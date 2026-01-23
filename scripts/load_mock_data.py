import json
import requests
import sys
import os

def load_data(json_path, base_url="http://127.0.0.1:8000"):
    if not os.path.exists(json_path):
        print(f"Errore: Il file {json_path} non esiste.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Caricamento di {len(products)} prodotti in {base_url}...")

    for product in products:
        try:
            response = requests.post(f"{base_url}/products/", json=product)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Prodotto '{product['name']}' creato con successo.")
            else:
                print(f"❌ Errore nella creazione di '{product['name']}': {response.status_code} - {response.text}")
        except requests.exceptions.ConnectionError:
            print("❌ Errore: Impossibile connettersi al server. Assicurati che FastAPI sia in esecuzione su http://127.0.0.1:8000")
            sys.exit(1)

if __name__ == "__main__":
    # Path relativo al file mock_data.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_json = os.path.join(script_dir, "..", "app", "data", "mock_data.json")
    
    json_file = sys.argv[1] if len(sys.argv) > 1 else default_json
    load_data(json_file)
