from threading import Thread
import matplotlib
import requests
import time
import json
import gzip

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class WThread(Thread):
    def init(self):
        self.sleeping = True
        self.start()


class SimpleLock:
    def __init__(self) -> None:
        self.blocked = False

    def block(self):
        self.blocked = True

    def unblock(self):
        self.blocked = False

    def wait(self):
        while self.blocked:
            time.sleep(0.2)


plot_lock = SimpleLock()


def send_string_list(url, channel_id, title, content):
    strings = list()
    string = f"```{title}\n"
    for str in content:
        if len(string) + len(str) >= 1900:
            string += "```"
            strings.append(string)
            string = f"```"
        string += str + "\n"
    string += "```"
    strings.append(string)
    for str in strings:
        requests.post(
            url,
            json={"channel_id": int(channel_id), "message": str},
            headers={"Content-Type": "application/json"},
        )
        time.sleep(2)


def load_json_gzip(filepath):
    with gzip.open(filepath, "r") as fin:
        return json.loads(fin.read().decode("utf-8"))


def save_json_gzip(data, filepath):
    with gzip.open(filepath, "w") as fout:
        fout.write(json.dumps(data).encode("utf-8"))


def basic_graph(x, y, x_name, y_name, title):
    plot_lock.wait()  # Is plot lock really needed?
    plot_lock.block()
    try:
        plt.plot(x, y)
        plt.xlabel(x_name)
        plt.ylabel(y_name)
        plt.title(title)
        plt.savefig("test.png")
        plt.clf()
    except:
        pass  # TODO: exception logging
    plot_lock.unblock()
