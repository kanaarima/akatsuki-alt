import api.webhook as wh
import traceback
import json
import time
import glob

thread = None


def user_stats_tracker(secrets):
    while True:
        try:
            time.sleep(1)
        except Exception as e:
            print(e)
            if "error_channel" in secrets:
                wh.send_string_list(
                    f'http://{secrets["flask2discord_host"]}:{secrets["flask2discord_port"]}/send_message',
                    secrets["error_channel"], f"Error in {__name__}",
                    (e.__class__.__name__, str(e), traceback.format_exc()))
            time.sleep(10)