import pandas as pd


# detach
def detach_emission_calculator(df, country_code, emission_factors_df, start_year, unit_number):
    BUI_COL299 = df.BUI_COL299[country_code]
    BUI_COL75 = df.BUI_COL75[country_code]
    BUI_COL107 = df.BUI_COL107[country_code]

    # Electricity
    def GHG_electricitya(nraXa, nraAa, nraBa, BUI_COL299, BUI_COL75, BUI_COL107, GRID_ELECTRICITY_emission_factora):
        electricity = (((nraXa * BUI_COL299) + (nraAa * BUI_COL75) + (
                nraBa * BUI_COL107)) * GRID_ELECTRICITY_emission_factora) / 1_000_000
        return electricity

    # Heat
    BUI_COL306 = df.BUI_COL306[country_code]
    BUI_COL82 = df.BUI_COL82[country_code]
    BUI_COL114 = df.BUI_COL114[country_code]

    def GHG_heata(nraXa, nraAa, nraBa, BUI_COL306, BUI_COL82, BUI_COL114, DISTRICT_HEATING_emission_factora=350):
        heat = (((nraXa * BUI_COL306) + (nraAa * BUI_COL82) + (
                nraBa * BUI_COL114)) * DISTRICT_HEATING_emission_factora) / 1_000_000
        return heat

    # Gas
    BUI_COL300 = df.BUI_COL300[country_code]
    BUI_COL76 = df.BUI_COL76[country_code]
    BUI_COL108 = df.BUI_COL108[country_code]
    BUI_COL1 = df.BUI_COL1[country_code]

    def GHG_gasa(nraXa, nraAa, nraBa, BUI_COL300, BUI_COL76, BUI_COL108, BUI_COL1):
        gas = (((nraXa * BUI_COL300) + (nraAa * BUI_COL76) + (nraBa * BUI_COL108)) * BUI_COL1) / 1_000_000
        return gas

    # Oil
    BUI_COL301 = df.BUI_COL301[country_code]
    BUI_COL77 = df.BUI_COL77[country_code]
    BUI_COL109 = df.BUI_COL109[country_code]
    BUI_COL2 = df.BUI_COL2[country_code]

    def GHG_oila(nraXa, nraAa, nraBa, BUI_COL301, BUI_COL77, BUI_COL109, BUI_COL2):
        oil = (((nraXa * BUI_COL301) + (nraAa * BUI_COL77) + (nraBa * BUI_COL109)) * BUI_COL2) / 1_000_000
        return oil

    # Coal
    BUI_COL302 = df.BUI_COL302[country_code]
    BUI_COL78 = df.BUI_COL78[country_code]
    BUI_COL110 = df.BUI_COL110[country_code]
    BUI_COL3 = df.BUI_COL3[country_code]

    def GHG_coala(nraXa, nraAa, nraBa, BUI_COL302, BUI_COL78, BUI_COL110, BUI_COL3):
        coal = (((nraXa * BUI_COL302) + (nraAa * BUI_COL78) + (nraBa * BUI_COL110)) * BUI_COL3) / 1_000_000
        return coal

    # Peat
    BUI_COL303 = df.BUI_COL303[country_code]
    BUI_COL79 = df.BUI_COL79[country_code]
    BUI_COL111 = df.BUI_COL111[country_code]
    BUI_COL4 = df.BUI_COL4[country_code]

    def GHG_peata(nraXa, nraAa, nraBa, BUI_COL303, BUI_COL79, BUI_COL111, BUI_COL4):
        peat = (((nraXa * BUI_COL303) + (nraAa * BUI_COL79) + (nraBa * BUI_COL111)) * BUI_COL4) / 1_000_000
        return peat

    # Wood
    BUI_COL304 = df.BUI_COL304[country_code]
    BUI_COL80 = df.BUI_COL80[country_code]
    BUI_COL112 = df.BUI_COL112[country_code]
    BUI_COL5 = df.BUI_COL5[country_code]

    def GHG_wooda(nraXa, nraAa, nraBa, BUI_COL304, BUI_COL80, BUI_COL112, BUI_COL5):
        wood = (((nraXa * BUI_COL304) + (nraAa * BUI_COL80) + (nraBa * BUI_COL112)) * BUI_COL5) / 1_000_000
        return wood

    # Renewable

    BUI_COL305 = df.BUI_COL305[country_code]
    BUI_COL81 = df.BUI_COL81[country_code]
    BUI_COL113 = df.BUI_COL113[country_code]
    BUI_COL6 = df.BUI_COL6[country_code]

    def GHG_renewablea(nraXa, nraAa, nraBa, BUI_COL305, BUI_COL81, BUI_COL113, BUI_COL6):
        renewabe = (((nraXa * BUI_COL305) + (nraAa * BUI_COL81) + (nraBa * BUI_COL113)) * BUI_COL6) / 1_000_000
        return renewabe

    demolish_rate = df.BUI_COL8[country_code] / 100
    growth_rate_A = df.BUI_COL32[country_code] / 100
    growth_rate_B = df.BUI_COL35[country_code] / 100
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
                growth_rate_A = df.BUI_COL33[country_code] / 100
                growth_rate_B = df.BUI_COL36[country_code] / 100
            elif i > 2040:
                demolish_rate = df.BUI_COL10[country_code] / 100
                growth_rate_A = df.BUI_COL34[country_code] / 100
                growth_rate_B = df.BUI_COL37[country_code] / 100
            nraXa = round(nraXa - demolish_rate * total)
            nraAa = round(nraAa + growth_rate_A * total)
            nraBa = round(nraBa + growth_rate_B * total)
        total = nraXa + nraAa + nraBa
        GRID_ELECTRICITY_emission_factora = emission_factors_df[i][0]
        Electricity = GHG_electricitya(nraXa, nraAa, nraBa, BUI_COL299, BUI_COL75, BUI_COL107,
                                       GRID_ELECTRICITY_emission_factora)
        Gas = GHG_gasa(nraXa, nraAa, nraBa, BUI_COL300, BUI_COL76, BUI_COL108, BUI_COL1)
        Oil = GHG_oila(nraXa, nraAa, nraBa, BUI_COL301, BUI_COL77, BUI_COL109, BUI_COL2)
        Coal = GHG_coala(nraXa, nraAa, nraBa, BUI_COL302, BUI_COL78, BUI_COL110, BUI_COL3)
        Peat = GHG_peata(nraXa, nraAa, nraBa, BUI_COL303, BUI_COL79, BUI_COL111, BUI_COL4)
        Wood = GHG_wooda(nraXa, nraAa, nraBa, BUI_COL304, BUI_COL80, BUI_COL112, BUI_COL5)
        Renewable = GHG_renewablea(nraXa, nraAa, nraBa, BUI_COL305, BUI_COL81, BUI_COL113, BUI_COL6)
        DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
        Heat = GHG_heata(nraXa, nraAa, nraBa, BUI_COL306, BUI_COL82, BUI_COL114, DISTRICT_HEATING_emission_factora)
        data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                   round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
    detach_emission = pd.DataFrame(data)
    detach_emission.index = energy_carriers
    return detach_emission