import pandas as pd


# APARTMENT
# Electricity
def apartment_emission(df, country_code, emission_factors_df, start_year, unit_number, completed_from, completed_to):
    annual_increase = round(unit_number / (completed_to - completed_from + 1))

    BUI_COL275 = df.BUI_COL275[country_code]
    BUI_COL51 = df.BUI_COL51[country_code]
    BUI_COL83 = df.BUI_COL83[country_code]

    def GHG_electricitya(nraXa, nraAa, nraBa, BUI_COL275, BUI_COL51, BUI_COL83, GRID_ELECTRICITY_emission_factora):
        electricity = (((nraXa * BUI_COL275) + (nraAa * BUI_COL51) + (
                nraBa * BUI_COL83)) * GRID_ELECTRICITY_emission_factora) / 1_000_000
        return electricity

    # Heat
    BUI_COL282 = df.BUI_COL282[country_code]
    BUI_COL58 = df.BUI_COL58[country_code]
    BUI_COL90 = df.BUI_COL90[country_code]

    def GHG_heata(nraXa, nraAa, nraBa, BUI_COL282, BUI_COL58, BUI_COL90, DISTRICT_HEATING_emission_factora=350):
        heat = (((nraXa * BUI_COL282) + (nraAa * BUI_COL58) + (
                nraBa * BUI_COL90)) * DISTRICT_HEATING_emission_factora) / 1_000_000
        return heat

    # Gas
    BUI_COL276 = df.BUI_COL276[country_code]
    BUI_COL52 = df.BUI_COL52[country_code]
    BUI_COL84 = df.BUI_COL84[country_code]
    BUI_COL1 = df.BUI_COL1[country_code]

    def GHG_gasa(nraXa, nraAa, nraBa, BUI_COL276, BUI_COL52, BUI_COL84, BUI_COL1):
        gas = (((nraXa * BUI_COL276) + (nraAa * BUI_COL52) + (nraBa * BUI_COL84)) * BUI_COL1) / 1_000_000
        return gas

    # Oil
    BUI_COL277 = df.BUI_COL277[country_code]
    BUI_COL53 = df.BUI_COL53[country_code]
    BUI_COL85 = df.BUI_COL85[country_code]
    BUI_COL2 = df.BUI_COL2[country_code]

    def GHG_oila(nraXa, nraAa, nraBa, BUI_COL277, BUI_COL53, BUI_COL85, BUI_COL2):
        oil = (((nraXa * BUI_COL277) + (nraAa * BUI_COL53) + (nraBa * BUI_COL85)) * BUI_COL2) / 1_000_000
        return oil

    # Coal
    BUI_COL278 = df.BUI_COL278[country_code]
    BUI_COL54 = df.BUI_COL54[country_code]
    BUI_COL86 = df.BUI_COL86[country_code]
    BUI_COL3 = df.BUI_COL3[country_code]

    def GHG_coala(nraXa, nraAa, nraBa, BUI_COL278, BUI_COL54, BUI_COL86, BUI_COL3):
        coal = (((nraXa * BUI_COL278) + (nraAa * BUI_COL54) + (nraBa * BUI_COL86)) * BUI_COL3) / 1_000_000
        return coal

    # Peat
    BUI_COL279 = df.BUI_COL279[country_code]
    BUI_COL55 = df.BUI_COL55[country_code]
    BUI_COL87 = df.BUI_COL87[country_code]
    BUI_COL4 = df.BUI_COL4[country_code]

    def GHG_peata(nraXa, nraAa, nraBa, BUI_COL279, BUI_COL55, BUI_COL87, BUI_COL4):
        peat = (((nraXa * BUI_COL279) + (nraAa * BUI_COL55) + (nraBa * BUI_COL87)) * BUI_COL4) / 1_000_000
        return peat

    # Wood
    BUI_COL280 = df.BUI_COL280[country_code]
    BUI_COL56 = df.BUI_COL56[country_code]
    BUI_COL88 = df.BUI_COL88[country_code]
    BUI_COL5 = df.BUI_COL5[country_code]

    def GHG_wooda(nraXa, nraAa, nraBa, BUI_COL280, BUI_COL56, BUI_COL88, BUI_COL5):
        wood = (((nraXa * BUI_COL280) + (nraAa * BUI_COL56) + (nraBa * BUI_COL88)) * BUI_COL5) / 1_000_000
        return wood

    # Renewable

    BUI_COL281 = df.BUI_COL281[country_code]
    BUI_COL57 = df.BUI_COL57[country_code]
    BUI_COL89 = df.BUI_COL89[country_code]
    BUI_COL6 = df.BUI_COL6[country_code]

    def GHG_renewablea(nraXa, nraAa, nraBa, BUI_COL281, BUI_COL57, BUI_COL89, BUI_COL6):
        renewabe = (((nraXa * BUI_COL281) + (nraAa * BUI_COL57) + (nraBa * BUI_COL89)) * BUI_COL6) / 1_000_000
        return renewabe

    demolish_rate = df.BUI_COL8[country_code] / 100
    growth_rate_A = df.BUI_COL14[country_code] / 100
    growth_rate_B = df.BUI_COL17[country_code] / 100
    data = {}
    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']

    for i in range(start_year, 2051):
        if i == start_year:
            nraXa = unit_number
            nraAa = 0
            nraBa = 0
        else:
            if 2030 < i <= 2040:
                demolish_rate = df.BUI_COL9[country_code] / 100
                growth_rate_A = df.BUI_COL15[country_code] / 100
                growth_rate_B = df.BUI_COL18[country_code] / 100
            elif i > 2040:
                demolish_rate = df.BUI_COL10[country_code] / 100
                growth_rate_A = df.BUI_COL16[country_code] / 100
                growth_rate_B = df.BUI_COL19[country_code] / 100
            # nraXa = round(nraXa - demolish_rate * total)
            # nraAa = round(nraAa + growth_rate_A * total)
            # nraBa = round(nraBa + growth_rate_B * total)
        # total = nraXa + nraAa + nraBa

        if i < completed_from:
            nraAa = 0
        elif i == completed_from:
            nraAa = annual_increase
        elif completed_from < i <= completed_to:
            nraAa += annual_increase
        nraAa = round(nraAa + growth_rate_A * nraAa)
        nraBa = 0
        nraXa = 0

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
    apartment_emission = pd.DataFrame(data)
    apartment_emission.index = energy_carriers
    return apartment_emission
