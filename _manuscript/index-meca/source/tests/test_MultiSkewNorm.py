import numpy as np
import pandas as pd
import pytest
from MultiSkewNorm import MultiSkewNorm, DirectParams, CentredParams

def test_multiskewnorm_init():
    msn = MultiSkewNorm()
    assert msn.selm_model is None
    assert msn.cp is None
    assert msn.dp is None
    assert msn.sample_data is None
    assert msn.data is None

def test_multiskewnorm_repr():
    msn = MultiSkewNorm()
    assert repr(msn) == "MultiSkewNorm() (unfitted)"

    msn.dp = DirectParams(np.array([1, 2, 3]), np.array([0.5, 0.6, 0.7]), np.array([0.1, 0.2, 0.3]))
    assert repr(msn) == "MultiSkewNorm(dp=DirectParams(xi=array([1, 2, 3]), omega=array([0.5, 0.6, 0.7]), alpha=array([0.1, 0.2, 0.3])))"

def test_multiskewnorm_summary():
    msn = MultiSkewNorm()
    assert msn.summary() == "MultiSkewNorm is not fitted."

    msn.dp = DirectParams(np.array([1, 2, 3]), np.array([0.5, 0.6, 0.7]), np.array([0.1, 0.2, 0.3]))
    msn.data = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    expected_output = "Fitted from data. n = 3\nDirectParams(xi=array([1, 2, 3]), omega=array([0.5, 0.6, 0.7]), alpha=array([0.1, 0.2, 0.3]))\n\nNone"
    assert msn.summary() == expected_output

def test_multiskewnorm_fit():
    msn = MultiSkewNorm()

    # Test with data provided as a DataFrame
    data = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    msn.fit(data=data)
    assert isinstance(msn.selm_model, rsn.selm)
    assert isinstance(msn.cp, CentredParams)
    assert isinstance(msn.dp, DirectParams)
    assert isinstance(msn.data, pd.DataFrame)

    # Test with data provided as numpy arrays
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    msn.fit(x=x, y=y)
    assert isinstance(msn.selm_model, rsn.selm)
    assert isinstance(msn.cp, CentredParams)
    assert isinstance(msn.dp, DirectParams)
    assert isinstance(msn.data, pd.DataFrame)

    # Test with missing data
    with pytest.raises(ValueError):
        msn.fit()

def test_multiskewnorm_define_dp():
    msn = MultiSkewNorm()
    xi = np.array([1, 2, 3])
    omega = np.array([0.5, 0.6, 0.7])
    alpha = np.array([0.1, 0.2, 0.3])
    msn.define_dp(xi=xi, omega=omega, alpha=alpha)
    assert isinstance(msn.dp, DirectParams)

def test_multiskewnorm_sample():
    msn = MultiSkewNorm()
    msn.dp = DirectParams(np.array([1, 2, 3]), np.array([0.5, 0.6, 0.7]), np.array([0.1, 0.2, 0.3]))

    # Test sample generation
    msn.sample(n=1000)
    assert isinstance(msn.sample_data, np.ndarray)
    assert msn.sample_data.shape == (1000, 2)

    # Test returning the sample
    sample = msn.sample(n=1000, return_sample=True)
    assert isinstance(sample, np.ndarray)
    assert sample.shape == (1000, 2)

def test_multiskewnorm_sspy_plot():
    msn = MultiSkewNorm()
    msn.sample_data = np.random.rand(1000, 2)
    msn.sspy_plot()  # No assertion, just checking if it runs without errors

def test_multiskewnorm_ks2ds():
    msn = MultiSkewNorm()
    msn.sample_data = np.random.rand(1000, 2)

    # Test with test data provided as a DataFrame
    test_data = pd.DataFrame({"ISOPleasant": np.random.rand(1000), "ISOEventful": np.random.rand(1000)})
    ks2ds_result = msn.ks2ds(test=test_data)
    assert isinstance(ks2ds_result, tuple)
    assert len(ks2ds_result) == 2

    # Test with test data provided as numpy arrays
    test_data = np.random.rand(1000, 2)
    ks2ds_result = msn.ks2ds(test=test_data)
    assert isinstance(ks2ds_result, tuple)
    assert len(ks2ds_result) == 2

def test_multiskewnorm_spi():
    msn = MultiSkewNorm()
    msn.sample_data = np.random.rand(1000, 2)

    # Test with test data provided as a DataFrame
    test_data = pd.DataFrame({"ISOPleasant": np.random.rand(1000), "ISOEventful": np.random.rand(1000)})
    spi_result = msn.spi(test=test_data)
    assert isinstance(spi_result, int)

    # Test with test data provided as numpy arrays
    test_data = np.random.rand(1000, 2)
    spi_result = msn.spi(test=test_data)
    assert isinstance(spi_result, int)