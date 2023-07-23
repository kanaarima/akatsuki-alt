import api.akatsuki as akatsuki
import api.webhook as wh
import traceback
import datetime
import json
import time
import glob
import os

thread = None


def user_stats_tracker(secrets):
    while True:
        try:
            thread.sleeping = False
            files = glob.glob("data/trackerbot/*.json")
            yesterday = (datetime.datetime.today() -
                         datetime.timedelta(days=1)).date()
            dir = f"data/user_stats/{yesterday}"
            if os.path.exists(dir):
                thread.sleeping = True
                time.sleep(60 * 5)
                continue
            os.makedirs(dir)
            for file in files:
                with open(file) as f:
                    data = json.load(f)
                fetch = akatsuki.grab_stats(data['userid'])
                with open(f"{dir}/{data['userid']}.json", "w") as f:
                    json.dump(fetch, f)
                time.sleep(1)
        except Exception as e:
            print(e)
            if "error_channel" in secrets:
                wh.send_string_list(
                    f'http://{secrets["flask2discord_host"]}:{secrets["flask2discord_port"]}/send_message',
                    secrets["error_channel"], f"Error in {__name__}",
                    (e.__class__.__name__, str(e), traceback.format_exc()))
            time.sleep(10)