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


def list_to_string(list):
    res = ""
    for str in list:
        res += f"{str}\n"
    return res


def wrap_horizontally(cols, wraps=3):
    strings = list()
    max_length = 0
    for col in cols:
        for str in col:
            max_length = max(max_length, len(str))
    max_length += 1
    current = list()
    i = 0
    for col in cols:
        i += 1
        if i > wraps:
            strings.append(f"{list_to_string(current)}\n")
            current = list()
            i = 1
        if current:
            x = 0
            for row in col:
                current[x] += f"{row: <{max_length}}"  # add padding
                x += 1
        else:
            for row in col:
                current.append(f"{row: <{max_length}}")
    if current:
        strings.append(f"{list_to_string(current)}\n")
    result = list()
    for row in strings:
        if result:
            if len(result[-1] + row) < 1950:
                result[-1] = f"{result[-1]}{row}"
                continue
        result.append(row)
    return result


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


NoMod = 0
NoFail = 1
Easy = 2
TouchDevice = 4
Hidden = 8
HardRock = 16
SuddenDeath = 32
DoubleTime = 64
Relax = 128
HalfTime = 256
Nightcore = 512
Flashlight = 1024
SpunOut = 4096


def get_mods(magic_number):
    mods = list()
    if magic_number & SpunOut:
        mods.append("SO")
    if magic_number & Flashlight:
        mods.append("FL")
    if magic_number & Nightcore:
        mods.append("NC")
    if magic_number & HalfTime:
        mods.append("HT")
    if magic_number & Relax:
        mods.append("RX")
    if magic_number & DoubleTime:
        mods.append("DT")
    if magic_number & SuddenDeath:
        mods.append("SD")
    if magic_number & HardRock:
        mods.append("HR")
    if magic_number & Hidden:
        mods.append("HD")
    if magic_number & TouchDevice:
        mods.append("TD")
    if magic_number & Easy:
        mods.append("EZ")
    if magic_number & NoFail:
        mods.append("NF")
    return mods
