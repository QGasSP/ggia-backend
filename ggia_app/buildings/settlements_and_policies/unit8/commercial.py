import pandas as pd

commercial_helper = {'Retail': 1, 'Health': 2, 'Hospitality': 3, 'Offices': 4, 'Industrial': 5, 'Warehouses': 6}


def BUI(df, selected_commercial_unit, country_code):
    bui = f'BUI_COL{307 + ((commercial_helper[selected_commercial_unit] - 1) * 8)}'
    return df[bui][country_code]


def emission(df, selected_commercial_unit, country_code, emission_factor, floor_area, energy_demand_reduction,
             unit_renewables_percent, unit_completed_to, unit_completed_from):
    energy_cons_before = BUI(df, selected_commercial_unit, country_code)
    energy_cons_after = energy_cons_before * (100 - energy_demand_reduction) / 100
    return (floor_area * ((energy_cons_before * energy_demand_reduction / 100) + (
            unit_renewables_percent / 100 * energy_cons_after)) * emission_factor / (unit_completed_to - unit_completed_from + 1) / 1000000)


def commercial_emission(df, country_code, emission_factors_df, start_year, selected_commercial_unit, floor_area,
                        energy_demand_reduction, unit_renewables_percent, unit_completed_from, unit_completed_to):
    data = {}
    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']

    last_Electricity = 0
    last_Gas = 0
    last_Oil = 0
    last_Coal = 0
    last_Peat = 0
    last_Wood = 0
    last_Renewable = 0
    last_Heat = 0
    for i in range(start_year, 2051):
        if unit_completed_from <= i <= unit_completed_to:
            GRID_ELECTRICITY_emission_factora = emission_factors_df[i][0]
            Electricity = last_Electricity + emission(df, selected_commercial_unit, country_code,
                                                      GRID_ELECTRICITY_emission_factora, floor_area,
                                                      energy_demand_reduction,
                                                      unit_renewables_percent, unit_completed_to, unit_completed_from)
            Gas = last_Gas + emission(df, selected_commercial_unit, country_code, df.BUI_COL1[country_code], floor_area,
                                      energy_demand_reduction,
                                      unit_renewables_percent, unit_completed_to, unit_completed_from)
            Oil = last_Oil + emission(df, selected_commercial_unit, country_code, df.BUI_COL2[country_code], floor_area,
                                      energy_demand_reduction,
                                      unit_renewables_percent, unit_completed_to, unit_completed_from)
            Coal = last_Coal + emission(df, selected_commercial_unit, country_code, df.BUI_COL3[country_code],
                                        floor_area, energy_demand_reduction,
                                        unit_renewables_percent, unit_completed_to, unit_completed_from)
            Peat = last_Peat + emission(df, selected_commercial_unit, country_code, df.BUI_COL4[country_code],
                                        floor_area, energy_demand_reduction,
                                        unit_renewables_percent, unit_completed_to, unit_completed_from)
            Wood = last_Wood + emission(df, selected_commercial_unit, country_code, df.BUI_COL5[country_code],
                                        floor_area, energy_demand_reduction,
                                        unit_renewables_percent, unit_completed_to, unit_completed_from)
            Renewable = last_Renewable + emission(df, selected_commercial_unit, country_code, df.BUI_COL6[country_code],
                                                  floor_area, energy_demand_reduction,
                                                  unit_renewables_percent, unit_completed_to, unit_completed_from)
            DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
            Heat = last_Heat + emission(df, selected_commercial_unit, country_code, DISTRICT_HEATING_emission_factora,
                                        floor_area, energy_demand_reduction,
                                        unit_renewables_percent, unit_completed_to, unit_completed_from)
        data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                   round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
        last_Electricity = Electricity
        last_Gas = Gas
        last_Oil = Oil
        last_Coal = Coal
        last_Peat = Peat
        last_Wood = Wood
        last_Renewable = Renewable
        last_Heat = Heat

    retrofit_emission = pd.DataFrame(data)
    retrofit_emission.index = energy_carriers
    return retrofit_emission
