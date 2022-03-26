#!/usr/bin/env python
# coding: utf-8

# GGIA Consumption Module
# authors: Peter Robert Walke (original Jupyter notebook)
#          Ulrich Norbisrath (ulno)

# Variable naming convention:
# Constants, strings, and static tables are spelled all capital letters
#
# Variable endings:
# - _T or _t: table
# - _KV or _kv: key-value
# - _loc: Local representation of a former global variable


# Loading Python Libraries
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt


## constants (mainly strings and labels) and csv tables
# they are easy to spot due to capital spelling

## CSV imports
CSV_PATH = os.path.join("CSVfiles", "consumption", "")

# Load the projections for income and house size
HOUSE_SIZE_PROJ_T = pd.read_csv(CSV_PATH + "House_proj_exio.csv", index_col=0)
INCOME_PROJ_T = pd.read_csv(CSV_PATH + "Income_proj_exio.csv", index_col=0)

# Load the different Y vectors.
# The user selects which one
# to use based on the urban density of the region (or the
# average one for mixed regions or if they are unsure)
Y_VECTORS = {
    'average': pd.read_csv(CSV_PATH + "Average_2020_Exio_elec_trans_en_Euro.csv", index_col=0),
    'city': pd.read_csv(CSV_PATH + "City_2020_Exio_elec_trans_en_Euro.csv", index_col=0),
    'rural': pd.read_csv(CSV_PATH + "Rural_2020_Exio_elec_trans_en_Euro.csv", index_col=0),
    'town': pd.read_csv(CSV_PATH + "Town_2020_Exio_elec_trans_en_Euro.csv", index_col=0) }

# Load the Use phase and tail pipe emissions.
USE_PHASE_T = pd.read_csv(CSV_PATH + "Energy_use_phase_Euro.csv", index_col=0)
TAIL_PIPE_T = pd.read_csv(CSV_PATH + "Tailpipe_emissions_bp.csv", index_col=0)

# Load default house sizes
HOUSE_SIZE_T = pd.read_csv(CSV_PATH + "Household_characteristics_2015.csv", index_col=0)

# Load the Emission intensities
# EMISSION_COUNTRIES_T is the standard Emissions factors
EMISSION_COUNTRIES_T = pd.read_csv(CSV_PATH + "Country_Emissions_intensities.csv", index_col=0)

# M_countries_LCA is the same as M_countries, but with the electricity sector replaced with
# individual LCA values
# This is useful if there is local electricity production. The user can replace certain values
# with these values if needed
EMISSION_COUNTRIES_LCA_T = pd.read_csv(
    CSV_PATH + "Country_Emissions_intensities_LCA.csv", index_col=0)
PRODUCT_COUNT = EMISSION_COUNTRIES_T.columns
EXIO_PRODUCTS_T = pd.read_csv(CSV_PATH + "Exio_products.csv")

# Load the IW sectors
# This is needed to put the emissions into different 'sectors', such as transport,
# food, building energy use, etc
IW_SECTORS_T = pd.read_csv(CSV_PATH + "IW_sectors_reduced.csv", index_col=0)
IW_SECTORS_NP_T = IW_SECTORS_T.to_numpy()
IW_SECTORS_NP_TR_T = np.transpose(IW_SECTORS_NP_T)

# Load the adjustable amounts.
# This says how much electricity is spent on heating. There are some other things here but
# decided not to include.
ADJUSTABLE_AMOUNTS_T = pd.read_csv(CSV_PATH + "Adjustable_energy_amounts.csv", index_col=0)

# Electricity prices database might need updating still - TODO: we could think about that later
# Load the electricity prices. This is so we know in monetary terms how much is being spent on
# electricity. The tool
# at the moment has the electricity used by households in kWh. However, maybe this should now be
# changed?
ELECTRICITY_PRICES_T = pd.read_csv(CSV_PATH + "electricity_prices_2019.csv", index_col=0)

# Load the fuel prices at basic price
# We need this because of electric vehicles. The electricity and fuels need to be in the same units.
FUEL_PRICES_T = pd.read_csv(CSV_PATH + "Fuel_prices_BP_attempt.csv", index_col=0)

# Load the Income scaler. This describes how much each household spends depending on their income.
INCOME_SCALING_T = pd.read_csv(CSV_PATH + "mean_expenditure_by_quint.csv", index_col=0)

# Types of electricity
# No electricity goes in ELECTRICITY_NEC. This is used for local electricity production
ELECTRICITY_NEC = 'Electricity nec'
ELECTRICITY_TYPES = [
    'Electricity by coal',
    'Electricity by gas',
    'Electricity by nuclear',
    'Electricity by hydro',
    'Electricity by wind',
    'Electricity by petroleum and other oil derivatives',
    'Electricity by biomass and waste',
    'Electricity by solar photovoltaic',
    'Electricity by solar thermal',
    'Electricity by tide, wave, ocean',
    'Electricity by Geothermal',
    ELECTRICITY_NEC]


# Supply of household heating
LIQUID_TYPES = [
    'Natural Gas Liquids',
    'Kerosene',
    'Heavy Fuel Oil',
    'Other Liquid Biofuels']
SOLID_TYPES = [
    ('Wood and products of wood and cork (except furniture); '
        'articles of straw and plaiting materials (20)'),
    'Coke Oven Coke']
DISTRIBUTION_GAS='Distribution services of gaseous fuels through mains'
GAS_TYPES = [
    DISTRIBUTION_GAS,
    'Biogas']
DISTRICT_SERVICE_LABEL = 'Steam and hot water supply services'

BIOGASOLINE = 'Biogasoline'
BIODIESEL = 'Biodiesels'
MOTORGASOLINE = 'Motor Gasoline'
GAS_DIESEL_OIL = 'Gas/Diesel Oil'
FUELS = [BIODIESEL, GAS_DIESEL_OIL, MOTORGASOLINE, BIOGASOLINE]

MOTOR_VEHICLES = 'Motor vehicles, trailers and semi-trailers (34)'
# the spelling mistake in accessories in the following LABEL is intended as that's how it is
# in the csv tables
SALE_REPAIR_VEHICLES = ('Sale, maintenance, repair of motor vehicles, motor vehicles parts, '
    'motorcycles, motor cycles parts and accessoiries')

PUBLIC_TRANSPORT = [
    'Railway transportation services',
    'Other land transportation services',
    'Sea and coastal water transportation services',
    'Inland water transportation services']

WOOD_PRODUCTS=('Wood and products of wood and cork (except furniture); '
    'articles of straw and plaiting materials (20)')

NORTH = ['Denmark', 'Finland', 'Sweden', 'Norway', 'Iceland']

WEST = ['Austria', 'Belgium', 'Germany', 'Spain', 'France', 'Ireland',
        'Italy', 'Luxembourg', 'Malta', 'Netherlands',
        'Portugal', 'United Kingdom', 'Switzerland', 'Liechtenstein']

EAST = ['Bulgaria', 'Cyprus', 'Czechia', 'Estonia', 'Greece',
        'Hungary', 'Croatia', 'Lithuania', 'Latvia', 'Poland',
        'Romania', 'Slovenia', 'Slovakia', ]

COUNTRY_ABBREVIATIONS = {
    'Austria': 'AT',
    'Belgium': 'BE',
    'Bulgaria': 'BG',
    'Cyprus': 'CR',
    'Croatia': 'HR',
    'Czechia': 'CZ',
    'Denmark': 'DK',
    'Estonia': 'EE',
    'France': 'FR',
    'Finland': 'FE',
    'Germany': 'DE',
    'Greece': 'GR',
    'Hungary': 'HU',
    'Iceland': 'IS',
    'Ireland': 'IE',
    'Italy': 'IT',
    'Latvia': 'LV',
    'Liechtenstein': 'LI',
    'Lithuania': 'LT',
    'Luxembourg': 'LU',
    'Malta': 'MT',
    'Netherlands': 'NL',
    'Norway': 'NO',
    'Portugal': 'PT',
    'Poland': 'PL',
    'Romania': 'RO',
    'Slovakia': 'SK',
    'Slovenia': 'SI',
    'Spain': 'ES',
    'Sweden': 'SE',
    'Switzerland': 'CH',
    'United Kingdom': 'GB',
}

class Consumption:
    """
    LIST of originally adjustable variables

    All values have defaults apart from the ones with
    required. So the minimum data required by the user for the
    baseline is filling in the required data.

    I don't know how to make it so that the default variables are loaded and can then be changed
    by the user.
    I think it would be necessary to recall the data from the server after the first consumption
    calculations screen.
    """

    ## Baseline variables ##

    year = int(2022)   # required
    region = str()   # required - Equivalent to "name the project"
    # I ask this to differentiate between policies, but maybe the tool has another way.
    policy_label = str()
    country = str()   # Required
    abbrev = str()      # This can be combined with the one above

    target_area = str()  # Required #3 options in dropdown menu
    area_type = str()   # Required #4_options in drop down menu
                        # - average, rural, city, town (former U_type)
    pop_size = int()  # Required - completely open


    house_size = float()  # completely open, but with a default value.
    income_level = str()  # There are 5 options in a drop down menu

    eff_scaling = float()  # default value should be 0.97 (equivalent to 3 %)

    # the following baseline variables are now set to defaults, but are still here for completion
    river_prop = float()
    ferry_prop = float()
    rail_prop = float()
    # These values should sum to 1 (or 100 %) They all have a default value
    bus_prop = float()

    ## end of baseline variables ##

    # For the policies, the following additional questions are required (as well as those above)
    ## policy variables ##
    policy_year = int()   # required - This question has been missed in the UI


    eff_gain = str()     # required
    eff_scaler = float()

    local_electricity = str()
    el_type = str()  # 3 options from drop_down menu
    el_scaler = float()

    s_heating = str()  # required

    biofuel_takeup = str()  # required
    bio_scaler = float()

    ev_takeup = str()  # required
    ev_scaler = float()

    modal_shift = str()  # required
    ms_fuel_scaler = float()
    ms_pt_scaler = float()
    ms_veh_scaler = float()

    new_floor_area = float()  # default is zero

    # These are all to do with electricity mix 99% of time should use default values
    hydro_prop = float()
    solar_pvc_prop = float()
    coal_prop = float()
    gas_prop = float()
    nuclear_prop = float()
    wind_prop = float()
    petrol_prop = float()
    solar_thermal_prop = float()
    tide_prop = float()
    geo_prop = float()
    # Last electricity mix  #These values should sum to 1 (or 100 %)
    nec_prop = float()

    district_prop = float()
    electricity_heat_prop = float()
    combustable_fuels_prop = float()    # These 3 values should sum to 1 (or 100 %)

    liquids_prop = float()
    solids_prop = float()
    gases_prop = float()                # These 3 values should sum to 1 (or 100 %)

    direct_district_emissions = float()  # A default value os given.

    ## end of policy variables ##

    def __init__(self, year, country, pop_size,
            region=None, # region is just a name for working on a specific subset of a country
            area_type="average",
            income_choice = "3rd_household",
            eff_scaler="normal"
            ):

        self.year = year
        self.country = country
        self.abbrev = COUNTRY_ABBREVIATIONS[country]
        self.pop_size = pop_size
        self.region = region
        self.area_type = area_type

        # initial demand vector
        self.demand_kv = Y_VECTORS[area_type][country].copy()

        # U9.3: House_size - also extracted
        # This is the default
        self.house_size_ab = HOUSE_SIZE_T.loc['Average_size_' + area_type, country]
        # self.house_size_ab = 2.14 #xx###USER_INPUT would look like this here

        # Otherwise,  the user selects the income level of the household (they choose by quintiles)
        self.income_choice = income_choice
        income_scaler = INCOME_SCALING_T.loc[income_choice, country] / \
            INCOME_SCALING_T.loc['Total_household', country]  # USER_INPUT
        elasticity = 1  # Random number for now. It should be specific to country and product

        # U9.4:Income_scaler
        # options are:
        # "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
        # 1st household is the richest.
        # if self.income_choice == "3rd_household":
        #    income_scaler = 1
        self.demand_kv *= income_scaler * elasticity

        # U9.5: This is the expected global reduction in product emissions
        # Suggestion - Just give the user one of three options, with the default being normal
        self.eff_scaling = 1 - {"fast": 0.07, "normal": 0.03, "slow": 0.01}[eff_scaler]

        ##############################################################
        # Forming data for the calculations

        self.direct_ab = "direct_"+self.abbrev
        self.indirect_ab = "indirect_"+self.abbrev

        # Here the emission intensities are selected
        self.emission_intensities = \
            EMISSION_COUNTRIES_T.loc[self.direct_ab:self.indirect_ab, :].copy()

        # These are needed for the use phase emissions
        self.tail_pipe_ab = TAIL_PIPE_T[country].copy()
        self.use_phase_ab = USE_PHASE_T[country].copy()

        # This is needed for calculating the amount of electricity coming from heating
        self.adjustable_amounts = ADJUSTABLE_AMOUNTS_T[country].copy()
        self.elec_price = ELECTRICITY_PRICES_T[country]["BP_2019_S2_Euro"]

        # Baseline Modifications go here  ##Possibly not included in this version of the tool
        ################ end of the mandatory questions #######################

        self.elec_total = self.demand_kv[ELECTRICITY_TYPES].sum()

        self.electricity_heat = (self.adjustable_amounts["elec_water"] \
            + self.adjustable_amounts["elec_heat"] \
            + self.adjustable_amounts["elec_cool"]) * self.elec_total * self.elec_price

        self.total_fuel = self.demand_kv[SOLID_TYPES].sum() \
            + self.demand_kv[LIQUID_TYPES].sum() \
            + self.demand_kv[GAS_TYPES].sum() \
            + self.demand_kv[DISTRICT_SERVICE_LABEL].sum() \
            + self.electricity_heat
        
        # TODO: look at this later -> we assume all 'fuels' are 
        # the same efficiency (obviously wrong, but no time to fix)



    # Policy "functions"
    # The different Policies are written as functions to reduce the length of the calculation code

    def biofuels(self, scaler):
        """
        This is a policy.

        *Explanation*

        This sort of policy acts only on the Expenditure (Intensities don't change)
        Similar polices could exist for housing fuel types, ...
        Similar adjustments to this could also be needed to correct the baselines if
        the user knows the results to be different

        Local Inputs:
        - demand_kv[BIOGASOLINE]
        - demand_kv[BIODIESEL]
        - demand_kv[MOTORGASOLINE]
        - demand_kv[GAS_DIESEL_OIL]

        Outputs:
        - demand_kv[BIOGASOLINE] - careful, this means this field is permanently changed after call
        - demand_kv[BIODIESEL] - careful, this means this field is permanently changed after a call
        - demand_kv[MOTORGASOLINE] - careful, this means this field is permanently changed after
                                        a call
        - demand_kv[GAS_DIESEL_OIL] - careful, this means this field is permanently changed after
                                        a call
        """
        demand_kv = self.demand_kv  # shortcut to work on this field

        #
        # current_biofuels = demand_loc_KV['Biogasaline'] + demand_loc_KV['biodiesel'] /

        # Step 1. Determine current expenditure on fuels and the proportions of each type
        total_fuel = demand_kv[BIOGASOLINE] + demand_kv[BIODIESEL] + \
            demand_kv[MOTORGASOLINE] + demand_kv[GAS_DIESEL_OIL]
        diesel = (demand_kv[BIODIESEL] + demand_kv[GAS_DIESEL_OIL])
        petrol = (demand_kv[MOTORGASOLINE] + demand_kv[BIOGASOLINE])

        # Step 1.1 current_biofuels = (demand_kv[BIOGASOLINE] + demand_kv[BIODIESEL]) / total_fuel

        # Step 2. Increase the biofuel to the designated amount
        demand_kv[BIOGASOLINE] = scaler * total_fuel * (petrol / (diesel + petrol))
        demand_kv[BIODIESEL] = scaler * total_fuel * (diesel / (diesel + petrol))

        # Step 3. Decrease the others by the correct amount,
        # taking into account their initial values
        # The formula to do this is :
        # New Value = Remaining_expenditure * Old_proportion
        # (once the previous categories are removed)
        # This can't be more than the total! - TODO: assert?
        sum_changed = demand_kv[BIOGASOLINE] + demand_kv[BIODIESEL]

        if sum_changed > total_fuel:
            # TODO: exception
            pass

        demand_kv[MOTORGASOLINE] = (
            total_fuel - sum_changed) * (petrol / (diesel + petrol))
        demand_kv[GAS_DIESEL_OIL] = (
            total_fuel - sum_changed) * (diesel / (diesel + petrol))


    def electric_vehicles(self, scaler):
        """
        This is a policy.

        *Explanation*

        xx% of vehicles are ev
        First we reduce the expenditure on all forms of transport fuels by xx%
        Then, we need to add something onto the electricity

        For this we need to: calculate how much fuel is saved and convert it back into liters
        (and then kWh)
        Take into account the difference in efficiency between the two types
        Add the kWh evenly onto the electricity sectors

        Explanation/Description
        This sort of policy acts only on the Expenditure

        Local Inputs:
        - demand_kv[BIODIESEL]
        - demand_kv[GAS_DIESEL_OIL]
        - demand_kv[MOTORGASOLINE]
        - demand_kv[BIOGASOLINE]
        - demand_kv[ELECTRICITY_TYPES]

        Global Inputs:
        - country - string of a country name
        - FUEL_PRICES_T.loc['Diesel_2020', country]
        - FUEL_PRICES_T.loc['petrol_2020', country]
        - ELECTRICITY_TYPES

        Outputs:
        - demand_kv[electricity] - careful, this means this (these) field is
                                    permanently changed after a call to this method
        """
        demand_kv = self.demand_kv  # shortcut to work on this field

        # Step 1 Assign a proportion of the fuels to be converted and
        # reduce the fuels by the correct amount

        diesel = (demand_kv[BIODIESEL] + demand_kv[GAS_DIESEL_OIL])*scaler
        petrol = (demand_kv[MOTORGASOLINE] + demand_kv[BIOGASOLINE])*scaler

        for fuel in FUELS:
            demand_kv[fuel] = demand_kv[fuel]*(1-scaler)

        # Step 2 Turn the amount missing into kWh
        diesel /= FUEL_PRICES_T.loc['Diesel_2020', self.country]
        petrol /= FUEL_PRICES_T.loc['petrol_2020', self.country]

        diesel *= 38.6*0.278   # liters, then kWh
        petrol *= 34.2*0.278   # liters, then kWh

        # Step 3. #Divide that amount by 4.54 (to account foe the efficiency gains)
        diesel /= 4.54         # Efficiency saving
        petrol /= 4.54         # Efficiency saving

        # Step 4. Assign this to increased electricity demand
        elec_vehicles = diesel + petrol
        elec_total = demand_kv[ELECTRICITY_TYPES].sum()
        elec_scaler = (elec_vehicles + elec_total) / elec_total

        demand_kv[ELECTRICITY_TYPES] *= elec_scaler


    def eff_improvements(self, scaler):
        """
        This is a policy.

        *Explanation*

        Retrofitting reduces energy expenditure on heating by xx %

        This sort of policy acts only on the Expenditure (intensities don't change)
        Take the expenditure on household fuels and reduce it by a scale factor defined by the user

        Global Inputs:
        - district - label
        - liquids
        - solids
        - gases
        - electricity - set of labels/strings marking electricity entries in demand_kv
        - ad["elec_water"]
        - ad["elec_heat"]
        - ad["elec_cool"]

        Local Inputs:
        - demand_kv <- all liquids, solids, and gases, electricity entries
        - demand_kv[GAS_DIESEL_OIL]
        - demand_kv[MOTORGASOLINE]
        - demand_kv[BIOGASOLINE]
        - demand_kv[electricity] - seems this time to be a list of values (as later sum used)

        Outputs:
        - demand_kv[district] - not sure if this is a side effect or not

        """

        demand_kv = self.demand_kv  # shortcut to work on this field

        # Step 1. This can be done as a single stage.
        # Just reduce the parts that can be reduced by the amount in the scaler

        for liquid in LIQUID_TYPES:
            demand_kv[liquid] = (demand_kv[liquid] * (1 - scaler))

        for solid in SOLID_TYPES:
            demand_kv[solid] = (demand_kv[solid] * (1 - scaler))

        for gas in GAS_TYPES:
            demand_kv[gas] = (demand_kv[gas] * (1 - scaler))

        for elec in ELECTRICITY_TYPES:
            elec_hold = demand_kv[elec] * (1 - (self.adjustable_amounts["elec_water"]
                + self.adjustable_amounts["elec_heat"]
                + self.adjustable_amounts["elec_cool"]))  # Parts not related to heating/cooling etc
            demand_kv[elec] = (demand_kv[elec] * (self.adjustable_amounts["elec_water"]
                + self.adjustable_amounts["elec_heat"]
                + self.adjustable_amounts["elec_cool"]) * (1 - scaler))
            demand_kv[elec] += elec_hold

        demand_kv[DISTRICT_SERVICE_LABEL] *= 1 - scaler


    def transport_modal_shift(self, scaler, scaler_2, scaler_3):
        """
        This is a policy.

        *Explanation*

        Modal share - decrease in private transport and increase in public transport

        This sort of policy acts only on the Expenditure (Intensities don't change)
        The expenditure on private transport is reduced by a certain amount
        (1 part for fuels and 1 for vehicles)

        The public transport is also increased by a different amount.
        This is to account for the effects of active travel

        Global Inputs:
        - PUBLIC_TRANSPORT

        Local Inputs:
        - demand_kv[GAS_DIESEL_OIL]
        - demand_kv[MOTORGASOLINE]
        - demand_kv[BIOGASOLINE]
        - demand_kv[electricity] - seems to be a list of values (as later sum used)
        - demand_kv[MOTOR_VEHICLES]
        - demand_kv[SALE_REPAIR_VEHICLES]
        - demand_kv <- for all public_transports

        Outputs:
        - demand_kv[MOTOR_VEHICLES] - careful, this means this field
          is permanently changed after a call to this method
        - demand_kv[SALE_REPAIR_VEHICLES] - - careful, this means this field is
          permanently changed after a call to this method
        - demand_kv <- for all public_transports - careful, this means this field is
          permanently changed after a call to this method
        """
        demand_kv = self.demand_kv  # shortcut to work on this field

        for fuel in FUELS:
            demand_kv[fuel] *= (1-scaler)
            # In this case, we also assume that there is a reduction on the amount spent on vehicles
            # Change in modal shift takes vehicles off the road?

        for vehicle in [MOTOR_VEHICLES, SALE_REPAIR_VEHICLES]:
            demand_kv[vehicle] *= (1-scaler_3)

        for transport in PUBLIC_TRANSPORT:  # Public transport was defined above
            demand_kv[transport] *= (1+scaler_2)


    def local_generation(self, ab_m, scaler, elec_type):
        """
        This is a policy.

        *Explanation*

        Local electricity is produced by (usually) rooftop solar and it is utilized only
        in that area

        Reduce current electricity by xx %
        Introduce a new electricity emission intensity (based on PV in the LCA emission intensities)
        that accounts for the missing xx %

        Global Inputs:
        - direct_ab
        - indirect_ab
        - electricity: here it's used a field of labels again

        Local Inputs:
        - demand_kv[ELECTRICITY_NEC]
        - M_countries_LCA.loc[direct_ab:indirect_ab,type_electricity]


        Outputs:
        - ab_M.loc[direct_ab:indirect_ab,ELECTRICITY_NEC]
        - demand_kv[ELECTRICITY_NEC] - careful, this means this field is permanently
                                        changed after a call to this method
        """
        demand_kv = self.demand_kv  # shortcut to work on this field

        elec_total = demand_kv[ELECTRICITY_TYPES].sum()

        for elec in ELECTRICITY_TYPES:
            demand_kv[elec] = (demand_kv[elec] * (1 - scaler))

        # Assign the remaining amount to the spare category (electricity nec)
        demand_kv[ELECTRICITY_NEC] = elec_total * scaler

        # Set the emission intensity of this based on LCA values
        ab_m.loc[self.direct_ab:self.indirect_ab, ELECTRICITY_NEC] = \
            EMISSION_COUNTRIES_LCA_T.loc[self.direct_ab:self.indirect_ab, elec_type]


    def local_heating(self, ab_m, district_prop, elec_heat_prop,
                    combustable_fuels_prop, liquids_prop,
                    gas_prop, solids_prop, district_val):
        """
        Is this a policy? It has a lot of nice input values.

        THIS JUST REPEATS BASELINE QUESTIONS 9 - 10.
        ALLOWING THE USER TO CHANGE THE VALUES

        Global Inputs:
        - district
        - direct_ab
        - total_fuel
        - electricity: here it's used a field of labels again
        - ad["elec_water"]
        - ad["elec_heat"]
        - ad["elec_cool"]
        - elec_total
        - liquids
        - solids

        Local Inputs:
        - demand_kv[elec] for all labels in electricity
        - demand_kv[liquid] for all labels in liquids

        Outputs:
        - demand_kv[elec] for all labels in electricity.
          Careful, this means these fields are permanently changed after a call to this method
        - demand_kv[liquid] for all labels in liquids.
          Careful, this means these fields are permanently changed after a call to this method
        - demand_kv[WOOD_PRODUCTS]
        - demand_kv[DISTRIBUTION_GAS]
        - ab_M.loc[direct_ab,district]
          Careful, this means this field is permanently changed after a call to this method
        """

        demand_kv = self.demand_kv  # shortcut to work on this field

        # DISTRICT HEATING
        demand_kv[DISTRICT_SERVICE_LABEL] = self.total_fuel * district_prop

        # ELECTRICITY
        for elec in ELECTRICITY_TYPES:
            # determine amount of each electricity source in total electricity mix.
            prop = demand_kv[elec] / self.elec_total
            elec_hold = (1 - (self.adjustable_amounts["elec_water"]
                            + self.adjustable_amounts["elec_heat"]
                            + self.adjustable_amounts["elec_cool"])
                        ) * demand_kv[elec]  # electricity for appliances
            # TODO: verify, that local elec_heat_prop works here
            # Scale based on electricity use in heat and elec mix
            demand_kv[elec] = prop * elec_heat_prop * self.total_fuel / self.elec_price
            demand_kv[elec] += elec_hold  # Add on the parts to do with appliances

        for liquid in LIQUID_TYPES:
            liquids_sum = demand_kv[LIQUID_TYPES].sum()
            if liquids_sum != 0:
                # Amount of each liquid in total liquid expenditure
                prop = demand_kv[liquid] / liquids_sum
                demand_kv[liquid] = prop * liquids_prop * \
                    combustable_fuels_prop * self.total_fuel
            else:
                demand_kv['Kerosene'] = liquids_prop * \
                    combustable_fuels_prop * self.total_fuel

        for solid in SOLID_TYPES:
            solids_sum = demand_kv[SOLID_TYPES].sum()
            if solids_sum != 0:
                # Amount of each solid in total solid expenditure
                prop = demand_kv[solid] / solids_sum
                demand_kv[solid] = prop * solids_prop * \
                    combustable_fuels_prop * self.total_fuel
            else:
                demand_kv[WOOD_PRODUCTS] = solids_prop * \
                    combustable_fuels_prop * self.total_fuel

        for gas in GAS_TYPES:
            gasses_sum = demand_kv[GAS_TYPES].sum()
            if gasses_sum != 0:
                # Amount of each gas in total gas expenditure
                prop = demand_kv[gas] / gasses_sum
                demand_kv[gas] = prop * self.gases_prop * \
                    combustable_fuels_prop * self.total_fuel

            else:
                demand_kv[DISTRIBUTION_GAS] = self.gases_prop * \
                    combustable_fuels_prop * self.total_fuel

        # The 'direct_ab' value should be changed to the value the user wants.
        # The user needs to convert the value into kg CO2e / Euro
        # 1.0475 # USER_INPUT
        ab_m.loc[self.direct_ab, DISTRICT_SERVICE_LABEL] = district_val


    def emission_calculation(self,
        policy_year=None, # U10.1
        pop_size_policy=None, # U10.2
        new_floor_area=0, # U10.3
        eff_gain=False,  # U11.1.0
        eff_scaler=0,  # U11.1.1
        local_electricity=False,  # U11.2.0
        # U11.2.1  'Electricity by solar photovoltaic','Electricity by biomass and waste',
        # 'Electricity by wind','Electricity by Geothermal'
        el_type = 'Electricity by solar photovoltaic',
        el_scaler = 0,  # U11.2.2
        s_heating = False,  # U11.3.0
        biofuel_takeup = False,  # U12.1.0
        bio_scaler = 0,  # U12.1.1
        ev_takeup = False,  # U12.2.0
        ev_scaler = 0,  # U12.2.1
        modal_shift = False,  # U12.3.0
        ms_fuel_scaler = 0,  # U12.3.1
        ms_veh_scaler = 0,  # U12.3.2
        ms_pt_scaler = 0,  # U12.3.3
        ):
        """
        This function can compute both a baseline, but also a six policies on an
        initialized consumption object.
        """

        if policy_year is None:
            policy_year=self.year

        if pop_size_policy is None:
            pop_size_policy = self.pop_size

        # if anything will be modified, this is not a baseline - TODO: check with Peter
        is_baseline = not (eff_gain or local_electricity or s_heating or ev_takeup or modal_shift)

        # Scale factor applied to income - unique value for each decade
        income_scaling = INCOME_PROJ_T.loc[self.country]

        # Scale factor applied to household size - unique value for each decade
        house_scaling = HOUSE_SIZE_PROJ_T.loc[self.country]

        # prepare empty dataframes
        # these are for the graphs
        df_main = pd.DataFrame(np.zeros((30, 8)), index=list(range(2020, 2050)),
                        columns=IW_SECTORS_T.columns)  # Holds final data in sectors 7 (+ sum)

        # df_tot = pd.DataFrame(np.zeros((30, 200)), index=list(range(2020, 2050)),
        #                     columns=PRODUCT_COUNT)  # holds final data in products (200)

        df_area = pd.DataFrame(np.zeros((30, 8)), index=list(range(2020, 2050)),
                            columns=IW_SECTORS_T.columns)  # Holds area emissions
                                                        # (multiplies by pop_size)


        for year_it in range(self.year, 2051):  # baseline year to 2050 (included)

            # check the policy part

            # if year_it == 2020:

            #     income_mult = 1 # This is just for the year 2020
            #     house_mult = 1  # This is just for the year 2020
            #     eff_factor = 1  # This is just for the year 2020

            ###########Policies are from here#####################################
            if not is_baseline and year_it == policy_year:

                #demand_kv = demand_kv_policy
                # house_size_ab = house_size_ab_policy  #Because we are not asking these questions
                pop_size = pop_size_policy

                ##############Household Efficiency################################

                if eff_gain:
                    self.eff_improvements(eff_scaler)

                ##############Local_Electricity###################################
                #######################U11.2######################################

                if local_electricity:
                    self.local_generation(self.emission_intensities, el_scaler, el_type)

                # TODO: district_value is never set in input material - check with Peter
                # district_value = ab_M.loc[direct_ab,district].sum() #copied from elsewhere
                self.district_value=0 # or given?
                if s_heating:
                    self.local_heating(self.emission_intensities, self.district_prop,
                        self.electricity_heat_prop, self.combustable_fuels_prop,
                        self.liquids_prop, self.gases_prop, self.solids_prop,
                        self.district_value) # TODO: check district_value is never set

                ###########Biofuel_in_transport####################
                if biofuel_takeup:
                    self.biofuels(bio_scaler)

                ########Electric_Vehicles##########################################
                ###### U12.2#############
                if ev_takeup:
                    self.electric_vehicles(ev_scaler)

                #########Modal_Shift####################################################
                #########U12.3#################
                if modal_shift:
                    self.transport_modal_shift(ms_fuel_scaler, ms_pt_scaler, ms_veh_scaler)

            if year_it > 2020 and year_it <= 2030:
                # Select the income multiplier for this decade
                income_mult = income_scaling['2020-2030']
                # Select the house multiplier for this decade
                house_mult = house_scaling['2020-2030']
                eff_factor = self.eff_scaling

            if year_it > 2030 and year_it <= 2040:
                # Select the income multiplier for this decade
                income_mult = income_scaling['2030-2040']
                # Select the house multiplier for this decade
                house_mult = house_scaling['2030-2040']
                eff_factor = self.eff_scaling

            if year_it > 2040 and year_it <= 2050:
                # Select the income multiplier for this decade
                income_mult = income_scaling['2040-2050']
                # Select the house multiplier for this decade
                house_mult = house_scaling['2040-2050']
                eff_factor = self.eff_scaling

            self.demand_kv *= income_mult

            self.emission_intensities *= eff_factor
            self.use_phase_ab *= eff_factor
            self.tail_pipe_ab *= eff_factor

            # Then we have to recalculate
            # GWP: Global Warming Potential (could be also called Emissions)

            gwp_ab = pd.DataFrame(self.emission_intensities.to_numpy().dot(
                np.diag(self.demand_kv.to_numpy())))  # This is the basic calculation
            gwp_ab.index = ['direct', 'indirect']
            gwp_ab.columns = PRODUCT_COUNT
            # This adds in the household heating fuel use
            use_phase_ab_gwp = self.demand_kv * self.use_phase_ab
            # This adds in the burning of fuel for cars
            tail_pipe_ab_gwp = self.demand_kv * self.tail_pipe_ab
            # This puts together in the same table (200 x 1)
            total_use_ab = tail_pipe_ab_gwp.fillna(0) + use_phase_ab_gwp.fillna(0)
            # all of the other 200 products are zero
            # Put together the IO and use phase
            gwp_ab.loc['Use phase', :] = total_use_ab

            #GWP_EE_pc = GWP_EE/House_size_EE
            # print(year_it)

            #GWP_EE = GWP_EE * (eff_factor) * (income_mult)
            gwp_ab_pc = gwp_ab / (self.house_size_ab * house_mult)

            # Put the results into sectors
            df_main.loc[year_it] = IW_SECTORS_NP_TR_T.dot(gwp_ab_pc.sum().to_numpy())
            # self.df_tot.loc[year_it] = gwp_ab_pc.sum()
            df_area.loc[year_it] = IW_SECTORS_NP_TR_T.dot(
                gwp_ab_pc.sum().to_numpy()) * self.pop_size # TODO: check which pop_size should be used here? base or policy

        df_main['Total_Emissions'] = df_main.sum(axis=1)
        df_area['Total_Emissions'] = df_area.sum(axis=1)


        ###########################################################################################
        # New Construction Emissions part!
        ###########################################################################################

        if not is_baseline:
            building_emissions = 0

            if self.country in NORTH:
                building_emissions = 350 * new_floor_area/pop_size

            if self.country in WEST:
                building_emissions = 520 * new_floor_area/pop_size

            if self.country in EAST:
                building_emissions = 580 * new_floor_area/pop_size

            df_main.loc[policy_year, 'Total_Emissions'] += building_emissions
            df_area.loc[policy_year, 'Total_Emissions'] += building_emissions * pop_size


        ###########################################################################################
        # End of Construction Emissions part!
        ###########################################################################################
        # Adding total emissions by multiplying by population

        # F_tot.columns = Exio_products
        result1 = df_main.copy()
        # locals()[region + "_Emissions_tot_" + policy_label] = DF_tot.copy()

        result2 = df_area.copy()

        return (result1, result2)

        ### end of emission calculation function ###


    ###################### end of policy methods/functions  ###################################


# Construction Emissions new part.

# This answers the question on the first policy page
# 2. Construction
# 2.1 New planned residential buildings in total gross square meters, m2"

# Baseline Version Peeter planner

# Baseline calculation here (policies is essentially the same calculation)
########### Explanation #######################
# The calculations work by describing the economy as being
# composed of 200 products, given by 'products'.
# For each product there is an emission intensity and they are collected
# together in ab_M.
# There are separate emission intensities for the 'direct production'
# and the 'indirect production' (rest of the supply chain).
# So ab_M is a 200 x 2 table.
# Some products that describe household fuel use for heat and
# also transport fuel use for cars have another emission
# intensity as well. These are held in separate tables
# 'use_phase' and 'tail_pipe' (all other products have 0 here)

# To calculate the emissions, each value in ab_M + the values in use_phase
# and tail_pipe are multiplied by the amount the household spends
# on each of the 200 products. These are stored in another table
# called demand_kv (demand vector).
# The emissions for each product from the direct production,
# indirect production, and use_phase/tail_pipe are summed
# to get the total emissions for that product.

# Once we have the total emissions for each product for that year,
# they are grouped together into 'sectors' that describe different things.
# There are 7 in total:
# Household Energy, Household Other, transport fuels, transport other, air transport, food,
# tangible goods, and services

# The calculations are performed every year until 2050,
# with the values of demand_kv and ab_M changing slighting each year.
# This is based on 3 factors, efficiency improvements,
# changes in income and changes in household size. There is also a
# section where these projections can change as a result
# of different policies (for the baseline no policies are introduced)

###################################################################################
# Determine Emissions for all years

######## Included in the start screen ##############################

def testcase_peter_planner():
    """
    Just a test case corresponding to the story
    """
    calculation = Consumption(
        year=2022, # required
        country="Ireland", # required
        pop_size=195000, # required
        region="County_Meath", # optional (else undefined)
        # area_type = "average",  # U9.4: average*, town, city, rural
        # eff_scaler = "normal", # U9.5: fast, normal*, slow
        )

    # baseline
    baseline_main, baseline_area = calculation.emission_calculation()


    policy_main, policy_area  = calculation.emission_calculation(
        policy_year=2025,
        pop_size_policy=205000,
        new_floor_area=0, # U10.3
        el_type = 'Electricity by solar photovoltaic', # U11.2.1
        el_scaler = 0.5,  # U11.2.2
        # s_heating = False,  # U11.3.0
        # # the following are already defined
        # # district_prop = 0.25 #USER_INPUT  U11.3.1
        # # electricity_heat_prop = 0.75 #USER_INPUT
        # # combustable_fuels_prop = 0.25 #USER_INPUT

        # # solids_prop = 0.0 #USER_INPUT   U11.3.2
        # # gases_prop = 0.0 #USER_INPUT
        # # liquids_prop = 0.0 #USER_INPUT
        # # District_value = ab_M.loc[direct_ab,district].sum() # ab_M   0.0 # USER_INPUT  U11.3.3
        # biofuel_takeup = False,  # U12.1.0
        # bio_scaler = 0.5,  # 12.1.1
        # ev_takeup = False, # U12.2.0
        # ev_scaler = 0.5,  # U12.2.1
        # modal_shift = False,  # U12.3.0
        # ms_fuel_scaler = 0.5,  # U12.3.1
        # ms_veh_scaler = 0.5,  # U12.3.2
        # ms_pt_scaler = 0.2,  # U12.3.3
        )

    ### Graphs are from here

    # First Graph is a breakdown of the Emissions as a stacked bar graph.
    # Maybe best to just show this one by itself?

    # Describe Emissions over time
    # The construction Emissions are now shown here.
    # I just added very quickly so please make better!

    fig, axis = plt.subplots(1, figsize=(15, 10))
    # Name of country Emissions
    country = "County_Meath"
    #policy_label = "BL"

    ###
    #x = np.arange(list(range(2020,2050)))
    # plot bars

    labels = ['HE', 'HO', 'TF', 'TO', 'AT', 'F', 'TG', 'S']
    sectors = list(IW_SECTORS_T.columns)

    bottom = len(baseline_main) * [0]
    for idx, name in enumerate(sectors):
        plt.bar(baseline_main.index, baseline_main[name], bottom=bottom)
        bottom = bottom + baseline_main[name]

    plt.bar(baseline_main.index, baseline_main['Total_Emissions'], edgecolor='black', color='none')

    axis.set_title("Annual Household Emissions for %s" % country, fontsize=20)
    axis.set_ylabel('Emissions / kG CO2 eq', fontsize=15)
    axis.tick_params(axis="y", labelsize=15)
    axis.set_xlabel('Year', fontsize=15)
    axis.tick_params(axis="x", labelsize=15)

    axis.legend(labels, bbox_to_anchor=([1, 1, 0, 0]), ncol=8, prop={'size': 15})


    plt.show()


    # Clicking on a bar or looking at a comparison between policies should generate this second graph
    # The labels below are just for different policies.

    # There should also be an option to remove the total emissions part
    # (This is basically only useful for new areas)


    # more graphs

    width = 0.2
    x = np.arange(len(baseline_main.columns))

    fig, axis = plt.subplots(figsize=(15, 10))

    rects1 = axis.bar(
        x + 0 * width, baseline_main.loc[2025], width, label='BL')
    # Extra policies
    rects2 = axis.bar(x - 1.5 * width,
                    policy_main.loc[2025], width, label='P1')
    # # Extra Policies
    # rects3 = axis.bar(x + 1.5 * width,
    #                 County_Meath_Emissions_P2.loc[2025], width, label='P2')
    # # rects4 = ax.bar(x - width / 2, Berlin_Emissions_NA.loc[2025], 
    # #                          width, label='NA')  # Extra Policies


    #plt.bar(x_sectors, E_countries_GWP_sectors_pp['EE'], width = 0.5,  color='green')
    #plt.bar(x_sectors, E_countries_GWP_sectors_pp['FI'], width = 0.5, color='blue', alpha = 0.5)
    axis.legend_size = 20
    axis.set_ylabel('Emissions / kG CO2 eq', fontsize=20)
    axis.set_xlabel('Emissions sector', fontsize=20)
    axis.set_title(
        'Per capita emissions by sector for County Meath policies', fontsize=25)
    axis.set_xticks(x)
    axis.set_xticklabels(baseline_main.columns, fontsize=15)
    #ax.set_yticklabels( fontsize = 15)
    axis.tick_params(axis="y", labelsize=15)
    axis.legend(prop={'size': 15})


    #x.label(rects1, padding=3)
    #x.label(rects2, padding=3)

    # lt.xlabel("Sectors")
    #lt.ylabel("CO2 eq /  kG?")
    #lt.title("Global Emissions by Sector")

    plt.xticks(x, baseline_main.columns, rotation=90)

    #plt.savefig("Sectoral_Graphs_breakdown.jpg",bbox_inches='tight', dpi=300)


    plt.show()

    # Finally, there should be some sort of cumulative emissions measurement.
    # Ths is also important in the case of delaying policies

    # This calculates the different cumulative emissions
    # THIS is just all the policies I made
    # Policy_labels = ["BL", "MSx50", "SHx50", "EVx50", "NA", "ALLx50_2035", "ALLx50_2025"]
    #    policy_labels = ["BL", "P1", "P2"]
    #    policy_labels = ["BL", "P1"]
    # Policy_labels = ["BL", "RFx50_2025", "RFx50_2035"]#for the graphs

    fig, axis = plt.subplots(1, figsize=(15, 10))
    # Name of country Emissions
    country = "County_Meath"
    region = "County_Meath"
    # Policy_labels = ["BL","EVx50", "MSx50", "SHx50", "NA"]
    #policy_labels = ["BL", "P1", "P2"]

    policy_frames = [(baseline_main, "BL"), (policy_main, "P1")]
    counter = 0
    for policy, policy_abbr in policy_frames:
        # Describe Emissions over time
        # TODO: no idea what is going here - need to verify my translation
        # locals()[region + "_summed_" + policy] = 
        #   pd.DataFrame(np.zeros((30,1)),index = list(range(2020,2050)),
        #       columns = ["Summed_Emissions"])
        policy_summed = pd.DataFrame(np.zeros((30, 1)),
                        index=list(range(2020, 2050)), columns=["Summed_Emissions"])

        # locals()[region + "_summed_" + policy].loc[2020, "Summed_Emissions"] =
        #      locals()[region + "_Emissions_" + policy].loc[2020,'Total_Emissions']
        policy_summed.loc[2020, "Summed_Emissions"] = policy.loc[2020, 'Total_Emissions']

        # years = list(range(2020,2050))
        years = list(range(2020, 2050))

        # for year in years:
        #     locals()[region + "_summed_" + policy].loc[year+1,"Summed_Emissions"] =
        #       locals()[region + "_summed_" + policy].loc[year,"Summed_Emissions"]
        #       + locals()[region + "_Emissions_" + policy].loc[year+1,'Total_Emissions']
        for year in years:
            policy_summed.loc[year+1, "Summed_Emissions"] = (
                policy_summed.loc[year, "Summed_Emissions"]
                + baseline_main.loc[year+1, 'Total_Emissions'])

        # print("The Emissions in 2025 for %s is" % policy,
        #   locals()[region + "_Emissions_" + policy].loc[2025,'Total_Emissions'])
        print("The Emissions in 2025 for %s is" % policy_abbr,
            baseline_main.loc[2025, 'Total_Emissions'])


        # Make the graph

        dataframe = policy_summed.copy()
        ###
        #x = np.arange(list(range(2020,2050)))
        # plot bars

        #Labels = ['HE','HO','TF','TO','AT','F','TG','S']
        sectors = list(IW_SECTORS_T.columns)

        #bottom = len(DF) * [0]
        # for idx, name in enumerate(sectors):
        #   plt.bar(self.df_main.index, self.df_main[name], bottom = bottom)
        #  bottom = bottom + self.df_main[name]

        plt.plot(dataframe.index, dataframe.Summed_Emissions, )

        plt.fill_between(dataframe.index, dataframe.Summed_Emissions, alpha=0.4)  # +counter)

        counter += 0.1

    #x = np.arange(len(Ireland_Emissions.index))
    #width = 0.8

    #rects1 = ax.bar(x, Ireland_Emissions['Housing_Energy'], width, label=abbrev)

    axis.set_title("Aggregated per capita Emissions for %s 2020-2050" %
                country, fontsize=20)
    axis.set_ylabel('Emissions / kG CO2 eq', fontsize=15)
    axis.tick_params(axis="y", labelsize=15)
    axis.set_xlabel('Year', fontsize=15)
    axis.tick_params(axis="x", labelsize=15)

    axis.legend(["BL", "P1"], loc='upper left', ncol=2, prop={'size': 15})

    #plt.savefig("Cumulative_example_high_buildphase.jpg",bbox_inches='tight', dpi=300)


    plt.show()

    print("County_Meath_Emissions_baseline", baseline_main)

    print("County_Meath_Emissions_policy", policy_main)


def main():
    """
    Simple main that can run a test.
    """
    testcase_peter_planner()

if __name__ == "__main__":
    main()
