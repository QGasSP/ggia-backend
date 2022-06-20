import pandas as pd

residential_helper = {'Apartment': 1, 'Terraced': 2, 'Semidetached': 3, 'Detached': 4}
energy_indicator_helper = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7}


def BUI(df, selected_residential_unit, energy_indicator_helper_item, country_code):
    bui = f'BUI_COL{(51 + ((residential_helper[selected_residential_unit] - 1) * 8) + ((energy_indicator_helper[energy_indicator_helper_item] - 1) * 32))}'
    return df[bui][country_code]


def emission(df, selected_residential_unit, before, after, country_code, emission_factor, Number_of_units,
             unit_renewables_percent, unit_completed_to, unit_completed_from):
    new_emission = Number_of_units * (BUI(df, selected_residential_unit, before, country_code)
                                      - BUI(df, selected_residential_unit, after, country_code)  # energy consAFTER
                                      + unit_renewables_percent / 100 * BUI(df, selected_residential_unit, after,
                                                                            country_code)) * \
                   emission_factor / (unit_completed_to - unit_completed_from + 1) / 1000000
    return (new_emission)


def residential_emission(df, country_code, emission_factors_df, start_year, selected_residential_unit, Number_of_units,
                         before, after, unit_renewables_percent, unit_completed_from, unit_completed_to):
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
            Electricity = last_Electricity + emission(df, selected_residential_unit, before, after,
                                                      country_code, GRID_ELECTRICITY_emission_factora, Number_of_units,
                                                      unit_renewables_percent, unit_completed_to,
                                                      unit_completed_from)
            Gas = last_Gas + emission(df, selected_residential_unit, before, after,
                                      country_code, df.BUI_COL1[country_code], Number_of_units,
                                      unit_renewables_percent, unit_completed_to,
                                      unit_completed_from)
            Oil = last_Oil + emission(df, selected_residential_unit, before, after,
                                      country_code, df.BUI_COL2[country_code], Number_of_units,
                                      unit_renewables_percent, unit_completed_to,
                                      unit_completed_from)
            Coal = last_Coal + emission(df, selected_residential_unit, before, after,
                                        country_code, df.BUI_COL3[country_code], Number_of_units,
                                        unit_renewables_percent, unit_completed_to,
                                        unit_completed_from)
            Peat = last_Peat + emission(df, selected_residential_unit, before, after,
                                        country_code, df.BUI_COL4[country_code], Number_of_units,
                                        unit_renewables_percent, unit_completed_to,
                                        unit_completed_from)
            Wood = last_Wood + emission(df, selected_residential_unit, before, after,
                                        country_code, df.BUI_COL5[country_code], Number_of_units,
                                        unit_renewables_percent, unit_completed_to,
                                        unit_completed_from)
            Renewable = last_Renewable + emission(df, selected_residential_unit, before, after,
                                                  country_code, df.BUI_COL6[country_code], Number_of_units,
                                                  unit_renewables_percent, unit_completed_to,
                                                  unit_completed_from)
            DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
            Heat = last_Heat + emission(df, selected_residential_unit, before, after,
                                        country_code, DISTRICT_HEATING_emission_factora, Number_of_units,
                                        unit_renewables_percent, unit_completed_to,
                                        unit_completed_from)
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
