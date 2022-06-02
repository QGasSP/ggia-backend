import pandas as pd


def warehouse_emission(df, country_code, emission_factors_df, start_year, unit_area, completed_from, completed_to):
    annual_increase = round(unit_area / (completed_to - completed_from + 1))
    # Electricity
    BUI_COL347 = df.BUI_COL347[country_code]

    # Gas
    BUI_COL348 = df.BUI_COL348[country_code]
    BUI_COL1 = df.BUI_COL1[country_code]

    # Oil
    BUI_COL349 = df.BUI_COL349[country_code]
    BUI_COL2 = df.BUI_COL2[country_code]

    # Coal
    BUI_COL350 = df.BUI_COL350[country_code]
    BUI_COL3 = df.BUI_COL3[country_code]

    # Peat
    BUI_COL351 = df.BUI_COL19[country_code]
    BUI_COL4 = df.BUI_COL4[country_code]

    # Wood
    BUI_COL352 = df.BUI_COL352[country_code]
    BUI_COL5 = df.BUI_COL5[country_code]

    # Renewable
    BUI_COL353 = df.BUI_COL353[country_code]
    BUI_COL6 = df.BUI_COL6[country_code]

    # Heat
    BUI_COL354 = df.BUI_COL354[country_code]

    demolish_rate = df.BUI_COL11[country_code] / 100
    growth_rate = df.BUI_COL38[country_code] / 100
    data = {}
    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']

    for i in range(start_year, 2051):
        if i == start_year:
            AWaa = unit_area
            demolish_rate = 0
            growth_rate = 0
        else:
            if 2030 < i <= 2040:
                demolish_rate = df.BUI_COL12[country_code] / 100
                growth_rate = df.BUI_COL39[country_code] / 100
            elif i > 2040:
                demolish_rate = df.BUI_COL13[country_code] / 100
                growth_rate = df.BUI_COL40[country_code] / 100

        if i < completed_from:
            AWaa = 0
        elif i == completed_from:
            AWaa = annual_increase
        elif completed_from < i <= completed_to:
            AWaa += annual_increase
        AWaa = (100 - demolish_rate + growth_rate) / 100 * AWaa

        GRID_ELECTRICITY_emission_factora = emission_factors_df[i][0]
        Electricity = AWaa * BUI_COL347 * GRID_ELECTRICITY_emission_factora / 1_000_000
        Gas = AWaa * BUI_COL348 * BUI_COL1 / 1_000_000
        Oil = AWaa * BUI_COL349 * BUI_COL2 / 1_000_000
        Coal = AWaa * BUI_COL350 * BUI_COL3 / 1_000_000
        Peat = AWaa * BUI_COL351 * BUI_COL4 / 1_000_000
        Wood = AWaa * BUI_COL352 * BUI_COL5 / 1_000_000
        Renewable = AWaa * BUI_COL353 * BUI_COL6 / 1_000_000
        DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
        Heat = AWaa * BUI_COL354 * DISTRICT_HEATING_emission_factora / 1_000_000
        data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                   round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
    warehouse_emission = pd.DataFrame(data)
    warehouse_emission.index = energy_carriers
    return warehouse_emission
