import inspect
class regress:
    def __init__(self):
        self.tests=[]
        self.arg_hash=set()

    def argstr(self, args):
        """Pretty representation of function arguments"""
        return ",".join(["{k}={v} ".format(k=k, v=v) for k,v in args.items()])

    def record(self, func):
        """Record function arguments and return value"""
        signature= inspect.signature(func)
        def wrapper(*args, **kwargs):
            bound_args= signature.bind(*args, **kwargs)
            ret = func(*args, **kwargs)
            if not self.argstr(bound_args.arguments) in self.arg_hash:
                self.tests.append((bound_args.arguments, ret))
                self.arg_hash.add(self.argstr(bound_args.arguments))
            return ret
        return wrapper

    def replay(self, func, diff = 0.0):
        """Replay recorded tests on a different function"""
        for args, ret in self.tests:
            actual = func(**args)
            if diff == 0.0:
                if ret != actual:
                    print ("Functions differ on: " + self.argstr(args))
            elif abs(ret - actual)>diff:
                print ("Functions differ on: " + self.argstr(args))
