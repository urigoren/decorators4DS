import collections
import marshal
from types import FunctionType
from sklearn.base import BaseEstimator, TransformerMixin, ClassifierMixin

class SKDecorate:
    def __init__(self, f):
        self.func = f
    def __call__(self, X):
        return self.func(X)
    def __iter__(self):
        return (i for i in [self.func.__name__, self])
    def __getitem__(self, i):
        return [self.func.__name__, self][i]
    def __getstate__(self):
        self.func_name = self.func.__name__
        self.func_code = marshal.dumps(self.func.__code__)
        del self.func
        return self.__dict__
    def __setstate__(self, d):
        new_dict = {}
        for k,v in d.items():
            if k in ['func', 'func_name']:
                continue
            if k=='func_code':
                new_dict["func"] = FunctionType(marshal.loads(v), globals(), d["func_name"])
            else:
                new_dict[k]=v
        self.__dict__ = new_dict

class SKTransform(BaseEstimator, TransformerMixin, SKDecorate):
    """Sklearn Transformer Decorator"""
    def __init__(self, f):
        self.func = f
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        if isinstance(X, collections.Iterable):
            return [self.func(x) for x in X]
        return self.func(X)
    
    
class SKClassify(BaseEstimator, ClassifierMixin, SKDecorate):
    """Sklearn Classifier Decorator"""
    def __init__(self, f):
        self.func = f
    def fit(self, X, y=None):
        return self
    def fit_predict(self, X, y=None):
        return self.predict(X)
    def predict(self, X, y=None):
        if isinstance(X, collections.Iterable):
            return [self.func(x) for x in X]
        return self.func(X)


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
