
import pandas as pd


# TTERRACED UNITS
# Electricity
def terraced_emission(df, country_code, emission_factors_df, start_year, unit_number, completed_from, completed_to):
    annual_increase = round(unit_number / (completed_to - completed_from + 1))
    BUI_COL283 = df.BUI_COL283[country_code]
    BUI_COL59 = df.BUI_COL59[country_code]
    BUI_COL91 = df.BUI_COL91[country_code]

    def GHG_electricitya(nraXa, nraAa, nraBa, BUI_COL283, BUI_COL59, BUI_COL91, GRID_ELECTRICITY_emission_factora):
        electricity = (((nraXa * BUI_COL283) + (nraAa * BUI_COL59) + (
                nraBa * BUI_COL91)) * GRID_ELECTRICITY_emission_factora) / 1_000_000
        return electricity

    # Heat
    BUI_COL290 = df.BUI_COL290[country_code]
    BUI_COL66 = df.BUI_COL66[country_code]
    BUI_COL98 = df.BUI_COL98[country_code]

    def GHG_heata(nraXa, nraAa, nraBa, BUI_COL290, BUI_COL66, BUI_COL98, DISTRICT_HEATING_emission_factora=350):
        heat = (((nraXa * BUI_COL290) + (nraAa * BUI_COL66) + (
                nraBa * BUI_COL98)) * DISTRICT_HEATING_emission_factora) / 1_000_000
        return heat

    # Gas
    BUI_COL284 = df.BUI_COL284[country_code]
    BUI_COL60 = df.BUI_COL60[country_code]
    BUI_COL92 = df.BUI_COL92[country_code]
    BUI_COL1 = df.BUI_COL1[country_code]

    def GHG_gasa(nraXa, nraAa, nraBa, BUI_COL284, BUI_COL60, BUI_COL92, BUI_COL1):
        gas = (((nraXa * BUI_COL284) + (nraAa * BUI_COL60) + (nraBa * BUI_COL92)) * BUI_COL1) / 1_000_000
        return gas

    # Oil
    BUI_COL285 = df.BUI_COL285[country_code]
    BUI_COL61 = df.BUI_COL61[country_code]
    BUI_COL93 = df.BUI_COL93[country_code]
    BUI_COL2 = df.BUI_COL2[country_code]

    def GHG_oila(nraXa, nraAa, nraBa, BUI_COL285, BUI_COL61, BUI_COL93, BUI_COL2):
        oil = (((nraXa * BUI_COL285) + (nraAa * BUI_COL61) + (nraBa * BUI_COL93)) * BUI_COL2) / 1_000_000
        return oil

    # Coal
    BUI_COL286 = df.BUI_COL286[country_code]
    BUI_COL62 = df.BUI_COL62[country_code]
    BUI_COL94 = df.BUI_COL94[country_code]
    BUI_COL3 = df.BUI_COL3[country_code]

    def GHG_coala(nraXa, nraAa, nraBa, BUI_COL286, BUI_COL62, BUI_COL94, BUI_COL3):
        coal = (((nraXa * BUI_COL286) + (nraAa * BUI_COL62) + (nraBa * BUI_COL94)) * BUI_COL3) / 1_000_000
        return coal

    # Peat
    BUI_COL287 = df.BUI_COL287[country_code]
    BUI_COL63 = df.BUI_COL63[country_code]
    BUI_COL95 = df.BUI_COL95[country_code]
    BUI_COL4 = df.BUI_COL4[country_code]

    def GHG_peata(nraXa, nraAa, nraBa, BUI_COL287, BUI_COL63, BUI_COL95, BUI_COL4):
        peat = (((nraXa * BUI_COL287) + (nraAa * BUI_COL63) + (nraBa * BUI_COL95)) * BUI_COL4) / 1_000_000
        return peat

    # Wood
    BUI_COL288 = df.BUI_COL288[country_code]
    BUI_COL64 = df.BUI_COL64[country_code]
    BUI_COL96 = df.BUI_COL96[country_code]
    BUI_COL5 = df.BUI_COL5[country_code]

    def GHG_wooda(nraXa, nraAa, nraBa, BUI_COL288, BUI_COL64, BUI_COL96, BUI_COL5):
        wood = (((nraXa * BUI_COL288) + (nraAa * BUI_COL64) + (nraBa * BUI_COL96)) * BUI_COL5) / 1_000_000
        return wood

    # Renewable

    BUI_COL289 = df.BUI_COL289[country_code]
    BUI_COL65 = df.BUI_COL65[country_code]
    BUI_COL97 = df.BUI_COL97[country_code]
    BUI_COL6 = df.BUI_COL6[country_code]

    def GHG_renewablea(nraXa, nraAa, nraBa, BUI_COL289, BUI_COL65, BUI_COL97, BUI_COL6):
        renewabe = (((nraXa * BUI_COL289) + (nraAa * BUI_COL65) + (nraBa * BUI_COL97)) * BUI_COL6) / 1_000_000
        return renewabe

    demolish_rate = df.BUI_COL8[country_code] / 100
    growth_rate_A = df.BUI_COL20[country_code] / 100
    growth_rate_B = df.BUI_COL23[country_code] / 100
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
                growth_rate_A = df.BUI_COL21[country_code] / 100
                growth_rate_B = df.BUI_COL24[country_code] / 100
            elif i > 2040:
                demolish_rate = df.BUI_COL10[country_code] / 100
                growth_rate_A = df.BUI_COL22[country_code] / 100
                growth_rate_B = df.BUI_COL25[country_code] / 100
        #     nraXa = round(nraXa - demolish_rate * total)
        #     nraAa = round(nraAa + growth_rate_A * total)
        #     nraBa = round(nraBa + growth_rate_B * total)
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
        Electricity = GHG_electricitya(nraXa, nraAa, nraBa, BUI_COL283, BUI_COL59, BUI_COL91,
                                       GRID_ELECTRICITY_emission_factora)
        Gas = GHG_gasa(nraXa, nraAa, nraBa, BUI_COL284, BUI_COL60, BUI_COL92, BUI_COL1)
        Oil = GHG_oila(nraXa, nraAa, nraBa, BUI_COL285, BUI_COL61, BUI_COL93, BUI_COL2)
        Coal = GHG_coala(nraXa, nraAa, nraBa, BUI_COL286, BUI_COL62, BUI_COL94, BUI_COL3)
        Peat = GHG_peata(nraXa, nraAa, nraBa, BUI_COL287, BUI_COL63, BUI_COL95, BUI_COL4)
        Wood = GHG_wooda(nraXa, nraAa, nraBa, BUI_COL288, BUI_COL64, BUI_COL96, BUI_COL5)
        Renewable = GHG_renewablea(nraXa, nraAa, nraBa, BUI_COL289, BUI_COL65, BUI_COL97, BUI_COL6)
        DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
        Heat = GHG_heata(nraXa, nraAa, nraBa, BUI_COL290, BUI_COL66, BUI_COL98, DISTRICT_HEATING_emission_factora)
        data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                   round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
    terraced_units_emission = pd.DataFrame(data)
    terraced_units_emission.index = energy_carriers
    return terraced_units_emission

