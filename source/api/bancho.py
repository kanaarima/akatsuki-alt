import ossapi

client_id = None
client_secret = None
client = None


def init(secrets):
    global client, client_id, client_secret
    client_id = secrets["osu_client_id"]
    client_secret = secrets["osu_client_secret"]
    client = ossapi.Ossapi(client_id=client_id, client_secret=client_secret)
