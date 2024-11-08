# -*- coding: utf-8 -*-
"""
Created on Sat Jan 26 16:19:12 2013

@author: Janwillem van Dijk
@email: jwe.van.dijk@xs4all.nl

Module for generating skew normal random numbers (Adelchi Azzalini)
===================================================================
http://azzalini.stat.unipd.it/SN/

Licensing:
This code is distributed under the GNU LGPL license.

Calling routines in R package sn through rpy2
-   rnd_skewnormal: returns random valuse for sn distribution with given
        location scale and shape
-   random_skewnormal: returns random valuse for sn distribution with given
        mean, stdev and skewness
-   skewnormal_parms: returns location, scale and shape given
        mean, stdev and skewnessof the sn distribution
-   skewnormal_stats: returns mean, stdev and skewness given
        location scale and shape
-   pdf_skewnormal: returns values for the pdf of a skew normal distribution
-   cdf_skewnormal: returns values for the cdf of a skew normal distribution
-   skew_max: returns the maximum skewness of a sn distribution
"""

from math import pi, sqrt, copysign

from rpy2.robjects.packages import importr
from rpy2.robjects import numpy2ri
import numpy as np

# from rpy2.robjects.numpy2ri import ri2numpy, numpy2ri

numpy2ri.activate()

sn = importr("sn")


def pdf_skewnormal(x, location=0.0, scale=1.0, shape=0.0):
    return sn.dsn(numpy2ri(x), location, scale, shape)


def cdf_skewnormal(x, location=0.0, scale=1.0, shape=0.0):
    return sn.psn(numpy2ri(x), location, scale, shape)


def rnd_skewnormal(location=0.0, scale=1.0, shape=0.0, size=1):
    """
    Return skew normal random values using sn.rsn in rpy2
    =====================================================
    with given location, scale and shape
    @param location:    location of sn distribution
    @param scale:       scale of sn distribution
    @param shape:       shape of sn distribution
    @param size:        number of values to generate

    http://azzalini.stat.unipd.it/SN/
    """
    dp = np.array([location, scale, shape])
    rdata = sn.rsn(n=size, dp=dp)
    return rdata


def skewnormal_parms(mean=0.0, stdev=1.0, skew=0.0):
    """
    Return parameters for a skew normal distribution function
    =========================================================
    @param mean:    mean of sn distribution
    @param stdev:   standard deviation of sn distribution
    @param skew:    skewness of sn distribution
    http://azzalini.stat.unipd.it/SN/Intro/intro.html
    location (xi), scale (omega) and shape (alpha)
    """
    if abs(skew) > skew_max():
        print("Skewness must be between %.4f and %.4f" % (-skew_max(), skew_max()))
        print("None, None, None returned")
        return None, None, None
    beta = 2.0 - pi / 2.0
    skew_23 = pow(skew * skew, 1.0 / 3.0)
    beta_23 = pow(beta * beta, 1.0 / 3.0)
    eps2 = skew_23 / (skew_23 + beta_23)
    eps = copysign(sqrt(eps2), skew)
    delta = eps * sqrt(pi / 2.0)
    alpha = delta / sqrt(1.0 - delta * delta)
    omega = stdev / sqrt(1.0 - eps * eps)
    xi = mean - omega * eps
    return xi, omega, alpha


def skewnormal_stats(location=0.0, scale=1.0, shape=0.0):
    """
    Return statistics of a skew normal distribution function
    ========================================================
    @param locn:    location of sn distribution
    @param scale:   scale of sn distribution
    @param shape:   shape of sn distribution
    http://azzalini.stat.unipd.it/SN/Intro/intro.html
    """
    beta = 2.0 - pi / 2.0
    delta = shape / sqrt(1.0 + shape * shape)
    eps = delta * sqrt(2.0 / pi)
    mean = location + scale * eps
    stdev = scale * sqrt(1.0 - eps * eps)
    skew = beta * pow(eps, 3.0) / pow(1.0 - eps * eps, 3.0 / 2.0)
    return mean, stdev, skew


def skew_max():
    """
    Return maximum skewness of a skew normal distribution
    =====================================================
    skewness for shape->infinity
    """
    beta = 2.0 - pi / 2.0
    # lim(delta, shape --> inf) = 1.0
    eps = sqrt(2.0 / pi)
    return beta * pow(eps, 3.0) / pow(1.0 - eps * eps, 3.0 / 2.0) - 1e-16


def random_skewnormal(mean=0.0, stdev=1.0, skew=0.0, size=1):
    """
    Return random numbers from a skew normal distribution
    =====================================================
    with given mean, stdev and shape
    @param mean:    mean of sn distribution
    @param stdev:   stdev of sn distribution
    @param shape:   shape of sn distribution
    @param shape:   shape of sn distribution
    """
    loc, scale, shape = skewnormal_parms(mean, stdev, skew)
    if loc is not None:
        return rnd_skewnormal(loc, scale, shape, size=size)
    else:
        return None


if __name__ == "__main__":
    """
    Test routine
    """
    from numpy import linspace, median, arange, take, sort
    import scipy.stats as stats
    import matplotlib.pyplot as plt

    def text_in_plot(fig):
        xtxt = 0.10
        ytxt = 0.87
        dtxt = 0.03
        txt = r"$\mu:\,%.2f$" % mean
        fig.text(xtxt, ytxt, txt, horizontalalignment="left", fontsize=14)
        ytxt -= dtxt
        txt = r"$\sigma:\,%.2f$" % stdev
        fig.text(xtxt, ytxt, txt, horizontalalignment="left", fontsize=14)
        ytxt -= dtxt
        txt = r"$\gamma_1:\,%.2f,\,%.2f,\,%.2f$" % (skew, 0.0, -skew)
        fig.text(xtxt, ytxt, txt, horizontalalignment="left", fontsize=14)
        ytxt -= 2.0 * dtxt
        txt = r"$\xi:\,%.2f,\,%.2f,\,%.2f$" % (locp, loc, locm)
        fig.text(xtxt, ytxt, txt, horizontalalignment="left", fontsize=14)
        ytxt -= dtxt
        txt = r"$\omega:\,%.2f,\,%.2f,\,%.2f$" % (scalep, scale, scalem)
        fig.text(xtxt, ytxt, txt, horizontalalignment="left", fontsize=14)
        ytxt -= dtxt
        txt = r"$\alpha:\,%.2f,\,%.2f,\,%.2f$" % (shapep, shape, shapem)
        fig.text(xtxt, ytxt, txt, horizontalalignment="left", fontsize=14)

    mean = 0.0
    stdev = 1.0
    # skew between -skew_max() and skew_max()
    skew = skew_max()  # 0.9
    n_rand = 300000
    n_plot = 200

    data_plus = random_skewnormal(mean, stdev, skew, n_rand)
    print("skew normal distribution: positive skewness")
    print("mean:   %.3f" % data_plus.mean())
    print("median: %.3f" % median(data_plus))
    print("stdev:  %.3f" % data_plus.std())
    print("skew:   %.3f" % stats.skew(data_plus))
    locp, scalep, shapep = skewnormal_parms(mean, stdev, skew)
    print("loc:    %.3f" % locp)
    print("scale:  %.3f" % scalep)
    print("shape:  %.3f" % shapep)
    mu, sigma, gamma = skewnormal_stats(locp, scalep, shapep)
    print("mean:   %.3f" % mu)
    print("stdev:  %.3f" % sigma)
    print("skew:   %.3f" % gamma)

    data_sym = random_skewnormal(mean, stdev, 0.0, n_rand)
    print("\nskew normal distribution: zero skewness")
    print("mean:   %.3f" % data_sym.mean())
    print("median: %.3f" % median(data_sym))
    print("stdev:  %.3f" % data_sym.std())
    print("skew:   %.3f" % stats.skew(data_sym))
    loc, scale, shape = skewnormal_parms(mean, stdev, 0.0)
    print("loc:    %.3f" % loc)
    print("scale:  %.3f" % scale)
    print("shape:  %.3f" % shape)
    mu, sigma, gamma = skewnormal_stats(loc, scale, shape)
    print("mean:   %.3f" % mu)
    print("stdev:  %.3f" % sigma)
    print("skew:   %.3f" % gamma)

    data_min = random_skewnormal(mean, stdev, -skew, n_rand)
    print("\nskew normal distribution: negative skewness")
    print("mean:   %.3f" % data_min.mean())
    print("median: %.3f" % median(data_min))
    print("stdev:  %.3f" % data_min.std())
    print("skew:   %.3f" % stats.skew(data_min))
    locm, scalem, shapem = skewnormal_parms(mean, stdev, -skew)
    print("loc:    %.3f" % locm)
    print("scale:  %.3f" % scalem)
    print("shape:  %.3f" % shapem)
    mu, sigma, gamma = skewnormal_stats(locm, scalem, shapem)
    print("mean:   %.3f" % mu)
    print("stdev:  %.3f" % sigma)
    print("skew:   %.3f" % gamma)

    xpdf = linspace(mean - 4.0 * stdev, mean + 4.0 * stdev, n_plot)

    ykde_plus = stats.gaussian_kde(data_plus)
    ypdf_plus = ykde_plus(xpdf)
    y_plus = pdf_skewnormal(xpdf, locp, scalep, shapep)

    ykde_sym = stats.gaussian_kde(data_sym)
    ypdf_sym = ykde_sym(xpdf)
    y_sym = pdf_skewnormal(xpdf, loc, scale, shape)

    ykde_min = stats.gaussian_kde(data_min)
    ypdf_min = ykde_min(xpdf)
    y_min = pdf_skewnormal(xpdf, locm, scalem, shapem)

    figpdf = plt.figure()
    subpdf = figpdf.add_subplot(1, 1, 1)
    txt = r"$\mathrm{Skew-normal\,distribution\,of\,data\,(rpy)}$"
    subpdf.set_title(txt, fontsize=18)
    text_in_plot(figpdf)

    subpdf.axes.set_xlim(xpdf[0], xpdf[-1])
    subpdf.plot(xpdf, ypdf_plus, "r")
    subpdf.plot(xpdf, ypdf_sym, "g")
    subpdf.plot(xpdf, ypdf_min, "b")
    subpdf.plot(xpdf, y_plus, ":k")
    subpdf.plot(xpdf, y_sym, ":k")
    subpdf.plot(xpdf, y_min, ":k")
    figpdf.tight_layout()
    figpdf.savefig("skewnormal_pdf_rpy.svg")
    figpdf.savefig("skewnormal_pdf_rpy.pdf")

    figcdf = plt.figure()
    subcdf = figcdf.add_subplot(1, 1, 1)
    xcdf = linspace(mean - 5.0 * stdev, mean + 5.0 * stdev, n_plot)
    # select n_plot samples from data
    step = int(n_rand / n_plot)
    i_sel = arange(0, n_rand, step)
    p = i_sel * 1.0 / n_rand

    ycdf_min = cdf_skewnormal(xcdf, locm, scalem, shapem)
    ycdf_sym = cdf_skewnormal(xcdf, loc, scale, shape)
    ycdf_plus = cdf_skewnormal(xcdf, locp, scalep, shapep)

    data_plus = take(sort(data_plus), i_sel)
    data_sym = take(sort(data_sym), i_sel)
    data_min = take(sort(data_min), i_sel)

    subcdf.axes.set_xlim(xcdf[0], xcdf[-1])
    subcdf.axes.set_ylim(0.0, 1.0)
    subcdf.plot(data_plus, p, "r")
    subcdf.plot(data_sym, p, "g")
    subcdf.plot(data_min, p, "b")
    subcdf.plot(xcdf, ycdf_plus, ":k")
    subcdf.plot(xcdf, ycdf_sym, ":k")
    subcdf.plot(xcdf, ycdf_min, ":k")
    txt = r"$\mathrm{Skew-normal\,distribution\,of\,data\,(rpy)}$"
    subcdf.set_title(txt, fontsize=18)
    text_in_plot(figcdf)
    figcdf.tight_layout()
    figcdf.savefig("skewnormal_cdf.svg")
    figcdf.savefig("skewnormal_cdf.pdf")
    plt.show()
