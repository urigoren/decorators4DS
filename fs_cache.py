import json
import pickle
import os
import inspect

def json_file(fname):
    def decorator(function):
        signature= inspect.signature(function)
        def wrapper(*args, **kwargs):
            bound_args= signature.bind(*args, **kwargs)
            file_name= fname.format(**bound_args.arguments)
            if os.path.isfile(file_name):
                with open(file_name, 'r') as f:
                    ret = json.load(f)
            else:
                with open(file_name,'w') as f:
                    ret = function(*args, **kwargs)
                    json.dump(ret, f)
            return ret
        return wrapper
    return decorator


def pickle_file(fname):
    def decorator(function):
        signature= inspect.signature(function)
        def wrapper(*args, **kwargs):
            bound_args= signature.bind(*args, **kwargs)
            file_name= fname.format(**bound_args.arguments)
            if os.path.isfile(file_name):
                with open(file_name, 'rb') as f:
                    ret = pickle.load(f)
            else:
                with open(file_name,'wb') as f:
                    ret = function(*args, **kwargs)
                    pickle.dump(ret, f)
            return ret
        return wrapper
    return decorator
