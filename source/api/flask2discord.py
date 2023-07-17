from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
discord_token = ""
baseurl = "https://discord.com/api"
thread = None


def flask2discord(secrets):
    global discord_token
    discord_token = secrets["discord_token"]
    app.run(host=secrets["flask2discord_host"],
            port=secrets["flask2discord_port"],
            debug=False)


@app.route("/send_message", methods=['POST'])
def send_message():
    thread.sleeping = False
    data = request.json
    channel_id = data.get('channel_id')
    message = data.get('message')
    if not channel_id or not message:
        return "Bad request", 400
    text = send_msg(int(channel_id), message)
    thread.sleeping = True
    if text:
        return text, 400
    return "Success"


def send_msg(channel_id, message):
    headers = {
        'Authorization': f"Bot {discord_token}",
        'Content-Type': 'application/json'
    }
    url = f"{baseurl}/channels/{channel_id}/messages"
    r = requests.post(url, json={"content": message}, headers=headers)
    if r.status_code != 200:
        return r.text