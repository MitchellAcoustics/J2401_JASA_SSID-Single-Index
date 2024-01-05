#%%
from soundscapy import isd
from pathlib import Path
import pandas as pd
import soundscapy as sspy
import matplotlib.pyplot as plt

# Load latest ISD dataset
isd_file = Path("/Users/mitch/Library/CloudStorage/OneDrive-UniversityCollegeLondon/_Fellowship/Datasets/ISD v1.0-alpha for Kenneth/ISD Database v1.0.1.xlsx")

data = pd.read_excel(isd_file, sheet_name = "Master Merge")
data, excl_data = isd.validate(data)

#%%

# Drop Chinese data
rows_to_drop = data.query("Language == 'Chinese Mandarin'").index
data.drop(rows_to_drop, inplace=True)

#%%
# Calculate an overall quality rating by combining 'Appropriateness' and 'Overall Rating'
data['QualityRating'] = data.Appropriate + data.Overall

#%%
# Define some architectural typologies
parks = [
    "RegentsParkFields",
    "RegentsParkJapan",
    "Noorderplantsoen",
    "StPaulsCross",
    "MiradorSanNicolas",
    "RussellSq",
    ]

walkways = [
    "MarchmontGarden",
    "MonumentoGaribaldi",
    "PancrasLock",
    "TateModern",
    ]

squares = [
    "PlazaBibRambla",
    "SanMarco",
    "StPaulsRow",
    "CampoPrincipe",
    "CarloV"
    ]

roads = [
    "CamdenTown",
    "EustonTap",
    "TorringtonSq"
    ]

#%%
# Assign architectural typologies to each data point
data.loc[data.LocationID.isin(parks), "ArchiType"] = "Park"
data.loc[data.LocationID.isin(walkways), "ArchiType"] = "Walkway"
data.loc[data.LocationID.isin(squares), "ArchiType"] = "Square"
data.loc[data.LocationID.isin(roads), "ArchiType"] = "Road"
data['ArchiType'] = data['ArchiType'].astype('category')

#%%
# Classify each point into a high or low soundscape quality
data['TypeSpecificQuality'] = "low"

# By using a quantile-based threshold, we are extracting the top x% of all responses from each typology
for type in data.ArchiType.unique():
    type_threshold = data.query("ArchiType == @type")["QualityRating"].quantile(0.75)
    # type_threshold = type_threshold if type_threshold > 8 else 8
    print(f"Threshold for {type} is {type_threshold}")
    rows = data.query(
        "ArchiType == @type & QualityRating >= @type_threshold & ISOPleasant > 0", engine="python"
    ).index
    data["TypeSpecificQuality"][rows] = "high"


#%%

# Plot the high quality responses for each typology
sspy.plotting.jointplot(
        data.query("TypeSpecificQuality == 'high'"),
        hue="ArchiType",
        density_type="simple",
        # incl_scatter=False,
        title="High soundscape quality distributions by Architectural type"
        )
plt.show()

#%%
# Calculate the mean and std for each of the high quality distributions
high_qual_data = data.query("TypeSpecificQuality == 'high'")
means = high_qual_data[['ISOPleasant', 'ISOEventful', 'ArchiType']].groupby("ArchiType").mean()
stds = high_qual_data[['ISOPleasant', 'ISOEventful', 'ArchiType']].groupby("ArchiType").std()

#%%
# Functions to sample distributions from the above means and stds
from scipy.stats import truncnorm

def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    # sample from a truncated normal distribution
    # this custom function wraps the scipy function to make it simpler to use
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)

def dist_generation(pl_mean, ev_mean, pl_std, ev_std, n=1000, dist_type="normal"):
    # Generate a distribution from ISOPl and ISOEv means and stds
    import numpy as np
    if dist_type == "normal":
        pl = np.random.normal(pl_mean, pl_std, n)
        ev = np.random.normal(ev_mean, ev_std, n)
    elif dist_type == "truncnorm":
        pl = get_truncated_normal(
            mean=pl_mean, sd=pl_std, low=-1, upp=1
        ).rvs(n)
        ev = get_truncated_normal(
            mean=ev_mean, sd=ev_std, low=-1, upp=1
        ).rvs(n)

    return pl, ev

def df_generation(pl_means, ev_means, pl_stds, ev_stds, n=1000, dist_type="normal"):
    # Create a df of values generated from a distribution
    import numpy as np
    import pandas as pd
    for type in pl_means.index:
        pl, ev = dist_generation(pl_means[type], ev_means[type], pl_stds[type], ev_stds[type], n, dist_type)
        if type == pl_means.index[0]:
            res_df = pd.DataFrame({"ISOPleasant": pl, "ISOEventful": ev, "ArchiType": type})
        else:
            temp_df = pd.DataFrame({"ISOPleasant": pl, "ISOEventful": ev, "ArchiType": type})
            res_df = pd.concat((res_df, temp_df), axis=0)
    res_df.reset_index(drop=True, inplace=True)
    return res_df

#%%
# generate the distributions for the architectural types
gend_df = df_generation(means.ISOPleasant, means.ISOEventful, stds.ISOPleasant, stds.ISOEventful, n=1000, dist_type="normal")
# plot
sspy.plotting.jointplot(gend_df, hue="ArchiType", density_type="simple", incl_scatter=False, title="Generated SSID distributions for 4 ArchiTypes")
plt.show()

#%%
# Functions for a 2D Kolmogorov-Smirnov test
# Will return the KS Divergence between two 2D distributions
# from https://github.com/syrte/ndtest

from __future__ import division
import numpy as np
from numpy import random
from scipy.spatial.distance import pdist, cdist
from scipy.stats import kstwobign, pearsonr
from scipy.stats import genextreme

__all__ = ['ks2d2s', 'estat', 'estat2d']


def ks2d2s(x1, y1, x2, y2, nboot=None, extra=False):
    '''Two-dimensional Kolmogorov-Smirnov test on two samples.
    Parameters
    ----------
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

    '''
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
        d = np.empty(nboot, 'f')
        for i in range(nboot):
            idx = random.choice(n, n, replace=True)
            ix1, ix2 = idx[:n1], idx[n1:]
            #ix1 = random.choice(n, n1, replace=True)
            #ix2 = random.choice(n, n2, replace=True)
            d[i] = avgmaxdist(x[ix1], y[ix1], x[ix2], y[ix2])
        p = np.sum(d > D).astype('f') / nboot
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


def estat(x, y, nboot=1000, replace=False, method='log', fitting=False):
    '''
    Energy distance statistics test.
    Reference
    ---------
    Aslan, B, Zech, G (2005) Statistical energy as a tool for binning-free
      multivariate goodness-of-fit tests, two-sample comparison and unfolding.
      Nuc Instr and Meth in Phys Res A 537: 626-636
    Szekely, G, Rizzo, M (2014) Energy statistics: A class of statistics
      based on distances. J Stat Planning & Infer 143: 1249-1272
    Brian Lau, multdist, https://github.com/brian-lau/multdist

    '''
    n, N = len(x), len(x) + len(y)
    stack = np.vstack([x, y])
    stack = (stack - stack.mean(0)) / stack.std(0)
    if replace:
        rand = lambda x: random.randint(x, size=x)
    else:
        rand = random.permutation

    en = energy(stack[:n], stack[n:], method)
    en_boot = np.zeros(nboot, 'f')
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


def energy(x, y, method='log'):
    dx, dy, dxy = pdist(x), pdist(y), cdist(x, y)
    n, m = len(x), len(y)
    if method == 'log':
        dx, dy, dxy = np.log(dx), np.log(dy), np.log(dxy)
    elif method == 'gaussian':
        raise NotImplementedError
    elif method == 'linear':
        pass
    else:
        raise ValueError
    z = dxy.sum() / (n * m) - dx.sum() / n**2 - dy.sum() / m**2
    # z = ((n*m)/(n+m)) * z # ref. SR
    return z

#%%

# Testing the 2D KS test
ct_data = data.query("LocationID == 'CamdenTown'")[['ISOPleasant', 'ISOEventful']].dropna().values
road_data = high_qual_data.query("ArchiType == 'Road'")[['ISOPleasant', 'ISOEventful']].values  # same distribution as (x1, y1)
road_gen = gend_df.query("ArchiType == 'Park'")[['ISOPleasant', 'ISOEventful']].values  # different distribution from (x1, y1)

x1 = ct_data[:,0]
y1 = ct_data[:,1]
x2 = road_data[:,0]
y2 = road_data[:,1]
x3 = road_gen[:,0]
y3 = road_gen[:,1]

# 2D KS
# print(f"{P=:.3g}, {D=:.3g}")

P, D = ks2d2s(x1, y1, x3, y3, extra=True)
print(f"{P=:.3g}, {D=:.3g}")


#%%
# Put it all together

def ssid_type(test_data, target_data, archi_type):
    x1 = test_data['ISOPleasant'].values
    y1 = test_data['ISOEventful'].values

    x2 = target_data.query("ArchiType == @archi_type", engine='python')['ISOPleasant'].values
    y2 = target_data.query("ArchiType == @archi_type", engine='python')['ISOEventful'].values

    P, D = ks2d2s(x1, y1, x2, y2, extra=True)
    return int((1-D)*100)

loc = 'RegentsParkJapan'
type = 'Park'
res = ssid_type(data.query("LocationID == @loc"), high_qual_data, type)
print(f"{loc} SSID_{type}: {res}")

loc = 'MarchmontGarden'
type = 'Park'
res = ssid_type(data.query("LocationID == @loc"), high_qual_data, type)
print(f"{loc} SSID_{type}: {res}")

loc = 'EustonTap'
type = 'Road'
res = ssid_type(data.query("LocationID == @loc"), high_qual_data, type)
print(f"{loc} SSID_{type}: {res}")


#%%

def ssid_plot(test_data, target_data, archi_type, location, ax=None):
    test_data = test_data.query("LocationID == @location")[['ISOPleasant', 'ISOEventful']].copy()
    ssid = ssid_type(test_data, target_data, archi_type)

    type_target = target_data.query("ArchiType == @archi_type")[['ISOPleasant', 'ISOEventful']]
    type_target['SSID'] = 'Park Target'
    test_data['SSID'] = location
    df = pd.concat((type_target, test_data))

    sspy.plotting.density(df, hue='SSID', density_type='simple', title=f"{location}\nSSID_{archi_type}: {ssid}", ax=ax)

ssid_plot(data, high_qual_data, 'Park', 'MarchmontGarden')

#%%
fig, axes = plt.subplots(3,2,figsize=(9,12))

for i, loc in enumerate(parks):
    ssid_plot(
            data,
            high_qual_data,
            'Park',
            loc,
            ax=axes.flatten()[i]
            )
plt.tight_layout()
plt.show()

#%%
fig, axes = plt.subplots(3,1,figsize=(4,12))

for i, loc in enumerate(roads):
    ssid_plot(
            data,
            high_qual_data,
            'Road',
            loc,
            ax=axes.flatten()[i]
            )
plt.tight_layout()
plt.show()

#%%
fig, axes = plt.subplots(6, 3, figsize=(9,18))
for i, loc in enumerate(data.LocationID.unique()):
    archi_type = data.query("LocationID == @loc")['ArchiType'].iloc[0]
    ssid_plot(
            data,
            gend_df,
            archi_type,
            loc,
            ax=axes.flatten()[i]
            )
plt.tight_layout()
plt.show()
# %%
