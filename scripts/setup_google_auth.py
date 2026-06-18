"""
Autoriza Google Calendar OAuth una sola vez y devuelve el JSON de credenciales
que se guarda cifrado en la tabla calendar_integrations de Supabase.

Uso:
    1. Descarga credentials.json desde Google Cloud Console
    2. Colócalo en la raíz del proyecto
    3. Ejecuta: python scripts/setup_google_auth.py
    4. Se abrirá el navegador para autorizar
    5. Copia el JSON impreso al campo credentials_encrypted de tu tenant
"""
import json
from pathlib import Path

CREDENTIALS_FILE = Path("credentials.json")

if not CREDENTIALS_FILE.exists():
    print("ERROR: No se encontró credentials.json en la raíz del proyecto.")
    print("Descárgalo desde: Google Cloud Console → APIs → Credenciales → OAuth 2.0")
    exit(1)

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]

flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
creds = flow.run_local_server(port=0)

credentials_json = json.dumps({
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
})

print("\n✅ Autorización exitosa. Guarda este JSON en Supabase:")
print("   Tabla: calendar_integrations")
print("   Campo: credentials_encrypted (cifrar con FernetCipher antes de insertar)")
print()
print(credentials_json)
