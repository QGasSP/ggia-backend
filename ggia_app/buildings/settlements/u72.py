from .apartment import apartment_emission as mother


def u72_emission(
        df, country_code, emission_factors_df, start_year,
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
    retail_after_renewable = (100 - retail_renewables_percent) / 100
    retail_emission = retail_after_renewable * mother(
        df, country_code, emission_factors_df, start_year,
        retail_floor_area, retail_completed_from, retail_completed_to
    )

    health_after_renewable = (100 - health_renewables_percent) / 100
    health_emission = health_after_renewable * mother(
        df, country_code, emission_factors_df, start_year,
        health_floor_area, health_completed_from, health_completed_to
    )

    hospitality_after_renewable = (100 - hospitality_renewables_percent) / 100
    hospitality_emission = hospitality_after_renewable * mother(
        df, country_code, emission_factors_df, start_year,
        hospitality_floor_area, hospitality_completed_from, hospitality_completed_to
    )

    offices_after_renewable = (100 - offices_renewables_percent) / 100
    offices_emission = offices_after_renewable * mother(
        df, country_code, emission_factors_df, start_year,
        offices_floor_area, offices_completed_from, offices_completed_to
    )

    industrial_after_renewable = (100 - industrial_renewables_percent) / 100
    industrial_emission = industrial_after_renewable * mother(
        df, country_code, emission_factors_df, start_year,
        industrial_floor_area, industrial_completed_from, industrial_completed_to
    )

    warehouses_after_renewable = (100 - warehouses_renewables_percent) / 100
    warehouses_emission = warehouses_after_renewable * mother(
        df, country_code, emission_factors_df, start_year,
        warehouses_floor_area, warehouses_completed_from, warehouses_completed_to
    )
    return (
        retail_emission,
        health_emission,
        hospitality_emission,
        offices_emission,
        industrial_emission,
        warehouses_emission
    )
