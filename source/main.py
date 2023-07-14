from api.threads import WThread as Thread
import trackers.clan_lb_tracker as clan_lb_tracker 
#from threading import Thread
import signal
import time
import json
import sys

stop = False
function_list = (clan_lb_tracker.track_clan_leaderboards,)
function_class = {clan_lb_tracker.track_clan_leaderboards: clan_lb_tracker} # No reflections

def handle_signal(*args):
    global stop
    stop = True

def start_thread(function, secrets):
    thread = Thread(target=function, args=(secrets,), daemon=True)
    function_class[function].thread = thread
    thread.init()
    return thread

def main(function, secrets):
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
    main(func, secrets)