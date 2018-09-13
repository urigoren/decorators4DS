import collections
from sklearn.base import BaseEstimator, TransformerMixin, ClassifierMixin


class SKTransform(BaseEstimator, TransformerMixin):
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
    
    
class SKClassify(BaseEstimator, ClassifierMixin):
    def __init__(self, f):
        self.predict_func = f
    def __call__(self, X):
        return self.predict_func(X)
    def fit(self, X, y=None):
        return self
    def predict(self, X, y=None):
        if isinstance(X, collections.Iterable):
            return [self.predict_func(x) for x in X]
        return self.predict_func(X)


if __name__ == '__main__':
    from sklearn.pipeline import Pipeline
    @SKTransform
    def power2(x):
        return x**2
    @SKClassify
    def lessThan50(x):
        return x<50

    ppl=Pipeline([
                  ('x^2', power2),
                  ('x<50', lessThan50),
                 ])
    assert ppl.predict([3,6,8,10]) == [True, True, False, False]
