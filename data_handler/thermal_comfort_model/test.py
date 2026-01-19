from pythermalcomfort.models import pmv_ppd_iso, utci

def test_comfort_models():
    """Quick sanity check of the comfort model functions."""

    # Calculate PMV and PPD using ISO 7730 standard
    result = pmv_ppd_iso(
        tdb=25,  # Dry Bulb Temperature in °C
        tr=25,  # Mean Radiant Temperature in °C
        vr=0.1,  # Relative air speed in m/s
        rh=50,  # Relative Humidity in %
        met=1.4,  # Metabolic rate in met
        clo=0.5,  # Clothing insulation in clo
        model="7730-2005"  # Year of the ISO standard
    )
    assert result.pmv is not None
    assert result.ppd is not None
    assert -3 <= result.pmv <= 3

    # Calculate UTCI for heat stress assessment
    utci_value = utci(tdb=30, tr=30, v=0.5, rh=50)
    assert utci_value is not None