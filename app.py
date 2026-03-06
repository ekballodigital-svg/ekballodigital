from flask import Flask, request, render_template, jsonify
import requests

app = Flask(__name__)

VERIFY_TOKEN = "ekballo_verify_token"

WHATSAPP_TOKEN = "EAA1ZCGcCmLbIBQZCjLWudv6Rlv01yRrCR4XWIRcOZADqqsZAYVv1OyeUvqBHfWFsLNLb0rz6sSOgdZAfaYE1MWJUrQFied6EPeGBooXowvQMlUyZCS78x0CuB23EOZB5XKlHSlrDkGteq1rbEV1jxj931dOBUBCgApVYlj4wfzarNFnmsZBTx8w8V5654ZBv4IBxSZANujUmD7umD88ylSQjqWBxI1XGTPQUZAmLNlaCebaU3OcPOVFvSVwG19FzvgE2F16W9vOcfKMT4GsmT15nNhiFs84ogZDZD"
PHONE_NUMBER_ID = "872291475977200"
BUSINESS_ACCOUNT_ID = "2314805045708173"

@app.route("/get-templates")
def get_templates():

    url = f"https://graph.facebook.com/v22.0/{BUSINESS_ACCOUNT_ID}/message_templates"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    return jsonify(response.json())


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


# WEBHOOK META
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


# ENVIAR TEMPLATE
@app.route("/send-template", methods=["POST"])
def send_template():

    data = request.json
    numero = data.get("numero")
    template = data.get("template")

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": template,
            "language": {
                "code": "pt_BR"
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    return jsonify(response.json())


@app.route("/create-template-api", methods=["POST"])
def create_template():

    data = request.json

    name = data.get("name")
    language = data.get("language")
    category = data.get("category")
    header = data.get("header")
    message = data.get("message")
    button = data.get("button")

    components = []

    if header:
        components.append({
            "type": "HEADER",
            "format": "TEXT",
            "text": header
        })

    components.append({
        "type": "BODY",
        "text": message
    })

    if button:
        components.append({
            "type": "BUTTONS",
            "buttons":[
                {
                    "type":"URL",
                    "text":"Acessar",
                    "url":button
                }
            ]
        })

    url = f"https://graph.facebook.com/v22.0/{BUSINESS_ACCOUNT_ID}/message_templates"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "language": language,
        "category": category,
        "components": components
    }

    response = requests.post(url, headers=headers, json=payload)

    return jsonify(response.json())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
