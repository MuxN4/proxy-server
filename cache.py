import time
from collections import OrderedDict
from threading import Lock

class Cache:
    def __init__(self, capacity=100, expiration=300):
        self.capacity = capacity
        self.expiration = expiration
        self.cache = OrderedDict()
        self.lock = Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            item = self.cache[key]
            if time.time() - item['timestamp'] > self.expiration:
                del self.cache[key]
                return None
            self.cache.move_to_end(key)
            return item['value']

    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            elif len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            self.cache[key] = {'value': value, 'timestamp': time.time()}

    def clear(self):
        with self.lock:
            self.cache.clear()

cache = Cache()