import rpyskewnorm as snpy
import numpy as np


def test_skewnormal_parms():
    xi, omega, alpha = snpy.skewnormal_parms(3, 1.2, 0.8)
    assert xi == 1.5231940559809032
    assert omega == 1.9028809201550514
    assert alpha == 4.19019476366201


def test_skewnormal_stats():
    mean, stdev, skew = snpy.skewnormal_stats(
        1.5231940559809032, 1.9028809201550514, 4.19019476366201
    )
    assert mean == 3
    assert stdev == 1.2
    assert round(skew, 1) == 0.8


def test_pdf_skewnormal():
    pdf = snpy.pdf_skewnormal(np.array((3, 4, 1)), 1.523, 1.903, 4.190)
    assert round(pdf[0], 2) == 0.31
    assert round(pdf[1], 2) == 0.18
    assert round(pdf[2], 2) == 0.05


def test_cdf_skewnormal():
    cdf = snpy.cdf_skewnormal(np.array((3, 4, 1)), 1.523, 1.903, 4.190)
    assert round(cdf[0], 2) == 0.56
    assert round(cdf[1], 2) == 0.81
    assert round(cdf[2], 2) == 0.01


def test_rnd_skewnormal():
    rnd = snpy.rnd_skewnormal(1.523, 1.903, 4.190, 4)
    assert len(rnd) == 4


def test_plotting():
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
        skew = snpy.skew_max()  # 0.9
        n_rand = 300000
        n_plot = 200

        data_plus = snpy.random_skewnormal(mean, stdev, skew, n_rand)
        print("skew normal distribution: positive skewness")
        print("mean:   %.3f" % data_plus.mean())
        print("median: %.3f" % median(data_plus))
        print("stdev:  %.3f" % data_plus.std())
        print("skew:   %.3f" % stats.skew(data_plus))
        locp, scalep, shapep = snpy.skewnormal_parms(mean, stdev, skew)
        print("loc:    %.3f" % locp)
        print("scale:  %.3f" % scalep)
        print("shape:  %.3f" % shapep)
        mu, sigma, gamma = snpy.skewnormal_stats(locp, scalep, shapep)
        print("mean:   %.3f" % mu)
        print("stdev:  %.3f" % sigma)
        print("skew:   %.3f" % gamma)

        data_sym = snpy.random_skewnormal(mean, stdev, 0.0, n_rand)
        print("\nskew normal distribution: zero skewness")
        print("mean:   %.3f" % data_sym.mean())
        print("median: %.3f" % median(data_sym))
        print("stdev:  %.3f" % data_sym.std())
        print("skew:   %.3f" % stats.skew(data_sym))
        loc, scale, shape = snpy.skewnormal_parms(mean, stdev, 0.0)
        print("loc:    %.3f" % loc)
        print("scale:  %.3f" % scale)
        print("shape:  %.3f" % shape)
        mu, sigma, gamma = snpy.skewnormal_stats(loc, scale, shape)
        print("mean:   %.3f" % mu)
        print("stdev:  %.3f" % sigma)
        print("skew:   %.3f" % gamma)

        data_min = snpy.random_skewnormal(mean, stdev, -skew, n_rand)
        print("\nskew normal distribution: negative skewness")
        print("mean:   %.3f" % data_min.mean())
        print("median: %.3f" % median(data_min))
        print("stdev:  %.3f" % data_min.std())
        print("skew:   %.3f" % stats.skew(data_min))
        locm, scalem, shapem = snpy.skewnormal_parms(mean, stdev, -skew)
        print("loc:    %.3f" % locm)
        print("scale:  %.3f" % scalem)
        print("shape:  %.3f" % shapem)
        mu, sigma, gamma = snpy.skewnormal_stats(locm, scalem, shapem)
        print("mean:   %.3f" % mu)
        print("stdev:  %.3f" % sigma)
        print("skew:   %.3f" % gamma)

        xpdf = linspace(mean - 4.0 * stdev, mean + 4.0 * stdev, n_plot)

        ykde_plus = stats.gaussian_kde(data_plus)
        ypdf_plus = ykde_plus(xpdf)
        y_plus = snpy.pdf_skewnormal(xpdf, locp, scalep, shapep)

        ykde_sym = stats.gaussian_kde(data_sym)
        ypdf_sym = ykde_sym(xpdf)
        y_sym = snpy.pdf_skewnormal(xpdf, loc, scale, shape)

        ykde_min = stats.gaussian_kde(data_min)
        ypdf_min = ykde_min(xpdf)
        y_min = snpy.pdf_skewnormal(xpdf, locm, scalem, shapem)

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

        ycdf_min = snpy.cdf_skewnormal(xcdf, locm, scalem, shapem)
        ycdf_sym = snpy.cdf_skewnormal(xcdf, loc, scale, shape)
        ycdf_plus = snpy.cdf_skewnormal(xcdf, locp, scalep, shapep)

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
