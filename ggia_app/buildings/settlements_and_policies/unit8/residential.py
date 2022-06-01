import pandas as pd


# APARTMENT
# Electricity
def residential_energy_delta(df, country_code, emission_factors_df, start_year,
                             unit_number, completed_from, completed_to):
    data = {}
    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']

    for i in range(start_year, 2051):
        if i < completed_from:
            Electricity = 0
            Gas = 0
            Oil = 0
            Coal = 0
            Peat = 0
            Wood = 0
            Renewable = 0
            Heat = 0
            data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                       round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
        elif completed_from <= i <= completed_to:

            GRID_ELECTRICITY_emission_factora = emission_factors_df[i][0]
            Electricity = GHG_electricitya(nraXa, nraAa, nraBa, BUI_COL275, BUI_COL51, BUI_COL83,
                                           GRID_ELECTRICITY_emission_factora)
            Gas = GHG_gasa(nraXa, nraAa, nraBa, BUI_COL276, BUI_COL52, BUI_COL84, BUI_COL1)
            Oil = GHG_oila(nraXa, nraAa, nraBa, BUI_COL277, BUI_COL53, BUI_COL85, BUI_COL2)
            Coal = GHG_coala(nraXa, nraAa, nraBa, BUI_COL278, BUI_COL54, BUI_COL86, BUI_COL3)
            Peat = GHG_peata(nraXa, nraAa, nraBa, BUI_COL279, BUI_COL55, BUI_COL87, BUI_COL4)
            Wood = GHG_wooda(nraXa, nraAa, nraBa, BUI_COL280, BUI_COL56, BUI_COL88, BUI_COL5)
            Renewable = GHG_renewablea(nraXa, nraAa, nraBa, BUI_COL281, BUI_COL57, BUI_COL89, BUI_COL6)
            DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
            Heat = GHG_heata(nraXa, nraAa, nraBa, BUI_COL282, BUI_COL58, BUI_COL90, DISTRICT_HEATING_emission_factora)
            data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                       round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
        else:
            data[i] = data[i - 1]
    apartment_emission = pd.DataFrame(data)
    apartment_emission.index = energy_carriers
    return apartment_emission


if __name__ == '__main__':
    from pre_process_buildings import *
    from emission_factor_calculator import emission_factor

    # baseLine Inputs
    start_year = 2023
    country = 'Austria'
    country_code = country_map[country]
    emission_factors = emission_factor(df, country_code)
    emission_factors_df = pd.DataFrame(emission_factors)

    # U81 input Retrofits of residental buildings
    selected_residential_unit = 'apartment'
    Number_of_units = 122
    before = 'A'
    after = 'C'
    unit_renewables_percent = 12
    unit_completed_from = 2030
    unit_completed_to = 2032
    energy_delta = residential_energy_delta(before, after)
    print(energy_delta)
