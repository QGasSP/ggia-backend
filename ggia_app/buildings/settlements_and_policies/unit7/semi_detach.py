import pandas as pd


# SEMI-DETACH
# Electricity
def semi_detach_emission(df, country_code, emission_factors_df, start_year, unit_number, completed_from, completed_to):
    annual_increase = round(unit_number / (completed_to - completed_from + 1))
    BUI_COL291 = df.BUI_COL291[country_code]
    BUI_COL67 = df.BUI_COL67[country_code]
    BUI_COL99 = df.BUI_COL99[country_code]

    def GHG_electricitya(nraXa, nraAa, nraBa, BUI_COL291, BUI_COL67, BUI_COL99, GRID_ELECTRICITY_emission_factora):
        electricity = (((nraXa * BUI_COL291) + (nraAa * BUI_COL67) + (
                nraBa * BUI_COL99)) * GRID_ELECTRICITY_emission_factora) / 1_000_000
        return electricity

    # Heat
    BUI_COL298 = df.BUI_COL298[country_code]
    BUI_COL74 = df.BUI_COL74[country_code]
    BUI_COL106 = df.BUI_COL106[country_code]

    def GHG_heata(nraXa, nraAa, nraBa, BUI_COL298, BUI_COL74, BUI_COL106, DISTRICT_HEATING_emission_factora=350):
        heat = (((nraXa * BUI_COL298) + (nraAa * BUI_COL74) + (
                nraBa * BUI_COL106)) * DISTRICT_HEATING_emission_factora) / 1_000_000
        return heat

    # Gas
    BUI_COL292 = df.BUI_COL292[country_code]
    BUI_COL68 = df.BUI_COL68[country_code]
    BUI_COL100 = df.BUI_COL100[country_code]
    BUI_COL1 = df.BUI_COL1[country_code]

    def GHG_gasa(nraXa, nraAa, nraBa, BUI_COL292, BUI_COL68, BUI_COL100, BUI_COL1):
        gas = (((nraXa * BUI_COL292) + (nraAa * BUI_COL68) + (nraBa * BUI_COL100)) * BUI_COL1) / 1_000_000
        return gas

    # Oil
    BUI_COL293 = df.BUI_COL293[country_code]
    BUI_COL69 = df.BUI_COL69[country_code]
    BUI_COL101 = df.BUI_COL101[country_code]
    BUI_COL2 = df.BUI_COL2[country_code]

    def GHG_oila(nraXa, nraAa, nraBa, BUI_COL293, BUI_COL69, BUI_COL101, BUI_COL2):
        oil = (((nraXa * BUI_COL293) + (nraAa * BUI_COL69) + (nraBa * BUI_COL101)) * BUI_COL2) / 1_000_000
        return oil

    # Coal
    BUI_COL294 = df.BUI_COL294[country_code]
    BUI_COL70 = df.BUI_COL70[country_code]
    BUI_COL102 = df.BUI_COL102[country_code]
    BUI_COL3 = df.BUI_COL3[country_code]

    def GHG_coala(nraXa, nraAa, nraBa, BUI_COL294, BUI_COL70, BUI_COL102, BUI_COL3):
        coal = (((nraXa * BUI_COL294) + (nraAa * BUI_COL70) + (nraBa * BUI_COL102)) * BUI_COL3) / 1_000_000
        return coal

    # Peat
    BUI_COL295 = df.BUI_COL295[country_code]
    BUI_COL71 = df.BUI_COL71[country_code]
    BUI_COL103 = df.BUI_COL103[country_code]
    BUI_COL4 = df.BUI_COL4[country_code]

    def GHG_peata(nraXa, nraAa, nraBa, BUI_COL295, BUI_COL71, BUI_COL103, BUI_COL4):
        peat = (((nraXa * BUI_COL295) + (nraAa * BUI_COL71) + (nraBa * BUI_COL103)) * BUI_COL4) / 1_000_000
        return peat

    # Wood
    BUI_COL296 = df.BUI_COL296[country_code]
    BUI_COL72 = df.BUI_COL72[country_code]
    BUI_COL104 = df.BUI_COL104[country_code]
    BUI_COL5 = df.BUI_COL5[country_code]

    def GHG_wooda(nraXa, nraAa, nraBa, BUI_COL296, BUI_COL72, BUI_COL104, BUI_COL5):
        wood = (((nraXa * BUI_COL296) + (nraAa * BUI_COL72) + (nraBa * BUI_COL104)) * BUI_COL5) / 1_000_000
        return wood

    # Renewable

    BUI_COL297 = df.BUI_COL297[country_code]
    BUI_COL73 = df.BUI_COL73[country_code]
    BUI_COL105 = df.BUI_COL105[country_code]
    BUI_COL6 = df.BUI_COL6[country_code]

    def GHG_renewablea(nraXa, nraAa, nraBa, BUI_COL297, BUI_COL73, BUI_COL105, BUI_COL6):
        renewabe = (((nraXa * BUI_COL297) + (nraAa * BUI_COL73) + (nraBa * BUI_COL105)) * BUI_COL6) / 1_000_000
        return renewabe

    demolish_rate = df.BUI_COL8[country_code] / 100
    growth_rate_A = df.BUI_COL26[country_code] / 100
    growth_rate_B = df.BUI_COL29[country_code] / 100
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
                growth_rate_A = df.BUI_COL27[country_code] / 100
                growth_rate_B = df.BUI_COL30[country_code] / 100
            elif i > 2040:
                demolish_rate = df.BUI_COL10[country_code] / 100
                growth_rate_A = df.BUI_COL28[country_code] / 100
                growth_rate_B = df.BUI_COL31[country_code] / 100
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
        Electricity = GHG_electricitya(nraXa, nraAa, nraBa, BUI_COL291, BUI_COL67, BUI_COL99,
                                       GRID_ELECTRICITY_emission_factora)
        Gas = GHG_gasa(nraXa, nraAa, nraBa, BUI_COL292, BUI_COL68, BUI_COL100, BUI_COL1)
        Oil = GHG_oila(nraXa, nraAa, nraBa, BUI_COL293, BUI_COL69, BUI_COL101, BUI_COL2)
        Coal = GHG_coala(nraXa, nraAa, nraBa, BUI_COL294, BUI_COL70, BUI_COL102, BUI_COL3)
        Peat = GHG_peata(nraXa, nraAa, nraBa, BUI_COL295, BUI_COL71, BUI_COL103, BUI_COL4)
        Wood = GHG_wooda(nraXa, nraAa, nraBa, BUI_COL296, BUI_COL72, BUI_COL104, BUI_COL5)
        Renewable = GHG_renewablea(nraXa, nraAa, nraBa, BUI_COL297, BUI_COL73, BUI_COL105, BUI_COL6)
        DISTRICT_HEATING_emission_factora = emission_factors_df[i][1]
        Heat = GHG_heata(nraXa, nraAa, nraBa, BUI_COL298, BUI_COL74, BUI_COL106, DISTRICT_HEATING_emission_factora)
        data[i] = [round(Electricity, 1), round(Gas, 1), round(Oil, 1), round(Coal, 1),
                   round(Peat, 1), round(Wood, 1), round(Renewable, 1), round(Heat, 1)]
    semiDetach_emission = pd.DataFrame(data)
    semiDetach_emission.index = energy_carriers
    return semiDetach_emission

