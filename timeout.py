from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import TimeoutError
from time import sleep

class time_limit:
    def __init__(self, limit):
        self.limit = limit
        self.worker = ThreadPool(1)

    def __call__(self, func):
        def time_limited(*args, **kwargs):
            result = self.worker.apply_async(func, args, kwargs)
            try:
                return result.get(timeout=self.limit)
            except TimeoutError:
                return None

        return time_limited
    
    
if __name__=='__main__':
    @time_limit(3)
    def test(n):
        for i in range(n):
            sleep(1)
            print(i+1)
        return n

    print(test(2))
    print(test(5))
