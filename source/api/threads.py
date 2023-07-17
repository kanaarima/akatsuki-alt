from threading import Thread


class WThread(Thread):
    def init(self):
        self.sleeping = True
        self.start()
