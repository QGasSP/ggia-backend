from .apartment import apartment_emission as _apartment_emission
from .terraced_units import terraced_emission as _terraced_emission
from .semi_detach import semi_detach_emission as _semi_detach_emission
from .detached import detach_emission as _detach_emission


def u71_emission(
        df, country_code, emission_factors_df, start_year,
        apartment_units_number, apartment_completed_from,
        apartment_completed_to, apartment_renewables_percent,
        terraced_units_number, terraced_completed_from,
        terraced_completed_to, terraced_renewables_percent,
        semi_detached_units_number, semi_detached_completed_from,
        semi_detached_completed_to, semi_detached_renewables_percent,
        detached_units_number, detached_completed_from,
        detached_completed_to, detached_renewables_percent
):
    apartment_after_renewable = (100 - apartment_renewables_percent) / 100
    apartment_emission = apartment_after_renewable * _apartment_emission(
        df, country_code, emission_factors_df, start_year,
        apartment_units_number, apartment_completed_from, apartment_completed_to)

    terraced_after_renewable = (100 - terraced_renewables_percent) / 100
    terraced_emission = terraced_after_renewable * _terraced_emission(
        df, country_code, emission_factors_df, start_year,
        terraced_units_number, terraced_completed_from, terraced_completed_to)

    semi_detached_after_renewable = (100 - semi_detached_renewables_percent) / 100
    semi_detached_emission = semi_detached_after_renewable * _semi_detach_emission(
        df, country_code, emission_factors_df, start_year,
        semi_detached_units_number, semi_detached_completed_from, semi_detached_completed_to
    )

    detached_after_renewable = (100 - detached_renewables_percent) / 100
    detached_emission = detached_after_renewable * _detach_emission(
        df, country_code, emission_factors_df, start_year,
        detached_units_number, detached_completed_from, detached_completed_to)
    return apartment_emission, terraced_emission, semi_detached_emission, detached_emission
