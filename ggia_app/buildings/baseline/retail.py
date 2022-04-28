import pandas as pd


def retail_emission_calculator(df, country_code, emission_factors_df, start_year, unit_area):
    # Electricity
    BUI_COL307 = df.BUI_COL307[country_code]

    # Gas
    BUI_COL308 = df.BUI_COL308[country_code]
    BUI_COL1 = df.BUI_COL1[country_code]

    # Oil
    BUI_COL309 = df.BUI_COL309[country_code]
    BUI_COL2 = df.BUI_COL2[country_code]

    # Coal
    BUI_COL310 = df.BUI_COL310[country_code]
    BUI_COL3 = df.BUI_COL3[country_code]

    # Peat
    BUI_COL311 = df.BUI_COL19[country_code]
    BUI_COL4 = df.BUI_COL4[country_code]

    # Wood
    BUI_COL312 = df.BUI_COL312[country_code]
    BUI_COL5 = df.BUI_COL5[country_code]

    # Renewable
    BUI_COL313 = df.BUI_COL313[country_code]
    BUI_COL6 = df.BUI_COL6[country_code]

    # Heat
    BUI_COL314 = df.BUI_COL314[country_code]

    demolish_rate = df.BUI_COL11[country_code] / 100
    growth_rate = df.BUI_COL38[country_code] / 100
    data = {}
    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']

    for i in range(start_year, 2051):
        if i == start_year:
            ARea = unit_area
            demolish_rate = 0
            growth_rate = 0
        else:
            if 2030 < i <= 2040:
                demolish_rate = df.BUI_COL12[country_code] / 100
                growth_rate = df.BUI_COL39[country_code] / 100
            elif i > 2040:
                demolish_rate = df.BUI_COL13[country_code] / 100
                growth_rate = df.BUI_COL40[country_code] / 100
        ARea = (100 - demolish_rate + growth_rate) / 100 * ARea

        GRID_ELECTRICITY_emission_factora = emission_factors_df[i][0]
        Electricity = ARea * BUI_COL307 * GRID_ELECTRICITY_emission_factora / 1_000_000
        Gas = ARea * BUI_COL308 * BUI_COL1 / 1_000_000
        Oil = ARea * BUI_COL309 * BUI_COL2 / 1_000_000
        Coal = ARea * BUI_COL310 * BUI_COL3 / 1_000_000
        Peat = ARea * BUI_COL311 * BUI_COL4 / 1_000_000
        Wood = ARea * BUI_COL312 * BUI_COL5 / 1_000_000
        Renewable = ARea * BUI_COL313 * BUI_COL6 / 1_000_000
        DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
        Heat = ARea * BUI_COL314 * DISTRICT_HEATING_emission_factora / 1_000_000
        data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                   round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
    retail_emission = pd.DataFrame(data)
    retail_emission.index = energy_carriers
    return retail_emission
