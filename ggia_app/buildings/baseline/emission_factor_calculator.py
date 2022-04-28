# making emission factors EFGEa and  EFDHa table

def emission_factor(df, country_code):
    GRID_ELECTRICITY_emission_factora_factor = df.ENE_COL2[country_code] / 100
    DISTRICT_HEATING_emission_factora_factor = df.ENE_COL6[country_code] / 100
    emission_factors = {}
    for i in range(2021, 2051):
        if i == 2021:
            GRID_ELECTRICITY_emission_factora = df.ENE_COL1[country_code]
            DISTRICT_HEATING_emission_factora = df.ENE_COL5[country_code]
        else:
            if 2030 < i <= 2040:
                GRID_ELECTRICITY_emission_factora_factor = df.ENE_COL3[country_code] / 100
                DISTRICT_HEATING_emission_factora_factor = df.ENE_COL7[country_code] / 100
            if i > 2040:
                GRID_ELECTRICITY_emission_factora_factor = df.ENE_COL4[country_code] / 100
                DISTRICT_HEATING_emission_factora_factor = df.ENE_COL8[country_code] / 100
            GRID_ELECTRICITY_emission_factora += GRID_ELECTRICITY_emission_factora * \
                                                 GRID_ELECTRICITY_emission_factora_factor
            DISTRICT_HEATING_emission_factora += DISTRICT_HEATING_emission_factora_factor * \
                                                 DISTRICT_HEATING_emission_factora
        emission_factors[i] = (round(GRID_ELECTRICITY_emission_factora, 1), round(DISTRICT_HEATING_emission_factora, 1))
    return emission_factors
