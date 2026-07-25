from collections import defaultdict


class EventEmitter:
    def __init__(self):
        self._listeners = defaultdict(list)

    def on(self, event, callback):
        self._listeners[event].append(callback)

    def off(self, event, callback):
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def emit(self, event, data=None):
        for cb in list(self._listeners.get(event, [])):
            cb(data)
