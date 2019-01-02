import collections
import marshal
from types import FunctionType
from sklearn.base import BaseEstimator, TransformerMixin, ClassifierMixin


class SKTransform(BaseEstimator, TransformerMixin):
    """Sklearn Transformer Decorator"""
    def __init__(self, f):
        self.transform_func = f
    def __call__(self, X):
        return self.transform_func(X)
    def __iter__(self):
        return (i for i in [self.transform_func.__name__, self])
    def __getitem__(self, i):
        return [self.transform_func.__name__, self][i]
    def __getstate__(self):
        self.func_code = marshal.dumps(self.transform_func.__code__)
        del self.transform_func
        return self.__dict__
    def __setstate__(self, d):
        new_dict = {}
        for k,v in d.items():
            if k=='transform_func':
                continue
            if k=='func_code':
                new_dict["transform_func"] = FunctionType(marshal.loads(v), globals(), "func")
            else:
                new_dict[k]=v
        self.__dict__ = new_dict
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        if isinstance(X, collections.Iterable):
            return [self.transform_func(x) for x in X]
        return self.transform_func(X)
    
    
class SKClassify(BaseEstimator, ClassifierMixin):
    """Sklearn Classifier Decorator"""
    def __init__(self, f):
        self.predict_func = f
    def __call__(self, X):
        return self.predict_func(X)
    def __iter__(self):
        return (i for i in [self.predict_func.__name__, self])
    def __getitem__(self, i):
        return [self.predict_func.__name__, self][i]
    def __getstate__(self):
        self.func_code = marshal.dumps(self.predict_func.__code__)
        del self.predict_func
        return self.__dict__
    def __setstate__(self, d):
        new_dict = {}
        for k,v in d.items():
            if k=='predict_func':
                continue
            if k=='func_code':
                new_dict["predict_func"] = FunctionType(marshal.loads(v), globals(), "func")
            else:
                new_dict[k]=v
        self.__dict__ = new_dict
    def fit(self, X, y=None):
        return self
    def fit_predict(self, X, y=None):
        return self.predict(X)
    def predict(self, X, y=None):
        if isinstance(X, collections.Iterable):
            return [self.predict_func(x) for x in X]
        return self.predict_func(X)


if __name__ == '__main__':
    # Toy usage example:
    from sklearn.pipeline import Pipeline
    @SKTransform
    def power2(x):
        return x**2
    @SKClassify
    def lessThan50(x):
        return x<50

    ppl=Pipeline([
                  power2,
                  lessThan50,
                 ])
    assert ppl.predict([3,6,8,10]) == [True, True, False, False]
