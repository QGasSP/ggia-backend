import pandas as pd


def health_emission_calculator(df, country_code, emission_factors_df, start_year, unit_area):
    # Electricity
    BUI_COL315 = df.BUI_COL315[country_code]

    # Gas
    BUI_COL316 = df.BUI_COL316[country_code]
    BUI_COL1 = df.BUI_COL1[country_code]

    # Oil
    BUI_COL317 = df.BUI_COL317[country_code]
    BUI_COL2 = df.BUI_COL2[country_code]

    # Coal
    BUI_COL318 = df.BUI_COL318[country_code]
    BUI_COL3 = df.BUI_COL3[country_code]

    # Peat
    BUI_COL319 = df.BUI_COL19[country_code]
    BUI_COL4 = df.BUI_COL4[country_code]

    # Wood
    BUI_COL320 = df.BUI_COL320[country_code]
    BUI_COL5 = df.BUI_COL5[country_code]

    # Renewable
    BUI_COL321 = df.BUI_COL321[country_code]
    BUI_COL6 = df.BUI_COL6[country_code]

    # Heat
    BUI_COL322 = df.BUI_COL322[country_code]

    demolish_rate = df.BUI_COL11[country_code] / 100
    growth_rate = df.BUI_COL38[country_code] / 100
    data = {}
    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']

    for i in range(start_year, 2051):
        if i == start_year:
            AHea = unit_area
            demolish_rate = 0
            growth_rate = 0
        else:
            if 2030 < i <= 2040:
                demolish_rate = df.BUI_COL12[country_code] / 100
                growth_rate = df.BUI_COL39[country_code] / 100
            elif i > 2040:
                demolish_rate = df.BUI_COL13[country_code] / 100
                growth_rate = df.BUI_COL40[country_code] / 100
        AHea = (100 - demolish_rate + growth_rate) / 100 * AHea

        GRID_ELECTRICITY_emission_factora = emission_factors_df[i][0]
        Electricity = AHea * BUI_COL315 * GRID_ELECTRICITY_emission_factora / 1_000_000
        Gas = AHea * BUI_COL316 * BUI_COL1 / 1_000_000
        Oil = AHea * BUI_COL317 * BUI_COL2 / 1_000_000
        Coal = AHea * BUI_COL318 * BUI_COL3 / 1_000_000
        Peat = AHea * BUI_COL319 * BUI_COL4 / 1_000_000
        Wood = AHea * BUI_COL320 * BUI_COL5 / 1_000_000
        Renewable = AHea * BUI_COL321 * BUI_COL6 / 1_000_000
        DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
        Heat = AHea * BUI_COL322 * DISTRICT_HEATING_emission_factora / 1_000_000
        data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                   round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
    health_emission = pd.DataFrame(data)
    health_emission.index = energy_carriers
    return health_emission
