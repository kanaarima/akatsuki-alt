import matplotlib
import time

matplotlib.use("Agg")
import matplotlib.pyplot as plt

blocked = False


def basic_graph(x, y, x_name, y_name, title):
    global blocked
    while blocked:
        time.sleep(1)
    blocked = True
    plt.plot(x, y)
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.title(title)
    plt.savefig("test.png")
    plt.clf()
    blocked = False
