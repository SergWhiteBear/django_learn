import numpy as np

from .models import *


# Logistic Regression, Random Forest, Linear Regression, дерево решений
class Analysis:

    def preprocess_data(self, df):
        pass

    def fit(self, X: np.array, y: np.array) -> np.array:
        pass

    def predict(self, X: np.array) -> np.array:
        pass

    def predict_proba(self, X: np.array) -> np.array:
        pass