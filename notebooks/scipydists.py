from scipy import stats
from scipy.stats._multivariate import _squeeze_output
from scipy.stats import multivariate_normal as mvn
import numpy as np


def scipy_mn(loc: float, cov: float, num_samples=1000):
    """
    Sample from a Multivariate Normal Distribution

    """
    return stats.multivariate_normal.rvs(mean=loc, cov=cov, size=num_samples)


def scipy_mtn(loc: float, cov: float, a: float = -1, b: float = 1, num_samples=1000):
    """
    Sample from a truncated multivariate normal distribution.
    Uses rejection sampling to ensure that the samples are within the bounds

    Args:
    loc: location parameter
    cov: covariance matrix
    a: lower bound
    b: upper bound
    num_samples: number of samples to draw
    """
    samples = []
    while len(samples) < num_samples:
        candidate = stats.multivariate_normal.rvs(mean=loc, cov=cov)
        if a <= candidate[0] <= b and a <= candidate[1] <= b:
            samples.append(candidate)
    return np.array(samples)


def scipy_tn(loc: float, stddev: float, a: float = -1, b: float = 1, num_samples=1000):
    """
    Sample from a truncated normal distribution.
    Uses rejection sampling to ensure that the samples are within the bounds

    Args:
    loc: location parameter
    scale: scale parameter
    a: lower bound
    b: upper bound
    num_samples: number of samples to draw
    """
    return stats.truncnorm.rvs(a, b, loc=loc, scale=stddev, size=num_samples)


def scipy_tn_2d(
    loc: tuple, scale: tuple, a: tuple = (-1, -1), b: tuple = (1, 1), num_samples=1000
):
    """
    Sample from a truncated normal distribution.
    Uses rejection sampling to ensure that the samples are within the bounds

    Args:
    loc: location parameter
    scale: scale parameter
    a: lower bound
    b: upper bound
    num_samples: number of samples to draw
    """
    samples = np.array(
        [
            scipy_tn(loc[0], scale[0], a[0], b[0], num_samples),
            scipy_tn(loc[1], scale[1], a[1], b[1], num_samples),
        ]
    ).T
    return samples


# Scipy Truncated Skew-Normal Distribution
def scipy_tsn(
    loc: float,
    scale: float,
    alpha: float,
    a: float = -1,
    b: float = 1,
    num_samples=1000,
):
    """
    Sample from a truncated skew-normal distribution.
    Uses rejection sampling to ensure that the samples are within the bounds

    Args:
    loc: location parameter
    scale: scale parameter
    skew: skew parameter
    a: lower bound
    b: upper bound
    num_samples: number of samples to draw
    """
    samples = []
    while len(samples) < num_samples:
        candidate = stats.skewnorm.rvs(alpha, loc=loc, scale=scale)
        if a <= candidate <= b:
            samples.append(candidate)
    return np.array(samples)


def estimate_skew_moments(samples: np.array):
    """
    Estimate the skewness and kurtosis of a sample using the method of moments

    Args:
    samples: the sample to estimate the moments from
    """
    alpha, loc, scale = stats.skewnorm.fit(samples)
    return loc, scale, alpha


def scipy_tsn_2d(
    loc: tuple,
    scale: tuple,
    alpha: tuple,
    a: tuple = (-1, -1),
    b: tuple = (1, 1),
    num_samples=1000,
):
    """
    Sample from a truncated skew-normal distribution.
    Uses rejection sampling to ensure that the samples are within the bounds

    Args:
    loc: location parameter
    scale: scale parameter
    skew: skew parameter
    a: lower bound
    b: upper bound
    num_samples: number of samples to draw
    """
    samples = np.array(
        [
            scipy_tsn(loc[0], scale[0], alpha[0], a[0], b[0], num_samples),
            scipy_tsn(loc[1], scale[1], alpha[1], a[1], b[1], num_samples),
        ]
    ).T
    return samples


def estimate_skew_moments_2d(samples: np.array):
    loc_0, scale_0, alpha_0 = estimate_skew_moments(samples[:, 0])
    loc_1, scale_1, alpha_1 = estimate_skew_moments(samples[:, 1])
    return (loc_0, loc_1), (scale_0, scale_1), (alpha_0, alpha_1)


## Scipy Multivariate Skew-Normal


class scipy_msn:
    # from: https://gregorygundersen.com/blog/2020/12/29/multivariate-skew-normal/
    def __init__(self, shape, mean=(0, 0), cov=None):
        self.dim = len(shape)
        self.shape = np.asarray(shape)
        self.mean = np.asarray(mean)
        self.cov = np.eye(self.dim) if cov is None else np.asarray(cov)

    def pdf(self, x):
        return np.exp(self.logpdf(x))

    def logpdf(self, x):
        x = mvn._process_quantiles(x, self.dim)
        pdf = mvn(self.mean, self.cov).logpdf(x)
        cdf = stats.norm(0, 1).logcdf(np.dot(x, self.shape))
        return _squeeze_output(np.log(2) + pdf + cdf)

    def rvs_slow(self, size=1):
        # K-variate normal density
        std_mvn = mvn(self.mean, self.cov)
        x = np.empty((size, self.dim))

        # Apply rejection sampling.
        n_samples = 0
        while n_samples < size:
            z = std_mvn.rvs(size=1)
            u = np.random.uniform(0, 2 * std_mvn.pdf(z))
            if not u > self.pdf(z):
                x[n_samples] = z
                n_samples += 1

        # Rescale based on correlation matrix.
        # chol = np.linalg.cholesky(self.cov)
        # x = (chol @ x.T).T

        return x

    def rvs_fast(self, size=1):
        aCa = self.shape @ self.cov @ self.shape
        delta = (1 / np.sqrt(1 + aCa)) * self.cov @ self.shape
        cov_star = np.block([[np.ones(1), delta], [delta[:, None], self.cov]])
        x = mvn(np.zeros(self.dim + 1), cov_star).rvs(size)
        x0, x1 = x[:, 0], x[:, 1:]
        inds = x0 <= 0
        x1[inds] = -1 * x1[inds]
        return x1


def estimate_msn_moments(samples):
    # Calculate sample mean
    sample_mean = np.mean(samples, axis=0)

    # Calculate sample covariance matrix
    sample_cov_matrix = np.cov(samples, rowvar=False)

    # Center the samples
    centered_samples = samples - sample_mean

    # Calculate skewness matrix using the centered samples
    skewness_matrix = (
        np.mean(centered_samples**3, axis=0) / np.std(centered_samples, axis=0) ** 3
    )

    return sample_mean, sample_cov_matrix, skewness_matrix
