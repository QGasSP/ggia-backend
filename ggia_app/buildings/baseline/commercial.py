from random import randint


def calculate_baseline_commercial_emission(
        start_year, country, retail_number, health_number, hospitality_number, offices_number,
        industrial_number, warehouses_number
):
    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']

    parameters = ['Apartment', 'Terraced', 'Semi-detached', 'Detached', 'Retail', 'Health',
                  'Hospitality', 'Offices', 'Industrial', 'Warehouses']

    mockr_table = {parameter: {carrier: randint(0, 1000) for carrier in energy_carriers}
                   for parameter in parameters}

    mockr_result = {year: {parameter: randint(0, 1000) for parameter in parameters} for year in
                    range(2023, 2051)}
    return mockr_table, mockr_result
