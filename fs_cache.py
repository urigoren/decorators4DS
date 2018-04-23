import json
import pickle
import os
import inspect
try:
    import boto3
except ModuleNotFoundError:
    pass

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


class s3_cache:
    def __init__(self, bucket, folder):
        self.folder = folder
        self.s3 = boto3.resource("s3").Bucket(bucket)

    def __call__(self, func):
        def new_func(*args, **kwargs):
            fname = "/"+"_".join(list(map(str, args))+[str(k) + "=" + str(v) for k, v in kwargs.items()])
            try:
                return pickle.loads(self.s3.Object(key=self.folder+fname).get()["Body"].read())
            except Exception:
                ret = func(*args, **kwargs)
                self.s3.put_object(Body=pickle.dumps(ret), Key=self.folder+fname)
                return ret
        return new_func
