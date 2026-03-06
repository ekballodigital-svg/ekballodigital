from flask import Flask, request, render_template, jsonify
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "ekballo_verify_token"

WHATSAPP_TOKEN ="EAA1ZCGcCmLbIBQ8AKgD5a3NgK0kRHfvWVNNvRxvMd2ZC3f0yEO6BZC9jGYYSwONK7ztmFx7ksXTrgMSrf3WwXMPBTuZAQGNMYOvFRfI3umz7V0ZAzfOUdU85rOwZCAWn5K6FzEEL8I9eZCsXTtL9skbBLh8E1jnzOR11nRXZCSdLpT3lfROqMoKwLY1TAG1Vp4uVJKTyx3ZCLPWoJA8xKBE6rDGPd8JnCyUpawQGYxR5jdnHqnfga5nU6RmUA6tUhoJHdqs2D8GKZA2h1UzWjISROeVGVZA"
PHONE_NUMBER_ID ="872291475977200"

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


# ENVIO DE TEMPLATE
@app.route("/send-template", methods=["POST"])
def send_template():

    data = request.json
    numero = data.get("numero")
    template = data.get("template")

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
