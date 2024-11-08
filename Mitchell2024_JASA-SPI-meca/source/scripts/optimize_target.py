import argparse
from itertools import product

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import ParameterGrid
from tqdm_pathos import tqdm_pathos

from scripts.MultiSkewNorm import MultiSkewNorm


def target_success(
    target: MultiSkewNorm,
    ranking: pd.Series,
    data: pd.DataFrame,
    group: str = "LocationID",
) -> tuple:
    """
    Calculate the success of a target function by comparing the ranking of groups to the SPI of the target function.

    Parameters
    ----------
    target : MultiSkewNorm
        Target function to evaluate
    ranking : pd.Series
        Ranking of groups
    data : pd.DataFrame
        Data to evaluate the target function on
    group : str
        Column in data to group by

    Returns
    -------
    spearman :
        Spearman correlation between ranking and SPI
    weighted_spi : float
        Weighted sum of SPIs
    spi_ranks : pd.DataFrame
        SPIs and ranks for each group
    target : MultiSkewNorm
        Target function
    """
    assert group in data.columns, f"Group column {group} not in data"
    assert len(ranking.index) == len(
        set(ranking.index)
    ), "Ranking has duplicate indices"
    assert target.sample_data is not None, "Target has not been sampled"

    spis = {}
    for group in ranking.index:
        test_data = data.query("LocationID == @group")
        test_spi = target.spi(test_data[["ISOPleasant", "ISOEventful"]])
        spis[group] = test_spi

    spi_ranks = pd.DataFrame.from_dict(spis, orient="index", columns=["SPI"])
    spi_ranks.sort_values(by="SPI", ascending=False, inplace=True)
    spi_ranks["Rank"] = range(1, len(spi_ranks) + 1)
    ranks = spi_ranks.sort_index()["Rank"]

    spearman = spearmanr(ranking, ranks)
    weighted_spi = sum([(1 / rank) * spi for rank, spi in zip(ranks, spi_ranks["SPI"])])

    return spearman, weighted_spi, spi_ranks, target


def run_grid(
    targets: list[MultiSkewNorm],
    ranking: pd.DataFrame,
    data: pd.DataFrame,
    groups: str = "LocationID",
    parallel: bool = True,
) -> tuple:
    """
    Runs a grid search optimization for a list of targets.

    Args:
        targets (list[MultiSkewNorm]): A list of target objects to optimize.
        ranking (pd.DataFrame): A DataFrame containing the ranking information.
        data (pd.DataFrame): A DataFrame containing the data for optimization.
        groups (str, optional): The column name to group the data by. Defaults to "LocationID".

    Returns:
        tuple: A tuple containing the optimization results for r_res, wspi_res, and targets.
    """
    if parallel:
        results = tqdm_pathos.map(target_success, targets, ranking, data)
    else:
        results = [target_success(target, ranking, data) for target in targets]

    r_res = [res[0][0] for res in results]
    wspi_res = [res[1] for res in results]
    targets = [res[3] for res in results]

    return r_res, wspi_res, targets


def construct_omega_grid(
    variance_range: tuple = (0, 1),
    variance_n: int = 10,
    covariance_range: tuple = (-1, 1),
    covariance_n: int = 10,
):
    """
    Constructs a grid of covariance matrices based on the given variance and covariance ranges.

    Checks that the covariance matrix is symmetric and positive definite before adding it to the grid.

    Args:
        variance_range (tuple, optional): A tuple specifying the range of variances. Defaults to (0, 1).
        variance_n (int, optional): The number of variance values to generate within the range. Defaults to 10.
        covariance_range (tuple, optional): A tuple specifying the range of covariances. Defaults to (-1, 1).
        covariance_n (int, optional): The number of covariance values to generate within the range. Defaults to 10.

    Returns:
        list: A list of covariance matrices that satisfy the conditions.

    """
    variances = np.linspace(variance_range[0], variance_range[1], variance_n)
    covariances = np.linspace(covariance_range[0], covariance_range[1], covariance_n)

    omega_grid = []
    for var1, var2, cov in product(variances, variances, covariances):
        covariance_matrix = np.array([[var1, cov], [cov, var2]])
        if np.allclose(covariance_matrix, covariance_matrix.T) and np.all(
            np.linalg.eigvals(covariance_matrix) > 0
        ):
            omega_grid.append(covariance_matrix)

    return omega_grid


def construct_target(params, n=100):
    """
    Construct a target using the given parameters.

    Args:
        params (dict): A dictionary containing the parameters for constructing the target.
            - "xi_x" (float): The x-coordinate of the skewness parameter.
            - "xi_y" (float): The y-coordinate of the skewness parameter.
            - "omega" (float): The scale parameter.
            - "alpha_x" (float): The x-coordinate of the shape parameter.
            - "alpha_y" (float): The y-coordinate of the shape parameter.
        n (int, optional): The number of samples to generate. Defaults to 100.

    Returns:
        MultiSkewNorm: The constructed target.

    Raises:
        AssertionError: If the parameters fail validation.

    """
    tgt = MultiSkewNorm()
    try:
        # Catch the errors raised by DirectParams.validate()
        # If dp doesn't pass validation,xi don't append it to the list
        tgt.define_dp(
            xi=np.array([params["xi_x"], params["xi_y"]]),
            omega=params["omega"],
            alpha=np.array([params["alpha_x"], params["alpha_y"]]),
        )
    except AssertionError:
        return None

    tgt.sample(n=n)
    return tgt


def construct_target_grid(
    omega_grid: list[np.ndarray],
    xi_range: tuple = (0, 1),
    xi_n: int = 10,
    alpha_range: tuple = (0, 1),
    alpha_n: int = 10,
    sample_n: int = 100,
    parallel: bool = True,
) -> list[MultiSkewNorm]:
    """
    Constructs a grid of MSN targets based on the given parameters.

    Parameters:
    - omega_grid (list[np.ndarray]): A list of numpy arrays representing the omega grid.
    - xi_range (tuple, optional): A tuple specifying the range of xi values. Defaults to (0, 1).
    - xi_n (int, optional): The number of xi values to generate. Defaults to 10.
    - alpha_range (tuple, optional): A tuple specifying the range of alpha values. Defaults to (0, 1).
    - alpha_n (int, optional): The number of alpha values to generate. Defaults to 10.
    - sample_n (int, optional): The number of samples to generate for each parameter combination. Defaults to 100.
    - parallel (bool, optional): Whether to use parallel processing. Defaults to True.

    Returns:
    - targets (list[MultiSkewNorm]): A list of MSN targets generated based on the given parameters.
    """
    param_grid = {
        "xi_x": np.linspace(xi_range[0], xi_range[1], xi_n),
        "xi_y": np.linspace(xi_range[0], xi_range[1], xi_n),
        "omega": omega_grid,
        "alpha_x": np.linspace(alpha_range[0], alpha_range[1], alpha_n),
        "alpha_y": np.linspace(alpha_range[0], alpha_range[1], alpha_n),
    }
    grid = ParameterGrid(param_grid)

    if parallel:
        targets = tqdm_pathos.map(construct_target, grid, n=sample_n)
    else:
        targets = [construct_target(params, n=sample_n) for params in grid]

    return targets


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Grid Search CLI")
    parser.add_argument(
        "--variance_range",
        type=float,
        nargs=2,
        default=[0, 1],
        help="Range of variances",
    )
    parser.add_argument(
        "--variance_n", type=int, default=10, help="Number of variance values"
    )
    parser.add_argument(
        "--covariance_range",
        type=float,
        nargs=2,
        default=[-1, 1],
        help="Range of covariances",
    )
    parser.add_argument(
        "--covariance_n", type=int, default=10, help="Number of covariance values"
    )
    parser.add_argument(
        "--xi_range", type=float, nargs=2, default=[0, 1], help="Range of xi values"
    )
    parser.add_argument("--xi_n", type=int, default=10, help="Number of xi values")
    parser.add_argument(
        "--alpha_range",
        type=float,
        nargs=2,
        default=[0, 1],
        help="Range of alpha values",
    )
    parser.add_argument(
        "--alpha_n", type=int, default=10, help="Number of alpha values"
    )
    parser.add_argument("--sample_n", type=int, default=100, help="Number of samples")
    parser.add_argument("--parallel", action="store_true", help="Run in parallel")
    args = parser.parse_args()

    # Construct omega grid
    omega_grid = construct_omega_grid(
        variance_range=args.variance_range,
        variance_n=args.variance_n,
        covariance_range=args.covariance_range,
        covariance_n=args.covariance_n,
    )

    # Construct target grid
    targets = construct_target_grid(
        omega_grid=omega_grid,
        xi_range=args.xi_range,
        xi_n=args.xi_n,
        alpha_range=args.alpha_range,
        alpha_n=args.alpha_n,
        sample_n=args.sample_n,
        parallel=args.parallel,
    )

    # Define ranking and data
    ranking = pd.Series([1, 2, 3, 4, 5])
    data = pd.DataFrame(
        {
            "LocationID": [1, 2, 3, 4, 5],
            "ISOPleasant": [0.1, 0.2, 0.3, 0.4, 0.5],
            "ISOEventful": [0.5, 0.4, 0.3, 0.2, 0.1],
        }
    )

    # Run grid search
    r_res, wspi_res, targets = run_grid(targets, ranking, data)
