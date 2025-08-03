from concurrent.futures import ThreadPoolExecutor

class ThreadPool:
    def __init__(self, max_workers=5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    def submit(self, fn, *args, **kwargs):
        return self.executor.submit(fn, *args, **kwargs)
    def shutdown(self):
        self.executor.shutdown(wait=True)