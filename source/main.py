from api.utils import WThread as Thread
import trackers.clan_lb_tracker as clan_lb_tracker
import trackers.user_stats_tracker as user_stats_tracker
import trackers.user_lb_tracker as user_lb_tracker
import trackers.maps_lb_tracker as maps_lb_tracker
import trackers.score_1s_tracker as score_1s_tracker
import trackers.disc_channel_tracker as disc_channel_tracker

import api.flask2discord as flask2discord
import bot.discord_bot as discord_bot
import bot.map_poster as map_poster

# from threading import Thread
import signal
import time
import json
import sys

stop = False
function_list = (
    clan_lb_tracker.track_clan_leaderboards,
    flask2discord.flask2discord,
    discord_bot.akataltbot,
    user_stats_tracker.user_stats_tracker,
    user_lb_tracker.user_lb_stats_tracker,
    maps_lb_tracker.track_maps,
    score_1s_tracker.score_1s_tracker,
    disc_channel_tracker.track_discord,
    map_poster.mapposterbot,
)
function_class = {
    clan_lb_tracker.track_clan_leaderboards: clan_lb_tracker,
    flask2discord.flask2discord: flask2discord,
    discord_bot.akataltbot: discord_bot,
    user_stats_tracker.user_stats_tracker: user_stats_tracker,
    user_lb_tracker.user_lb_stats_tracker: user_lb_tracker,
    maps_lb_tracker.track_maps: maps_lb_tracker,
    score_1s_tracker.score_1s_tracker: score_1s_tracker,
    disc_channel_tracker.track_discord: disc_channel_tracker,
    map_poster.mapposterbot: map_poster,
}  # No reflections


def handle_signal(*args):
    global stop
    stop = True


def start_thread(function, secrets):
    thread = Thread(target=function, args=(secrets,), daemon=True)
    function_class[function].thread = thread
    thread.init()
    return thread


def main(function, secrets, debug):
    # Handle signals from OS
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    # Start thread
    thread = start_thread(function, secrets)
    # Watch for OS messages.
    while True:
        if stop:
            while True:
                if not thread.sleeping and thread.is_alive():
                    print(f"{function} thread still operating. Waiting 5 seconds.")
                    time.sleep(5)
                    if not debug:
                        continue
                print("Exit.")
                sys.exit()
        time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} function secrets.json")
        exit(-1)
    func = None
    for f in function_list:
        if f.__name__ == sys.argv[1]:
            func = f
            break
    if not func:
        print(f"Invalid function {sys.argv[1]}. Valid functions: {function_list}")
        exit(-1)
    with open(sys.argv[2]) as f:
        secrets = json.load(f)
    debug = False
    if len(sys.argv) > 3:
        if sys.argv[3] == "debug":
            debug = True
    main(func, secrets, debug)
