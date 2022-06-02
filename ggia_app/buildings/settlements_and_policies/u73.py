from .unit7.apartment import apartment_emission as _apartment_emission
from .unit7.terraced_units import terraced_emission as _terraced_emission
from .unit7.semi_detach import semi_detach_emission as _semi_detach_emission
from .unit7.detached import detach_emission as _detach_emission
from .unit7.retail import retail_emission as _retail_emission
from .unit7.health import health_emission as _health_emission
from .unit7.hospitality import hospitality_emission as _hospitality_emission
from .unit7.office import office_emission as _office_emission
from .unit7.industrial import industrial_emission as _industrial_emission
from .unit7.warehouse import warehouse_emission as _warehouse_emission


def u73_emission(
        df, country_code, emission_factors_df, start_year,
        apartment_units_number, apartment_completed_from, apartment_completed_to,
        apartment_renewables_percent,
        terraced_units_number, terraced_completed_from, terraced_completed_to,
        terraced_renewables_percent,
        semi_detached_units_number, semi_detached_completed_from, semi_detached_completed_to,
        semi_detached_renewables_percent,
        detached_units_number, detached_completed_from, detached_completed_to,
        detached_renewables_percent,
        retail_floor_area, retail_completed_from, retail_completed_to, retail_renewables_percent,
        health_floor_area, health_completed_from, health_completed_to, health_renewables_percent,
        hospitality_floor_area, hospitality_completed_from, hospitality_completed_to,
        hospitality_renewables_percent,
        offices_floor_area, offices_completed_from, offices_completed_to,
        offices_renewables_percent,
        industrial_floor_area, industrial_completed_from, industrial_completed_to,
        industrial_renewables_percent,
        warehouses_floor_area, warehouses_completed_from, warehouses_completed_to,
        warehouses_renewables_percent
):
    apartment_after_renewable = (100 - apartment_renewables_percent) / 100
    apartment_emission = apartment_after_renewable * _apartment_emission(
        df, country_code, emission_factors_df, start_year,
        apartment_units_number, apartment_completed_from, apartment_completed_to
    )

    terraced_after_renewable = (100 - terraced_renewables_percent) / 100
    terraced_emission = terraced_after_renewable * _terraced_emission(
        df, country_code, emission_factors_df, start_year,
        terraced_units_number, terraced_completed_from, terraced_completed_to
    )

    semi_detached_after_renewable = (100 - semi_detached_renewables_percent) / 100
    semi_detached_emission = semi_detached_after_renewable * _semi_detach_emission(
        df, country_code, emission_factors_df, start_year,
        semi_detached_units_number, semi_detached_completed_from, semi_detached_completed_to
    )

    detached_after_renewable = (100 - detached_renewables_percent) / 100
    detached_emission = detached_after_renewable * _detach_emission(
        df, country_code, emission_factors_df, start_year,
        detached_units_number, detached_completed_from, detached_completed_to
    )

    retail_after_renewable = (100 - retail_renewables_percent) / 100
    retail_emission = retail_after_renewable * _retail_emission(
        df, country_code, emission_factors_df, start_year,
        retail_floor_area, retail_completed_from, retail_completed_to
    )

    health_after_renewable = (100 - health_renewables_percent) / 100
    health_emission = health_after_renewable * _health_emission(
        df, country_code, emission_factors_df, start_year,
        health_floor_area, health_completed_from, health_completed_to
    )

    hospitality_after_renewable = (100 - hospitality_renewables_percent) / 100
    hospitality_emission = hospitality_after_renewable * _hospitality_emission(
        df, country_code, emission_factors_df, start_year,
        hospitality_floor_area, hospitality_completed_from, hospitality_completed_to
    )

    offices_after_renewable = (100 - offices_renewables_percent) / 100
    offices_emission = offices_after_renewable * _office_emission(
        df, country_code, emission_factors_df, start_year,
        offices_floor_area, offices_completed_from, offices_completed_to
    )

    industrial_after_renewable = (100 - industrial_renewables_percent) / 100
    industrial_emission = industrial_after_renewable * _industrial_emission(
        df, country_code, emission_factors_df, start_year,
        industrial_floor_area, industrial_completed_from, industrial_completed_to
    )

    warehouses_after_renewable = (100 - warehouses_renewables_percent) / 100
    warehouses_emission = warehouses_after_renewable * _warehouse_emission(
        df, country_code, emission_factors_df, start_year,
        warehouses_floor_area, warehouses_completed_from, warehouses_completed_to
    )

    return (
        apartment_emission, terraced_emission, semi_detached_emission, detached_emission,
        retail_emission, health_emission, hospitality_emission, offices_emission,
        industrial_emission, warehouses_emission
    )
