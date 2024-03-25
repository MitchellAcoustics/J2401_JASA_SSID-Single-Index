# %%
import pandas as pd
from rpy2.robjects import numpy2ri, pandas2ri
import rpy2.robjects as robjects
import rpy2.robjects.packages as rpackages
from rpy2.robjects.vectors import StrVector
import numpy as np

packageNames = ["sn", "tmvtnorm"]
utils = rpackages.importr("utils")
utils.chooseCRANmirror(ind=1)

packnames_to_install = [x for x in packageNames if not rpackages.isinstalled(x)]

# Running R in Python example installing packages:
if len(packnames_to_install) > 0:
    utils.install_packages(StrVector(packnames_to_install))

sn = rpackages.importr("sn")
tmvtnorm = rpackages.importr("tmvtnorm")

numpy2ri.activate()
pandas2ri.activate()


# %%

# mu = [0.5, 0.5]
# sigma = np.array([[1, 0.8], [0.8, 2]])
# a = [-1.0, -1.0]
# b = [1.0, 1.0]

# mu = robjects.FloatVector(mu)
# sigma = robjects.r.matrix(
#     robjects.FloatVector(sigma.flatten()),
#     nrow=sigma.shape[0],
#     ncol=sigma.shape[1]
# )
# a = robjects.FloatVector(a)
# b = robjects.FloatVector(b)

# # tmvtnorm.rtmvnorm(n=1000, mean=mu, sigma=sigma, lower=a, upper=b, algorithm="gibbs")
# moments = tmvtnorm.mtmvnorm(
#     mean=mu, sigma=sigma, lower=a, upper=b
# )


# %%   


def selm(x: str, y: str, data: pd.DataFrame):
    formula = f"cbind({x}, {y}) ~ 1"
    return sn.selm(formula, data=data, family="SN")


def calc_cp(x: str, y: str, data: pd.DataFrame):
    selm_model = selm(x, y, data)
    return extract_cp(selm_model)


def calc_dp(x: str, y: str, data: pd.DataFrame):
    selm_model = selm(x, y, data)
    return extract_dp(selm_model)


def extract_cp(selm_model):
    return tuple(selm_model.slots["param"][1])


def extract_dp(selm_model):
    return tuple(selm_model.slots["param"][0])


def sample_msn(selm_model=None, xi=None, omega=None, alpha=None, n=1000):
    if selm_model is not None:
        return sn.rmsn(n, dp=selm_model.slots["param"][0])
    elif xi is not None and omega is not None and alpha is not None:
        xi = robjects.FloatVector(xi.T)  # Transpose to make it a column vector
        omega = robjects.r.matrix(
            robjects.FloatVector(omega.flatten()),
            nrow=omega.shape[0],
            ncol=omega.shape[1],
        )
        alpha = robjects.FloatVector(alpha)  # Transpose to make it a column vector
        return sn.rmsn(n, xi=xi, Omega=omega, alpha=alpha)
    else:
        raise ValueError("Either selm_model or xi, omega, and alpha must be provided.")


def sample_sn(selm_model, n=1000):
    return sn.rsn(n, dp=selm_model.slots["param"][0])


def sample_mtsn(selm_model=None, xi=None, omega=None, alpha=None, a=-1, b=1, n=1000):
    """
    Sample from a multivariate truncated skew-normal distribution.
    Uses rejection sampling to ensure that the samples are within the bounds

    Args:

    """
    samples = np.array([[0, 0]])
    n_samples = 0
    while n_samples < n:
        if selm_model is not None:
            sample = sample_msn(selm_model, n=1)
        elif xi is not None and omega is not None and alpha is not None:
            sample = sample_msn(xi=xi, omega=omega, alpha=alpha, n=1)
        else:
            raise ValueError(
                "Either selm_model or xi, omega, and alpha must be provided."
            )
        if a <= sample[0][0] <= b and a <= sample[0][1] <= b:
            samples = np.append(samples, sample, axis=0)
            if n_samples == 0:
                samples = samples[1:]
            n_samples += 1
    return samples
