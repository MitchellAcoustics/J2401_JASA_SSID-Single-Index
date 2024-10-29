from __future__ import division

import numpy as np
import pandas as pd
from numpy import random
from scipy.spatial.distance import cdist, pdist

# Functions to sample distributions from the above means and stds
from scipy.stats import genextreme, kstwobign, pearsonr, skewnorm, truncnorm


def get_truncated_normal(
    mean: float = 0.0, sd: float = 1.0, low: float = 0.0, upp: float = 10.0
):
    # sample from a truncated normal distribution
    # this custom function wraps the scipy function to make it simpler to use
    return truncnorm((low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)


def truncated_skew_normal(mean, var, skew, a, b, num_samples=100000):
    # Parameters for the skew-normal distribution
    # delta = skew / np.sqrt(1 + skew**2)
    delta = skew
    # Rejection sampling
    samples = []
    while len(samples) < num_samples:
        candidate = skewnorm.rvs(delta, loc=mean, scale=var)
        if a <= candidate <= b:
            samples.append(candidate)

    return np.array(samples)


def dist_generation(
    pl_mean: float,
    ev_mean: float,
    pl_std: float,
    ev_std: float,
    pl_a: float = None,
    ev_a: float = None,
    n: int = 1000,
    dist_type: str = "normal",
):
    # Generate a distribution from ISOPl and ISOEv means and stds
    if dist_type == "normal":
        pl = np.random.normal(pl_mean, pl_std, n)
        ev = np.random.normal(ev_mean, ev_std, n)
    elif dist_type == "truncnorm":
        pl = get_truncated_normal(mean=pl_mean, sd=pl_std, low=-1, upp=1).rvs(n)
        ev = get_truncated_normal(mean=ev_mean, sd=ev_std, low=-1, upp=1).rvs(n)
    elif dist_type == "skewnorm":
        pl = skewnorm.rvs(a=pl_a, loc=pl_mean, scale=pl_std, size=n)
        ev = skewnorm.rvs(a=ev_a, loc=ev_mean, scale=ev_std, size=n)
    elif dist_type == "trunc_skewnorm":
        pl = truncated_skew_normal(
            mean=pl_mean, var=pl_std, skew=pl_a, a=-1, b=1, num_samples=n
        )
        ev = truncated_skew_normal(
            mean=ev_mean, var=ev_std, skew=ev_a, a=-1, b=1, num_samples=n
        )

    return pl, ev


def df_generation(
    pl_means: pd.DataFrame,
    ev_means: pd.DataFrame,
    pl_stds: pd.DataFrame,
    ev_stds: pd.DataFrame,
    pl_as: pd.DataFrame = None,
    ev_as: pd.DataFrame = None,
    n: int = 1000,
    dist_type: str = "normal",
):
    # Create a df of values generated from a distribution
    for type in pl_means.index:
        pl, ev = dist_generation(
            pl_means[type],
            ev_means[type],
            pl_stds[type],
            ev_stds[type],
            pl_as,
            ev_as,
            n,
            dist_type,
        )
        if type == pl_means.index[0]:
            res_df = pd.DataFrame(
                {"ISOPleasant": pl, "ISOEventful": ev, "ArchiType": type}
            )
        else:
            temp_df = pd.DataFrame(
                {"ISOPleasant": pl, "ISOEventful": ev, "ArchiType": type}
            )
            res_df = pd.concat((res_df, temp_df), axis=0)
    res_df.reset_index(drop=True, inplace=True)
    return res_df


# Functions for a 2D Kolmogorov-Smirnov test
# Will return the KS Divergence between two 2D distributions
# from https://github.com/syrte/ndtest


__all__ = ["ks2d2s", "estat", "estat2d"]


def ks2d2s(
    test_data: pd.DataFrame | np.ndarray = None,
    target_data: pd.DataFrame | np.ndarray = None,
    x1: np.array = None,
    y1: np.array = None,
    x2: np.array = None,
    y2: np.array = None,
    nboot=None,
    extra=False,
):
    """Two-dimensional Kolmogorov-Smirnov test on two samples.

    This is the two-sided K-S test. Small p-values means that the two samples are significantly different.
    Note that the p-value is only an approximation as the analytic distribution is unkonwn. The approximation
    is accurate enough when N > ~20 and p-value < ~0.20 or so. When p-value > 0.20, the value may not be accurate,
    but it certainly implies that the two samples are not significantly different. (cf. Press 2007)

    Parameters
    ----------
    test_data, target_data: pd.DataFrame
        DataFrames containing the test and target distributions.
        Can be used instead of x1, y1, x2, y2.
    x1, y1 : ndarray, shape (n1, )
        Data of sample 1.
    x2, y2 : ndarray, shape (n2, )
        Data of sample 2. Size of two samples can be different.
    nboot : None or int
        Number of bootstrap resample to estimate the p-value. A large number is expected.
        If None, an approximate analytic estimate will be used.
    extra: bool, optional
        If True, KS statistic is also returned. Default is False.

    Returns
    -------
    p : float
        Two-tailed p-value.
    D : float, optional
        KS statistic, returned if keyword `extra` is True.

    Notes
    -----
    This is the two-sided K-S test. Small p-values means that the two samples are significantly different.
    Note that the p-value is only an approximation as the analytic distribution is unkonwn. The approximation
    is accurate enough when N > ~20 and p-value < ~0.20 or so. When p-value > 0.20, the value may not be accurate,
    but it certainly implies that the two samples are not significantly different. (cf. Press 2007)

    References
    ----------
    Peacock, J.A. 1983, Two-Dimensional Goodness-of-Fit Testing in Astronomy, MNRAS, 202, 615-627
    Fasano, G. and Franceschini, A. 1987, A Multidimensional Version of the Kolmogorov-Smirnov Test, MNRAS, 225, 155-170
    Press, W.H. et al. 2007, Numerical Recipes, section 14.8

    """

    if (
        test_data is None
        and target_data is None
        and x1 is None
        and x2 is None
        and y1 is None
        and y2 is None
    ):
        raise ValueError("Use either test_data and target_data or x1, y1, x2, y2")

    if test_data is not None and target_data is not None:
        assert test_data.shape[1] == 2 and target_data.shape[1] == 2
        if isinstance(test_data, pd.DataFrame):
            x1 = test_data.iloc[:, 0].values
            y1 = test_data.iloc[:, 1].values
        else:
            x1, y1 = test_data[:, 0], test_data[:, 1]

        if isinstance(target_data, pd.DataFrame):
            x2 = target_data.iloc[:, 0].values
            y2 = target_data.iloc[:, 1].values
        else:
            x2, y2 = target_data[:, 0], target_data[:, 1]

    assert (len(x1) == len(y1)) and (len(x2) == len(y2))
    n1, n2 = len(x1), len(x2)
    D = avgmaxdist(x1, y1, x2, y2)

    if nboot is None:
        sqen = np.sqrt(n1 * n2 / (n1 + n2))
        r1 = pearsonr(x1, y1)[0]
        r2 = pearsonr(x2, y2)[0]
        r = np.sqrt(1 - 0.5 * (r1**2 + r2**2))
        d = D * sqen / (1 + r * (0.25 - 0.75 / sqen))
        p = kstwobign.sf(d)
    else:
        n = n1 + n2
        x = np.concatenate([x1, x2])
        y = np.concatenate([y1, y2])
        d = np.empty(nboot, "f")
        for i in range(nboot):
            idx = random.choice(n, n, replace=True)
            ix1, ix2 = idx[:n1], idx[n1:]
            # ix1 = random.choice(n, n1, replace=True)
            # ix2 = random.choice(n, n2, replace=True)
            d[i] = avgmaxdist(x[ix1], y[ix1], x[ix2], y[ix2])
        p = np.sum(d > D).astype("f") / nboot
    if extra:
        return p, D
    else:
        return p


def avgmaxdist(x1, y1, x2, y2):
    D1 = maxdist(x1, y1, x2, y2)
    D2 = maxdist(x2, y2, x1, y1)
    return (D1 + D2) / 2


def maxdist(x1, y1, x2, y2):
    n1 = len(x1)
    D1 = np.empty((n1, 4))
    for i in range(n1):
        a1, b1, c1, d1 = quadct(x1[i], y1[i], x1, y1)
        a2, b2, c2, d2 = quadct(x1[i], y1[i], x2, y2)
        D1[i] = [a1 - a2, b1 - b2, c1 - c2, d1 - d2]

    # re-assign the point to maximize difference,
    # the discrepancy is significant for N < ~50
    D1[:, 0] -= 1 / n1

    dmin, dmax = -D1.min(), D1.max() + 1 / n1
    return max(dmin, dmax)


def quadct(x, y, xx, yy):
    n = len(xx)
    ix1, ix2 = xx <= x, yy <= y
    a = np.sum(ix1 & ix2) / n
    b = np.sum(ix1 & ~ix2) / n
    c = np.sum(~ix1 & ix2) / n
    d = 1 - a - b - c
    return a, b, c, d


def estat2d(x1, y1, x2, y2, **kwds):
    return estat(np.c_[x1, y1], np.c_[x2, y2], **kwds)


def estat(x, y, nboot=1000, replace=False, method="log", fitting=False):
    """
    Energy distance statistics test.
    Reference
    ---------
    Aslan, B, Zech, G (2005) Statistical energy as a tool for binning-free
      multivariate goodness-of-fit tests, two-sample comparison and unfolding.
      Nuc Instr and Meth in Phys Res A 537: 626-636
    Szekely, G, Rizzo, M (2014) Energy statistics: A class of statistics
      based on distances. J Stat Planning & Infer 143: 1249-1272
    Brian Lau, multdist, https://github.com/brian-lau/multdist

    """
    n, N = len(x), len(x) + len(y)
    stack = np.vstack([x, y])
    stack = (stack - stack.mean(0)) / stack.std(0)
    if replace:
        rand = lambda x: random.randint(x, size=x)
    else:
        rand = random.permutation

    en = energy(stack[:n], stack[n:], method)
    en_boot = np.zeros(nboot, "f")
    for i in range(nboot):
        idx = rand(N)
        en_boot[i] = energy(stack[idx[:n]], stack[idx[n:]], method)

    if fitting:
        param = genextreme.fit(en_boot)
        p = genextreme.sf(en, *param)
        return p, en, param
    else:
        p = (en_boot >= en).sum() / nboot
        return p, en, en_boot


def energy(x, y, method="log"):
    dx, dy, dxy = pdist(x), pdist(y), cdist(x, y)
    n, m = len(x), len(y)
    if method == "log":
        dx, dy, dxy = np.log(dx), np.log(dy), np.log(dxy)
    elif method == "gaussian":
        raise NotImplementedError
    elif method == "linear":
        pass
    else:
        raise ValueError
    z = dxy.sum() / (n * m) - dx.sum() / n**2 - dy.sum() / m**2
    # z = ((n*m)/(n+m)) * z # ref. SR
    return z


def spi(test_data, target_data):
    P, D = ks2d2s(test_data, target_data, extra=True)
    return int((1 - D) * 100)


def spi_plot(test_data, target, n=1000, ax=None):
    # TODO: Add a plot of the two distributions
    return None


# def adj_angle_iso_coords(data: pd.DataFrame, angles, scale=100):
#     isopl = data.apply(
#         lambda x: adj_iso_pl(x[scales].values, angles, scale=scale), axis=1
#     )
#     isoev = data.apply(
#         lambda x: adj_iso_ev(x[scales].values, angles, scale=scale), axis=1
#     )
#     return isopl, isoev


def adj_iso_pl(values, angles, scale=None):
    # scale = range of input values (e.g. 0-100)
    # The scaling factor was derived by comparing to
    # the scaling from the ISO method. Confirmed to be
    # the same value when using equal angles.
    # 100 * sum of abs values of the loading factors / 2
    iso_pl = np.sum(
        [np.cos(np.deg2rad(angle)) * values[i] for i, angle in enumerate(angles)]
    )
    if scale:
        iso_pl = iso_pl / (
            scale / 2 * np.sum(np.abs([np.cos(np.deg2rad(angle)) for angle in angles]))
        )
    return iso_pl


def adj_iso_ev(values, angles, scale=None):
    iso_ev = np.sum(
        [np.sin(np.deg2rad(angle)) * values[i] for i, angle in enumerate(angles)]
    )
    if scale:
        iso_ev = iso_ev / (
            scale / 2 * np.sum(np.abs([np.sin(np.deg2rad(angle)) for angle in angles]))
        )
    return iso_ev
