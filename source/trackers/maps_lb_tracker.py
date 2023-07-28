import api.utils as utils
import traceback
import time

thread = None


def track_maps(secrets):
    while True:
        try:
            thread.sleeping = True
            time.sleep(30)
        except Exception as e:
            print(e)
            if "error_channel" in secrets:
                utils.send_string_list(
                    f'http://{secrets["flask2discord_host"]}:{secrets["flask2discord_port"]}/send_message',
                    secrets["error_channel"],
                    f"Error in {__name__}",
                    (e.__class__.__name__, str(e), traceback.format_exc()),
                )
            time.sleep(10)
