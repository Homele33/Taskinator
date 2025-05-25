import pymc as pm
import pytensor.tensor as pt
import arviz as az

def build_and_train_bnn(X, y):
    n_features = X.shape[1]
    n_classes = 48 

    with pm.Model() as model:
        # Inputs
        X_shared = pm.Data("X_shared", X)
        y_shared = pm.Data("y_shared", y)

        # Hidden layer
        w1 = pm.Normal("w1", mu=0, sigma=1, shape=(n_features, 16))
        b1 = pm.Normal("b1", mu=0, sigma=1, shape=(16,))
        hidden = pm.math.tanh(pm.math.dot(X_shared, w1) + b1)

        # Output layer
        w2 = pm.Normal("w2", mu=0, sigma=1, shape=(16, n_classes))
        b2 = pm.Normal("b2", mu=0, sigma=1, shape=(n_classes,))
        logits = pm.math.dot(hidden, w2) + b2

        # Probabilities
        theta = pm.Deterministic("theta", pm.math.softmax(logits))

        # Likelihood function 
        yl = pm.Categorical("yl", p=theta, observed=y_shared)

        # Training with ADVI
        approx = pm.fit(n=5000, method="advi")
        trace = approx.sample(1000)

    return model, approx, trace
