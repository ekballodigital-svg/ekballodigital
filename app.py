import os
import json
import time
import threading
from pathlib import Path

from flask import Flask, request, render_template, jsonify
import requests

app = Flask(__name__)

# =========================================================
# CONFIGURAÇÃO GERAL
# =========================================================
VERIFY_TOKEN = "ekballo_verify_token"

# Credenciais "padrão" (mantidas por compatibilidade com o sistema atual,
# usadas quando nenhum client_id é informado nas chamadas)
WHATSAPP_TOKEN = "EAAM0ZBQieCesBSFDAZAetJ4cQVpUP7ieUCDvrWHYrQiUKGoQGWXGNnZCrXsy9goEWmNuTT9zTVHntxgTkicWtES4kKnWUzuZAQzWTB9USunJCwYgrSZBOQ3c46YZBbSyz0dkcZBULEdD9R7BlIBdKTFDESMk3Ez1ou5k6OuXuafFZBR9lZCYZCZAmtYXNGCTKWJ1BzERmO0nvMebGFy2NcdSGJjApJowQIFilv6xQPkHtXlbTF4HnZCNugZBkZBnk4j5NRXBZB2W5UZAidfTrMnZAikQg1aFN"
PHONE_NUMBER_ID = "1182475218290035"
BUSINESS_ACCOUNT_ID = "2064448947777009"

# Credenciais do App no Meta for Developers (para o Cadastro Incorporado)
# Encontradas em: App Dashboard > Configurações > Básico
META_APP_ID="3798923280264626"
META_APP_SECRET="c9869a99cb146c37bc76c8921e4c8e2a"

# ID da configuração de "Login do Facebook para Empresas"
# Criado em: App Dashboard > WhatsApp > Configuração da API incorporada
META_CONFIG_ID="917644857399714"

GRAPH_VERSION = "v22.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

# =========================================================
# ARMAZENAMENTO SIMPLES EM JSON (data/clients.json)
# =========================================================
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CLIENTS_FILE = DATA_DIR / "clients.json"
_lock = threading.Lock()


def _load_clients():
    if not CLIENTS_FILE.exists():
        return {"clients": []}
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"clients": []}


def _save_clients(data):
    with _lock:
        with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def get_client(client_id):
    data = _load_clients()
    for c in data["clients"]:
        if c["id"] == client_id:
            return c
    return None


def upsert_client(client):
    data = _load_clients()
    for i, c in enumerate(data["clients"]):
        if c["id"] == client["id"]:
            data["clients"][i] = {**c, **client}
            _save_clients(data)
            return
    data["clients"].append(client)
    _save_clients(data)


def resolve_credentials(client_id):
    """Retorna (access_token, phone_number_id, business_account_id) para um client_id.
    Se não houver client_id ou o cliente não existir, cai para as credenciais padrão."""
    if client_id:
        c = get_client(client_id)
        if c:
            return (
                c.get("access_token", WHATSAPP_TOKEN),
                c.get("phone_number_id", PHONE_NUMBER_ID),
                c.get("waba_id", BUSINESS_ACCOUNT_ID),
            )
    return WHATSAPP_TOKEN, PHONE_NUMBER_ID, BUSINESS_ACCOUNT_ID


# =========================================================
# PÁGINAS
# =========================================================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/send")
def send_page():
    return render_template("send.html")


@app.route("/create-template")
def template_page():
    return render_template("create_template.html")


@app.route("/embedded-signup")
def embedded_signup_page():
    return render_template(
        "embedded_signup.html",
        app_id=META_APP_ID,
        config_id=META_CONFIG_ID,
    )


@app.route("/clients")
def clients_page():
    data = _load_clients()
    return render_template("clients.html", clients=data["clients"])


# =========================================================
# API - LISTAGEM DE CLIENTES (sem expor o access_token)
# =========================================================
@app.route("/api/clients")
def api_clients():
    data = _load_clients()
    safe = [
        {
            "id": c["id"],
            "business_name": c.get("business_name"),
            "display_phone_number": c.get("display_phone_number"),
            "phone_number_id": c.get("phone_number_id"),
            "waba_id": c.get("waba_id"),
            "status": c.get("status"),
            "created_at": c.get("created_at"),
        }
        for c in data["clients"]
    ]
    return jsonify(safe)


# =========================================================
# CADASTRO INCORPORADO (EMBEDDED SIGNUP)
# =========================================================
@app.route("/api/embedded-signup", methods=["POST"])
def api_embedded_signup():
    """
    Recebe do frontend (após o popup do Facebook Login fechar):
      - code: código de autorização (response_type=code)
      - waba_id: ID da WhatsApp Business Account criada/conectada
      - phone_number_id: ID do número conectado
      - pin (opcional): PIN de 6 dígitos para registrar o número (padrão 000000)
    """
    payload = request.json or {}
    code = payload.get("code")
    waba_id = payload.get("waba_id")
    phone_number_id = payload.get("phone_number_id")
    pin = payload.get("pin", "000000")

    if not code or not waba_id or not phone_number_id:
        return jsonify({"error": "code, waba_id e phone_number_id são obrigatórios"}), 400

    if not META_APP_ID or not META_APP_SECRET:
        return jsonify({"error": "META_APP_ID / META_APP_SECRET não configurados no servidor"}), 500

    # 1) Trocar o "code" por um access token
    token_resp = requests.get(
        f"{GRAPH_URL}/oauth/access_token",
        params={
            "client_id": META_APP_ID,
            "client_secret": META_APP_SECRET,
            "code": code,
        },
    )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return jsonify({"error": "Falha ao trocar code por access_token", "details": token_data}), 400

    # 2) Inscrever seu app na WABA do cliente (necessário para receber webhooks)
    sub_resp = requests.post(
        f"{GRAPH_URL}/{waba_id}/subscribed_apps",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # 3) Registrar o número de telefone (necessário para poder enviar mensagens)
    reg_resp = requests.post(
        f"{GRAPH_URL}/{phone_number_id}/register",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"messaging_product": "whatsapp", "pin": pin},
    )

    # 4) Buscar dados cosméticos do número (nome verificado, número em exibição)
    info_resp = requests.get(
        f"{GRAPH_URL}/{phone_number_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"fields": "verified_name,display_phone_number"},
    )
    info = info_resp.json() if info_resp.ok else {}

    client = {
        "id": waba_id,
        "waba_id": waba_id,
        "phone_number_id": phone_number_id,
        "access_token": access_token,
        "business_name": info.get("verified_name", "Sem nome"),
        "display_phone_number": info.get("display_phone_number", ""),
        "status": "active",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    upsert_client(client)

    return jsonify(
        {
            "success": True,
            "client": {k: v for k, v in client.items() if k != "access_token"},
            "subscribe_result": sub_resp.json() if sub_resp.ok else sub_resp.text,
            "register_result": reg_resp.json() if reg_resp.ok else reg_resp.text,
        }
    )


# =========================================================
# WEBHOOK META
# =========================================================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    if request.method == "POST":
        data = request.json
        print("Evento recebido:", data)
        return "EVENT_RECEIVED", 200


# =========================================================
# TEMPLATES / ENVIO (agora aceitam client_id opcional)
# =========================================================
@app.route("/get-templates")
def get_templates():
    client_id = request.args.get("client_id")
    token, _phone_id, business_id = resolve_credentials(client_id)

    url = f"{GRAPH_URL}/{business_id}/message_templates"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return jsonify(response.json())


@app.route("/send-template", methods=["POST"])
def send_template():
    data = request.json
    client_id = data.get("client_id")
    numero = data.get("numero")
    template = data.get("template")

    token, phone_id, _business_id = resolve_credentials(client_id)

    url = f"{GRAPH_URL}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {"name": template, "language": {"code": "en"}},
    }
    response = requests.post(url, headers=headers, json=payload)
    return jsonify(response.json())


@app.route("/create-template-api", methods=["POST"])
def create_template():
    data = request.json
    client_id = data.get("client_id")
    name = data.get("name")
    language = data.get("language")
    category = data.get("category")
    header = data.get("header")
    message = data.get("message")
    button = data.get("button")

    token, _phone_id, business_id = resolve_credentials(client_id)

    components = []
    if header:
        components.append({"type": "HEADER", "format": "TEXT", "text": header})
    components.append({"type": "BODY", "text": message})
    if button:
        components.append(
            {
                "type": "BUTTONS",
                "buttons": [{"type": "URL", "text": "Acessar", "url": button}],
            }
        )

    url = f"{GRAPH_URL}/{business_id}/message_templates"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"name": name, "language": language, "category": category, "components": components}
    response = requests.post(url, headers=headers, json=payload)
    return jsonify(response.json())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
