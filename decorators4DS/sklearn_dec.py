import collections
from sklearn.base import BaseEstimator, TransformerMixin, ClassifierMixin


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
    
    
class FunctionClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, f):
        self.predict_func = f
    def __call__(self, X):
        return self.predict_func(X)
    def fit(self, X, y=None):
        return self
    def predict(self, X):
        if isinstance(X, collections.Iterable):
            return [self.predict_func(x) for x in X]
        return self.predict_func(X)


def sktransform(func):
    return FunctionTransformer(func)

def skclassify(func):
    return FunctionClassifier(func)

if __name__ == '__main__':
    from sklearn.pipeline import Pipeline
    @sktransform
    def power2(x):
        return x**2

    ppl=Pipeline([('a', power2),
                  ('b', power2)])
    print(ppl.fit_transform([3]))
