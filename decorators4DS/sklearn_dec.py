import collections
import cloudpickle
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin, ClassifierMixin


class SKDecorate:
    def __init__(self, f):
        self.func = f

    def __call__(self, X=None):
        if X is None:
               return self
        return self.func(X)

    def __iter__(self):
        return (i for i in [self.func.__name__, self])

    def __getitem__(self, i):
        return [self.func.__name__, self][i]

    def __getstate__(self):
        self.func_pkl = cloudpickle.dumps(self.func)
        del self.func
        return self.__dict__

    def __setstate__(self, d):
        d["func"] = cloudpickle.loads(d["func_pkl"])
        del d["func_pkl"]
        self.__dict__ = d


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
    from sklearn.externals import joblib


    @SKTransform
    def power2(x):
        return x ** 2


    @SKClassify
    def lessThan50(x):
        return x < 50


    ppl = Pipeline([
        power2,
        lessThan50,
    ])
    assert ppl.predict([3, 6, 8, 10]) == [True, True, False, False]
    joblib.dump(ppl, "ppl.pkl")
    del power2
    del lessThan50
    del ppl
    ppl = joblib.load("ppl.pkl")
    assert ppl.predict([3, 6, 8, 10]) == [True, True, False, False]
