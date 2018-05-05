import multiprocessing
from time import sleep

class time_limit:
    def __init__(self, limit):
        self.limit = limit
        self.q = multiprocessing.Queue()

    def __call__(self, func):
        def qfunc(*args, **kwargs):
            while not self.q.empty():
                self.q.get()
            self.q.put(func(*args, **kwargs))

        def time_limited(*args, **kwargs):
            p = multiprocessing.Process(target=qfunc, name=func.__name__, args=args, kwargs=kwargs)
            p.start()
            p.join(self.limit)
            if p.is_alive():
                p.terminate()
                p.join()
            if self.q.empty():
                return None
            return self.q.get()

        return time_limited
    
    
if __name__=='__main__':
    @time_limit(3)
    def test(n):
        for i in range(n):
            sleep(1)
            i += 1
            print(i)
        return n

    print(test(2))
