import collections
from sklearn.base import BaseEstimator, TransformerMixin


class FunctionTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, f):
        self.transform_func = f
    def __call__(self, X):
        return self.transform_func(X)
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        if isinstance(X, collections.Iterable):
            return [self.transform_func(x) for x in X]
        return self.transform_func(X)


def sktransform(func):
    return FunctionTransformer(func)
