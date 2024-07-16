from flask import Flask, request, jsonify
from pyngrok import ngrok
import requests
import sys
import os
import dialogflow
from google.api_core.exceptions import InvalidArgument

app = Flask(__name__)

# Replace the values here.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'private_key.json'

INSTANCE_URL = "https://api.maytapi.com/api"
PRODUCT_ID = ""
PHONE_ID = ""
API_TOKEN = ""
PROJECT_ID = ""
DIALOGFLOW_LANGUAGE_CODE = 'en'
SESSION_ID = "me"

session_client = dialogflow.SessionsClient()
session = session_client.session_path(PROJECT_ID, SESSION_ID)


@app.route("/")
def hello():
    return app.send_static_file("index.html")


def send_response(body):
    print("Request Body", body, file=sys.stdout, flush=True)
    url = INSTANCE_URL + "/" + PRODUCT_ID + "/" + PHONE_ID + "/sendMessage"
    headers = {
        "Content-Type": "application/json",
        "x-maytapi-key": API_TOKEN,
    }
    response = requests.post(url, json=body, headers=headers)
    print("Response", response.json(), file=sys.stdout, flush=True)
    return


def runSample(text="hello"):
    text_input = dialogflow.types.TextInput(
        text=text, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(
            session=session, query_input=query_input)
    except InvalidArgument:
        raise

    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:",
          response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)
    return response


@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json()
    message = json_data["message"]
    conversation = json_data["conversation"]
    _type = message["type"]
    if message["fromMe"]:
        return
    if _type == "text":
        # Handle Messages
        text = message["text"]
        result = runSample(text)
        print("Type:", _type, "Text:", text, file=sys.stdout, flush=True)
        body = {"type": "text", "message": result.query_result.fulfillment_text,
                "to_number": conversation}
        send_response(body)
    else:
        print("Ignored Message Type:", type,  file=sys.stdout, flush=True)
    return jsonify({"success": True}), 200


def setup_webhook():
    if PRODUCT_ID == "" or PHONE_ID == "" or API_TOKEN == "":
        print(
            "You need to change PRODUCT_ID, PHONE_ID and API_TOKEN values in app.py file.", file=sys.stdout, flush=True
        )
        return
    public_url = ngrok.connect(9000)
    public_url = public_url.replace("http", "https", 1)
    print("Public Url " + public_url, file=sys.stdout, flush=True)
    url = INSTANCE_URL + "/" + PRODUCT_ID + "/setWebhook"
    headers = {
        "Content-Type": "application/json",
        "x-maytapi-key": API_TOKEN,
    }
    body = {"webhook": public_url + "/webhook"}
    response = requests.post(url, json=body, headers=headers)
    print(response.json(), file=sys.stdout, flush=True)


# Do not use this method in your production environment
setup_webhook()
