# %%
import numpy as np
import pandas as pd
import rpyskewnorm as rsn
import soundscapy as sspy
import KS2D


class DirectParams:
    """
    Represents a set of direct parameters for a statistical model.

    Direct parameters are the parameters that are directly used in the model. They are the parameters that
    are used to define the distribution of the data. In the case of a skew normal distribution, the direct
    parameters are the xi, omega, and alpha values.

    Attributes:
        xi (np.ndarray): The location of the distribution in 2D space, represented as a 2x1 array
            with the x and y coordinates.
        omega (np.ndarray): The covariance matrix of the distribution, represented as a 2x2 array.
            The covariance matrix represents the measure of the relationship between different variables.
            It provides information about how changes in one variable are associated with changes in other variables.
        alpha (np.ndarray): The shape parameters for the x and y dimensions, controlling the shape (skewness) of the distribution.
            It is represented as a 2x1 array.
    """

    def __init__(self, xi: np.ndarray, omega: np.ndarray, alpha: np.ndarray):
        self.xi = xi
        self.omega = omega
        self.alpha = alpha
        self.validate()

    def __repr__(self) -> str:
        return f"DirectParams(xi={self.xi}, omega={self.omega}, alpha={self.alpha})"

    def __str__(self) -> str:
        return (
            f"Direct Parameters:"
            f"\nxi:    {self.xi.round(3)}"
            f"\nomega: {self.omega.round(3)}"
            f"\nalpha: {self.alpha.round(3)}"
        )

    def _omega_is_pos_def(self) -> bool:
        return np.all(np.linalg.eigvals(self.omega) > 0)

    def _omega_is_symmetric(self) -> bool:
        return np.allclose(self.omega, self.omega.T)

    def _xi_is_in_range(self, xi_range: np.ndarray | tuple[float, float]) -> bool:
        if isinstance(xi_range, tuple):
            xi_range = np.array([xi_range, xi_range])
        return np.all((xi_range[:, 0] <= self.xi) & (self.xi <= xi_range[:, 1]))

    def validate(self):
        """
        Validate the direct parameters.

        In a skew normal distribution, the covariance matrix, often denoted as Ω (Omega), represents the 
        measure of the relationship between different variables. It provides information about how changes 
        in one variable are associated with changes in other variables. The covariance matrix must be positive
        definite and symmetric.

        Raises:
            AssertionError: If the direct parameters are not valid.

        Returns:
            None
        """
        assert self._omega_is_pos_def(), "Omega must be positive definite"
        assert self._omega_is_symmetric(), "Omega must be symmetric"


class CentredParams:
    def __init__(self, mean, sigma, skew):
        self.mean = mean
        self.sigma = sigma
        self.skew = skew

    def __repr__(self):
        return f"CentredParams(mean={self.mean}, sigma={self.sigma}, skew={self.skew})"

    def __str__(self) -> str:
        return (
            f"Centred Parameters:"
            f"\nmean:  {self.mean.round(3)}"
            f"\nsigma: {self.sigma.round(3)}"
            f"\nskew:  {self.skew.round(3)}"
        )

    def from_dp(self, dp: DirectParams):
        # TODO: Implement this method with dp2cp function
        pass


class MultiSkewNorm:
    def __init__(self):
        self.selm_model = None
        self.cp = None
        self.dp = None
        self.sample_data = None
        self.data = None

    def __repr__(self):
        if self.cp is None and self.dp is None and self.selm_model is None:
            return "MultiSkewNorm() (unfitted)"
        return f"MultiSkewNorm(dp={self.dp})"

    def summary(self):
        if self.cp is None and self.dp is None and self.selm_model is None:
            return "MultiSkewNorm is not fitted."
        else:
            if self.data is not None:
                print(f"Fitted from data. n = {len(self.data)}")
            else:
                print("Fitted from direct parameters.")
            print(self.dp)
            print("\n")
            print(self.cp)

    def fit(
        self,
        data: pd.DataFrame | np.ndarray = None,
        x: np.ndarray | pd.Series = None,
        y: np.ndarray | pd.Series = None,
    ):
        if data is None and (x is None or y is None):
            # Either data or x and y must be provided
            raise ValueError("Either data or x and y must be provided")

        if data is not None:
            # If data is provided, convert it to a pandas DataFrame
            if isinstance(data, pd.DataFrame):
                # If data is already a DataFrame, no need to convert
                df = data
                df.columns = ["x", "y"]

            else:
                assert x.shape == y.shape, "x and y must have the same shape"

                # Convert data to a DataFrame
                df = pd.DataFrame(data, columns=["x", "y"])

        elif x is not None and y is not None:
            # If x and y are provided, convert them to a pandas DataFrame
            df = pd.DataFrame({"x": x, "y": y})

        else:
            # This should never happen
            raise ValueError("This should never happen")

        # Fit the model
        # TODO: Move the util to this class method rather than having it separate
        m = rsn.selm("x", "y", df)

        # Extract the parameters
        cp = rsn.extract_cp(m)
        dp = rsn.extract_dp(m)

        self.cp = CentredParams(*cp)
        self.dp = DirectParams(*dp)
        self.data = df
        self.selm_model = m

        return None

    def define_dp(self, xi: np.ndarray, omega: np.ndarray, alpha: np.ndarray):
        self.dp = DirectParams(xi, omega, alpha)
        return None

    def sample(self, n: int = 1000, return_sample: bool = False) -> None | np.ndarray:
        if self.selm_model is not None:
            sample = rsn.sample_msn(selm_model=self.selm_model, n=n)
        elif self.dp is not None:
            sample = rsn.sample_msn(
                xi=self.dp.xi, omega=self.dp.omega, alpha=self.dp.alpha, n=n
            )
        else:
            raise ValueError(
                "Either selm_model or xi, omega, and alpha must be provided."
            )

        self.sample_data = sample

        if return_sample:
            return sample

    def sspy_plot(self):
        if self.sample_data is None:
            self.sample()

        df = pd.DataFrame(self.sample_data, columns=["ISOPleasant", "ISOEventful"])
        sspy.plotting.jointplot(
            df,
        )

    def ks2ds(
        self, test: pd.DataFrame | np.ndarray, nboot: int = None, extra: bool = True
    ):
        if self.sample_data is None:
            self.sample()

        if isinstance(test, pd.DataFrame):
            test = test[["ISOPleasant", "ISOEventful"]].values

        return KS2D.ks2d2s(self.sample_data, test)

    def spi(self, test: pd.DataFrame | np.ndarray):
        return int((1 - self.ks2ds(test)[0]) * 100)


# %%

if __name__ == "__main__":
    from pathlib import Path
    from soundscapy.utils.parameters import LANGUAGE_ANGLES, PAQ_IDS

    isd_file = Path("ISD v1.0 Data.csv")
    data = pd.read_csv(isd_file, low_memory=False)
    data, excl_data = sspy.isd.validate(data)
    data = data.query("Language != 'cmn'")

    excl_id = [652, 706, 548, 550, 551, 553, 569, 580, 609, 618, 623, 636, 643]
    data.drop(excl_id, inplace=True)

    for i, row in data.iterrows():
        lang = row["Language"]
        angles = LANGUAGE_ANGLES[lang]
        iso_pl, iso_ev = (
            sspy.surveys.adj_iso_pl(row[PAQ_IDS], angles, scale=4),
            sspy.surveys.adj_iso_ev(row[PAQ_IDS], angles, scale=4),
        )
        data.loc[i, "ISOPleasant"] = iso_pl
        data.loc[i, "ISOEventful"] = iso_ev

    # %%

    ct = data.query("LocationID == 'SanMarco'")
    x = ct["ISOPleasant"].values
    y = ct["ISOEventful"].values

    msn = MultiSkewNorm()
    # msn.fit(x=x, y=y)
    msn.fit(data=ct[["ISOPleasant", "ISOEventful"]])
    msn.summary()
    msn.sspy_plot()

    # %%

    msn2 = MultiSkewNorm()
    msn2.define_dp(
        xi=np.array([0.06534, 0.628637]),
        omega=np.array([[0.14890315, -0.06423752], [-0.06423752, 0.10139612]]),
        alpha=np.array([0.79105, -0.767217]),
    )
    msn2.sample(n=1000, return_sample=True)
    msn2.summary()
    msn2.sspy_plot()

    # %%

    import utils

    utils.spi(pd.DataFrame(msn.sample_data), pd.DataFrame(msn2.sample_data))

    # %%

    fits = []

    for loc in data.LocationID.unique():
        df = data.query(f"LocationID == '{loc}'")[["ISOPleasant", "ISOEventful"]]

        msn = MultiSkewNorm()
        msn.fit(data=df)
        msn.sample()
        fits.append(msn)
