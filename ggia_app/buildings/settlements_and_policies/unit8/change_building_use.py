import pandas as pd

building_helper = {'Apartment': 1, 'Terraced': 2, 'Semidetached': 3, 'Detached': 4, 'Retail': 5,
                   'Health': 6,
                   'Hospitality': 7, 'Offices': 8, 'Industrial': 9, 'Warehouses': 10}


def BUI(df, from_unit, country_code):
    bui = f'BUI_COL{275 + ((building_helper[from_unit] - 1) * 8)}'
    return df[bui][country_code]


def emission(emission_factor, df, country_code, floor_area, from_unit,
             unit_completed_to, unit_completed_from):
    if from_unit == 'Apartment':
        floor_area = df.BUI_COL42[country_code] * floor_area
    if from_unit == 'Terraced':
        floor_area = df.BUI_COL43[country_code] * floor_area
    if from_unit == 'Semidetached':
        floor_area = df.BUI_COL44[country_code] * floor_area
    if from_unit == 'Detached':
        floor_area = df.BUI_COL45[country_code] * floor_area

    energy_cons = BUI(df, from_unit, country_code)
    new_emission = (floor_area * energy_cons * emission_factor / (
            unit_completed_to - unit_completed_from + 1) / 1000000)
    return new_emission


def building_emission(df, country_code, emission_factors_df, start_year, floor_area,
                      from_unit, unit_completed_from, unit_completed_to, to_unit):
    emission_data = {
        'df': df, 'country_code': country_code, 'floor_area': floor_area, 'from_unit': from_unit,
        'unit_completed_to': unit_completed_to, 'unit_completed_from': unit_completed_from
    }

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
            Electricity = last_Electricity + emission(GRID_ELECTRICITY_emission_factora,
                                                      **emission_data)
            Gas = last_Gas + emission(df.BUI_COL1[country_code], **emission_data)
            Oil = last_Oil + emission(df.BUI_COL2[country_code], **emission_data)
            Coal = last_Coal + emission(df.BUI_COL3[country_code], **emission_data)
            Peat = last_Peat + emission(df.BUI_COL4[country_code], **emission_data)
            Wood = last_Wood + emission(df.BUI_COL5[country_code], **emission_data)
            Renewable = last_Renewable + emission(df.BUI_COL6[country_code], **emission_data)
            DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
            Heat = last_Heat + emission(DISTRICT_HEATING_emission_factora, **emission_data)
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
