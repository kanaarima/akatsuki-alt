import json
import time

thread = None


def user_stats_tracker(secrets):
    while True:
        time.sleep(1)