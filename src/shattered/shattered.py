import logging
import time

import stomp


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShatteredListener(stomp.ConnectionListener):
    def __init__(self, app):
        self.app = app

    def on_connected(self, headers, body):
        logger.info("STOMP connection established")
        for destination in self.app.subscriptions:
            self.app.conn.subscribe(destination, 1)

    def on_message(self, headers, body):
        logger.info("STOMP message received")
        destination = headers["destination"]
        for callback in self.app.subscriptions[destination]:
            callback(headers, body, self.app.conn)


class Shattered:
    def __init__(self, **config):
        self.config = config
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 61613)
        self.username = self.config.get("username", "guest")
        self.password = self.config.get("password", "guest")
        self.vhost = self.config.get("vhost", "/")

        self.subscriptions = {}
        self.conn = None
        self.listener = ShatteredListener(self)

    def add_subscription(self, destination, callback):
        if destination not in self.subscriptions:
            self.subscriptions[destination] = []
        self.subscriptions[destination].append(callback)

    def subscribe(self, destination):
        def decorator(callback):
            self.add_subscription(destination, callback)
            return callback

        return decorator

    def _run(self):
        self.conn = stomp.Connection(
            [(self.host, self.port)], vhost=self.vhost, heartbeats=(10000, 10000)
        )
        self.conn.set_listener("shattered", self.listener)
        self.conn.connect(self.username, self.password, wait=True)

    def run(self):
        self._run()
        while True:
            time.sleep(60)
