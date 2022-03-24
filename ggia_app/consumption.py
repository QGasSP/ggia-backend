#!/usr/bin/env python
# coding: utf-8


# Calculation_Example

# Loading Python Libraries
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

### CSV import
# Load the projections for income and housesize
House_proj = pd.read_csv("data/House_proj_exio.csv" , index_col = 0)
Income_proj = pd.read_csv("data/Income_proj_exio.csv" , index_col = 0)

# Load the different Y vectors.
# The user selects which one
# to use based on the urban density of the region (or the
# average one for mixed regions or if they are unsure)
Y_average = pd.read_csv("data/Average_2020_Exio_elec_trans_en_Euro.csv", index_col = 0)
Y_city = pd.read_csv("data/City_2020_Exio_elec_trans_en_Euro.csv", index_col = 0)
Y_rural = pd.read_csv("data/Rural_2020_Exio_elec_trans_en_Euro.csv", index_col = 0)
Y_town = pd.read_csv("data/Town_2020_Exio_elec_trans_en_Euro.csv", index_col = 0)

# Load the Use phase and tail pipe emissions.
Use_phase =  pd.read_csv("data/Energy_use_phase_Euro.csv", index_col = 0)
Tail_pipe =  pd.read_csv("data/Tailpipe_emissions_bp.csv", index_col = 0)

# Load default house sizes
House_size = pd.read_csv("data/Household_characteristics_2015.csv", index_col = 0)

# Load the Emission intensities
# M_countries is the standard Emissions factors
M_countries = pd.read_csv("data/Country_Emissions_intensities.csv", index_col = 0)

# M_countries_LCA is the same as M_countries, but with the electricity sector replaced with individual LCA values
# This is useful if there is local electricity production. The user can replace certain values with these values 
# if needed
M_countries_LCA = pd.read_csv("data/Country_Emissions_intensities_LCA.csv", index_col = 0)
products = M_countries.columns
Exio_products = pd.read_csv("data/Exio_products.csv")

# Load the IW sectors
# This is needed to put the emissions into different 'sectors', such as transport, food, building energy use, etc
IW_sectors = pd.read_csv("data/IW_sectors_reduced.csv", index_col = 0)
IW_sectors_np = IW_sectors.to_numpy()
IW_sectors_np_tr = np.transpose(IW_sectors_np)

# Load the adjustable amounts.
# This says how much electricity is spent on heating. There are some other things here but decided not to include.
Adjustable_amounts = pd.read_csv("data/Adjustable_energy_amounts.csv", index_col = 0)

# Electricity prices database might need updating still - TODO: we could think about that later
# Load the electricity prices. This is so we know in monetary terms how much is being spent on electricity. The tool
# at the moment has the electricity used by households in kWh. However, maybe this should now be changed?
Electricity_prices = pd.read_csv("data/electricity_prices_2019.csv", index_col = 0)

# Load the fuel prices at basic price
# We need this because of electric vehicles. The electricity and fuels need to be in the same units.
Fuel_prices = pd.read_csv("data/Fuel_prices_BP_attempt.csv", index_col = 0)

# Load the Income scaler. This describes how much each household spends depending on their income.
Income_scaling = pd.read_csv("data/mean_expenditure_by_quint.csv", index_col = 0)


### Policy "functions"
# The different Policies are written as functions to reduce the length of the calculation code

def BioFuels(demand_KV, scaler):
    """
    This is a policy.
    
    *Explanation*
    This sort of policy acts only on the Expenditure (Intensities don't change)
    Similar polices could exist for housing fuel types, ...
    Similar adjustments to this could also be needed to correct the baselines if the user knows the 
    results to be different

    Local Inputs:
    - demand_KV['Biogasoline']
    - demand_KV['Biodiesels']
    - demand_KV['Motor Gasoline']
    - demand_KV['Gas/Diesel Oil']

    Outputs:
    - demand_KV['Biogasoline'] - careful, this means this field is permanently changed after a call to this method
    - demand_KV['Biodiesels'] - careful, this means this field is permanently changed after a call to this method
    - demand_KV['Motor Gasoline'] - careful, this means this field is permanently changed after a call to this method
    - demand_KV['Gas/Diesel Oil'] - careful, this means this field is permanently changed after a call to this method
    """
    
    #
    # current_biofuels = demand_KV['Biogasaline'] + demand_KV['biodiesel'] / 
    
    
    ## Step 1. Determine current expenditure on fuels and the proportions of each type
    
    Total_fuel = demand_KV['Biogasoline'] + demand_KV['Biodiesels'] + demand_KV['Motor Gasoline'] + demand_KV['Gas/Diesel Oil']
        
    Diesel = (demand_KV['Biodiesels'] + demand_KV['Gas/Diesel Oil'])
        
    Petrol = (demand_KV['Motor Gasoline'] + demand_KV['Biogasoline'])
    
    # Step 1.1 current_biofuels = (demand_KV['Biogasoline'] + demand_KV['Biodiesels']) / Total_fuel 
        
    # Step 2. Increase the biofuel to the designated amount
        
    demand_KV['Biogasoline'] = scaler * Total_fuel * (Petrol/ (Diesel + Petrol))
    demand_KV['Biodiesels'] =  scaler * Total_fuel * (Diesel / (Diesel + Petrol))
        
    # Step 3. Decrease the others by the correct amount, taking into account their initial values
        
    # The formula to do this is :
    # New Value = Remaining_expenditure * Old_proportion (once the previous categories are removed)
        
    Sum_changed = demand_KV['Biogasoline'] + demand_KV['Biodiesels']  # This can't be more than the total! - TODO: assert?

    if Sum_changed > Total_fuel:
        # TODO: exception
        pass
        
    demand_KV['Motor Gasoline'] = (Total_fuel - Sum_changed) * (Petrol / (Diesel + Petrol))
    demand_KV['Gas/Diesel Oil'] = (Total_fuel - Sum_changed) * (Diesel / (Diesel + Petrol))
    

def Electric_Vehicles(demand_KV, scaler):
    """
    This is a policy.

    *Explanation*

    xx% of vehicles are ev
    First we reduce the expenditure on all forms of transport fuels by xx%
    Then, we need to add something onto the electricity
    
    For this we need to: calculate how much fuel is saved and convert it back into Liters (and then kWh)
    Take into account the difference in efficiency between the two types
    Add the kWh evenly onto the electricity sectors
    
    Explanation/Description
    This sort of policy acts only on the Expenditure 

    Local Inputs:
    - demand_KV['Biodiesels']
    - demand_KV['Gas/Diesel Oil']
    - demand_KV['Motor Gasoline']
    - demand_KV['Biogasoline']
    - demand_KV[electricity] - seems to be a list of values (as later sum used)

    Global Inputs:
    - country - string of a country name
    - Fuel_prices.loc['Diesel_2020', country]
    - Fuel_prices.loc['petrol_2020', country]
    - electricity - list of labels for different electricity types

    Outputs:
    - demand_KV[electricity] - careful, this means this (these) field is permanently changed after a call to this method

    """

        
    # Step 1 Assign a proportion of the fuels to be converted and reduce the fuels by the correct amount
        
    Diesel = (demand_KV['Biodiesels'] + demand_KV['Gas/Diesel Oil'])*scaler
        
    Petrol = (demand_KV['Motor Gasoline'] + demand_KV['Biogasoline'])*scaler
        
    Fuels = ['Biodiesels', 'Gas/Diesel Oil', 'Motor Gasoline', 'Biogasoline']
        
    for fuel in Fuels:    
        demand_KV[fuel] = demand_KV[fuel]*(1-scaler)
        
    # Step 2 Turn the amount missing into kWh
    Diesel /= Fuel_prices.loc['Diesel_2020', country]
    Petrol /= Fuel_prices.loc['petrol_2020', country]
        
    Diesel *= 38.6*0.278   # liters, then kWh
    Petrol *= 34.2*0.278   # liters, then kWh
        
    # Step 3. #Divide that amount by 4.54 (to account foe the efficiency gains) 
    Diesel /= 4.54         # Efficiency saving
    Petrol /= 4.54         # Efficiency saving
        
    # Step 4. Assign this to increased electricity demand 
    Elec_vehicles = Diesel + Petrol      
    elec_total = demand_KV[electricity].sum()
    elec_scaler = (Elec_vehicles + elec_total) / elec_total
        
    demand_KV[electricity] *= elec_scaler  # is this a working vector operation?
        

def Eff_improvements(demand_KV, scaler):
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
    - electricity - set of labels/strings marking electricity entries in demand_KV
    - ad["elec_water"]
    - ad["elec_heat"]
    - ad["elec_cool"]
    - district

    Local Inputs:
    - demand_KV <- all liquids, solids, and gases, electricity entries
    - demand_KV['Gas/Diesel Oil']
    - demand_KV['Motor Gasoline']
    - demand_KV['Biogasoline']
    - demand_KV[electricity] - seems this time to be a list of values (as later sum used)

    Outputs:
    - demand_KV[district] - not sure if this is a side effect or not

    """
      
    # Step 1. This can be done as a single stage. 
    # Just reduce the parts that can be reduced by the amount in the scaler
            
    for liquid in liquids:
        demand_KV[liquid] = (demand_KV[liquid] * (1 - scaler))
            
    for solid in solids:
        demand_KV[solid] = (demand_KV[solid] * (1 - scaler))
        
    for gas in gases:
        demand_KV[gas] = (demand_KV[gas] * (1 - scaler)) 
                                                            
    for elec in electricity:
        elec_hold = demand_KV[elec] * (1 - (ad["elec_water"] + ad["elec_heat"] + ad["elec_cool"]))  # Parts not related to heating/cooling etc
        demand_KV[elec] = (demand_KV[elec] * (ad["elec_water"] + ad["elec_heat"] + ad["elec_cool"]) * (1-scaler)) 
        demand_KV[elec] += elec_hold
            
    demand_KV[district] = demand_KV[district]*(1-scaler) 
        


def Transport_Modal_Shift(demand_KV, scaler, scaler_2, scaler_3):
    """
    This is a policy.

    *Explanation*
    
    Modal share - decrease in private transport and increase in public transport
    
    This sort of policy acts only on the Expenditure (Intensities don't change)
    The expenditure on private transport is reduced by a certain amount (1 part for fuels and 1 for vehicles)
    
    The public transport is also increased by a different amount. This is to account for the effects of active travel
    
    Global Inputs:
    - public_transport - list of labels

    Local Inputs:
    - demand_KV['Gas/Diesel Oil']
    - demand_KV['Motor Gasoline']
    - demand_KV['Biogasoline']
    - demand_KV[electricity] - seems to be a list of values (as later sum used)
    - demand_KV['Motor vehicles, trailers and semi-trailers (34)']
    - demand_KV['Sale, maintenance, repair of motor vehicles, motor vehicles parts, motorcycles, motor cycles parts and accessoiries']
    - demand_KV <- for all public_transports 

    Outputs:
    - demand_KV['Motor vehicles, trailers and semi-trailers (34)'] - careful, this means this field is permanently changed after a call to this method
    - demand_KV['Sale, maintenance, repair of motor vehicles, motor vehicles parts, motorcycles, motor cycles parts and accessoiries'] - - careful, this means this field is permanently changed after a call to this method
    - demand_KV <- for all public_transports - careful, this means this field is permanently changed after a call to this method

    """
         
    Fuels = ['Biodiesels', 'Gas/Diesel Oil', 'Motor Gasoline', 'Biogasoline']
    for fuel in Fuels:
        demand_KV[fuel] *= (1-scaler)
        #In this case, we also assume that there is a reduction on the amount spent on vehicles
        #Change in modal shift takes vehicles off the road?

    Vehicles = ['Motor vehicles, trailers and semi-trailers (34)', 
                   'Sale, maintenance, repair of motor vehicles, motor vehicles parts, motorcycles, motor cycles parts and accessoiries']
    for vehicle in Vehicles:
        demand_KV[vehicle] *=(1-scaler_3)
        
    for transport in public_transport:  # Public transport was defined above
        demand_KV[transport] *= (1+scaler_2)
        

def Local_generation(ab_M, demand_KV, scaler, type_electricity):
    """
    This is a policy.

    *Explanation*
    
    Local electricity is produced by (usually) rooftop solar and it is utilized only in that area
        
    Reduce current electricity by xx %
    Introduce a new electricity emission intensity (based on PV in the LCA emission intensities) 
    that accounts for the missing xx %    

    Global Inputs:
    - direct_ab
    - indirect_ab
    - electricity: here it's used a field of labels again

    Local Inputs:
    - demand_KV['Electricity nec']
    - M_countries_LCA.loc[direct_ab:indirect_ab,type_electricity]


    Outputs:
    - ab_M.loc[direct_ab:indirect_ab,'Electricity nec']
    - demand_KV['Electricity nec'] - careful, this means this field is permanently changed after a call to this method

    """
    
    elec_total = demand_KV[electricity].sum()
    
    for elec in electricity:
        
        demand_KV[elec] = (demand_KV[elec] * (1 - scaler))
        
    # Assign the remaining amount to the spare category (electricity nec)    
    demand_KV['Electricity nec'] = elec_total * scaler

    # Set the emission intensitiy of this based on LCA values
    ab_M.loc[direct_ab:indirect_ab,'Electricity nec'] = M_countries_LCA.loc[direct_ab:indirect_ab,type_electricity]


def local_heating(ab_M, demand_KV, district_prop, elec_heat_prop, 
        combustable_fuels_prop, liquids_prop, gas_prop, solids_prop, district_val):
    """
    Is this a policy? It has a lot of nice input values.

    THIS JUST REPEATS BASELINE QUESTIONS 9 - 10.
    ALLOWING THE USER TO CHANGE THE VALUES

    Global Inputs:
    - district
    - direct_ab
    - Total_Fuel
    - electricity: here it's used a field of labels again
    - ad["elec_water"]
    - ad["elec_heat"]
    - ad["elec_cool"]
    - elec_total
    - liquids
    - solids

    Local Inputs:
    - demand_KV[elec] for all labels in electricity
    - demand_KV[liquid] for all labels in liquids
    
    Outputs:
    - demand_KV[elec] for all labels in electricity. Careful, this means these fields are permanently changed after a call to this method
    - demand_KV[liquid] for all labels in liquids. Careful, this means these fields are permanently changed after a call to this method
    - demand_KV['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)']
    - demand_KV['Distribution services of gaseous fuels through mains']
    - ab_M.loc[direct_ab,district] - careful, this means this field is permanently changed after a call to this method

    """

    # DISTRICT HEATING
    demand_KV[district] = Total_Fuel * district_prop


    # ELECTRICITY
    for elec in electricity:
        prop = demand_KV[elec] / elec_total # determine amount of each electricity source in total electricity mix.
        elec_hold = (1 - (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"])) * demand_KV[elec] # electricity for appliances
        # TODO: verify, that local elec_heat_prop works here
        demand_KV[elec] = prop * elec_heat_prop * Total_Fuel / elec_price # Scale based on electricity use in heat and elec mix
        demand_KV[elec] += elec_hold # Add on the parts to do with appliances
    

    for liquid in liquids:
        liquids_sum = demand_KV[liquids].sum()
        if  liquid_sum != 0:
            prop = demand_KV[liquid] / liquids_sum  # Amount of each liquid in total liquid expenditure
            demand_KV[liquid] = prop * liquids_prop * combustable_fuels_prop * Total_Fuel
        else:
            demand_KV['Kerosene'] = liquids_prop * combustable_fuels_prop * Total_Fuel
        
        
    for solid in solids:
        solids_sum = demand_KV[solids].sum() 
        if solids_sum != 0:
            prop = demand_KV[solid] / solids_sum  # Amount of each solid in total solid expenditure
            demand_KV[solid] = prop * solids_prop * combustable_fuels_prop * Total_Fuel
        else:
            demand_KV['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)'] = solids_prop * combustable_fuels_prop * Total_Fuel

        
    for gas in gases:
        gasses_sum = demand_KV[gases].sum()
        if gasses_sum != 0:
            prop = demand_KV[gas] / gasses_sum  # Amount of each gas in total gas expenditure
            demand_KV[gas] = prop * gases_prop * combustable_fuels_prop * Total_Fuel

        else:
            demand_KV['Distribution services of gaseous fuels through mains'] = gases_prop * combustable_fuels_prop * Total_Fuel


    # The 'direct_ab' value should be changed to the value the user wants. 
    # The user needs to convert the value into kg CO2e / Euro 
    ab_M.loc[direct_ab,district] = district_val ####1.0475 # USER_INPUT


###################### end of policy methods/functions  ##########################################



"""
Construction Emissions new part. 

This answers the question on the first policy page 
"2. Construction 
2.1 New planned residential buildings in total gross square meters, m2"
"""


North = ['Denmark', 'Finland' , 'Sweden' , 'Norway' , 'Iceland']

West = ['Austria', 'Belgium', 'Germany', 'Spain', 'France' , 'Ireland', 'Italy' , 'Luxembourg' , 'Malta', 'Netherlands',
       'Portugal', 'United Kingdom', 'Switzerland' , 'Liechtenstein']

East = ['Bulgaria', 'Cyprus', 'Czechia', 'Estonia', 'Greece', 'Hungary', 'Croatia', 'Lithuania', 'Latvia', 'Poland', 
       'Romania', 'Slovenia', 'Slovakia', ]



###LIST of Variables from here#############################################################################
# All values have defaults apart from the ones with
# required. So the minimum data required by the user for the
# baseline is filling in the required data.

# I don't know how to make it so that the default variables are loaded and can then be changed by the user.
# I think it would be necessary to recall the data from the server after the first consumption calculations screen.

year = int()   # required
Region = str()   # required - Equivalent to "name the project"
Policy_label = str() # I ask this to differentiate between policies, but maybe the tool has another way.
country = str()   # Required
ab =str()      # This can be combined with the one above

target_area = str() # Required #3 options in dropdown menu
U_type =str()   # Required #4_options in drop down menu - mixed, rural, city, town
pop_size = int() # Required - completely open


house_size = float() # completely open, but with a default value.
income_level = str() # There are 5 options in a drop down menu

eff_scaling = float() # default value should be 0.97 (equivalent to 3 %)

river_prop = float()
ferry_prop = float()
rail_prop = float()
bus_prop = float()       # These values should sum to 1 (or 100 %) They all have a default value

hydro_prop = float()         # These are all to do with electricity mix 99% of time should use default values
solar_pvc_prop = float()
coal_prop = float()
gas_prop = float()
nuclear_prop = float()
wind_prop = float()
petrol_prop = float()
solar_thermal_prop = float()
tide_prop = float()
geo_prop = float()
nec_prop = float()           # Last electricity mix  #These values should sum to 1 (or 100 %)

district_prop = float()
electricity_heat_prop = float()
combustable_fuels_prop = float()    # These 3 values should sum to 1 (or 100 %)

liquids_prop = float()
solids_prop = float()
gases_prop = float()                # These 3 values should sum to 1 (or 100 %)

direct_district_emissions = float()  # A default value os given.

#### These are all the inputs required for the baseline

### For the policies, the following additional questions are required (as well as those above)
policy_year = int()   # required - This question has been missed in the UI


Eff_gain = str()     # required
Eff_scaler = float()  

Local_electricity = str()
EL_Type = str() # 3 options from drop_down menu
EL_scaler = float()

S_heating = str() # required

Biofuel_takeup = str() # required
bio_scaler = float()

EV_takeup = str() # required
EV_scaler = float()

Modal_Shift = str() # required
MS_fuel_scaler = float()
MS_pt_scaler = float()
MS_veh_scaler = float()

New_floor_area = float() # default is zero


"""
A note about the different types of area (existing area, partially existing area, new area)

Existing_area:

Here the calculation works as usually understood. E.g. calculate the baseline and then calculate policy changes and 
compare them.

Partially existing area:

This corresponds to new developments (and new populations) within an existing area.

Here, the baseline is calculated representing the existing population.
Then, the 'policy' represents the new population. The final result 
should be a weighted sum of the two (weighted by population). And this is what is compared against the baseline

New area:

Here, there is 0 original population. So the baseline calculation should be zero before the year of the policy
(which corresponds to the year of the development)


"""


## Baseline Version Peeter planner



# Baseline calculation here - policies is essentially the same calculation
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
# called demand_KV (demand vector).
# The emissions for each product from the direct production,
# indirect production, and use_phase/tail_pipe are summed 
# to get the total emissions for that product.

# Once we have the total emissions for each product for that year,
# they are grouped together into 'sectors' that describe different things.
# There are 7 in total: 
# Household Energy, Household Other, transport fuels, transport other, air transport, food, 
# tangible goods, and services

# The calculations are performed every year until 2050, 
# with the values of demand_KV and ab_M changing slighting each year.
# This is based on 3 factors, efficiency improvements, 
# changes in income and changes in household size. There is also a 
# section where these projections can change as a result 
# of different policies (for the baseline no policies are introduced)

##################################################################################################################
##################################################################################################################
# Determine Emissions for all years

######## Included in the start screen ##############################

################ Question 9.0 ##################################
year = 2022
region = "County_Meath" # User_input

## U9.1
policy_label = "BL"  # This is just a label for the policy. Or the tool has a way to select different policies.

## U9.0
country = "Ireland"  # This is to choose the country - USER_INPUT
ab = "IE"            # This is to identify the country, should match above

# Population_size
pop_size = 195000 #USER_INPUT

# now create a local variable with name "pop_size" + Policy_label
# here in this example it would be equivalent to 
# pop_sizeBL = pop_size
# TODO: check what this could be used for later
locals() ["pop_size" + Policy_label] = pop_size   # create local variable with name "pop_size" + Policy_label

##################################################################################
# Additional questions for the baseline
# For a simple example, we use defaults for all of them

## U9.2
# This is to select the demand vector - the user should choose
U_type = "average" # 'average', 'town', 'city', 'rural'  

# Extracting the correct demand vector - this is the initialization of demand_KV
demand_KV = locals() ["Y_" + U_type][country].copy() # TODO: why is that pumped through locals?


## U9.3: House_size - also extracted
House_size_ab = House_size.loc['Average_size_'+ U_type, country] # This is the default
# House_size_ab = 2.14 #xx###USER_INPUT would look like this here

## U9.4:Income_scaler
### options are "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
### 1st household is the richest.
Income_choice =  "3rd_household"  
# Otherwise,  the user selects the income level of the household (they choose by quntiles)
Income_scaler = Income_scaling.loc[Income_choice,country] / Income_scaling.loc['Total_household',country] # USER_INPUT
Elasticity = 1 # Random number for now. It should be specific to country and product

#if Income_choice == "3rd_household":
#    Income_scaler = 1

demand_KV *= Income_scaler * Elasticity
##############################################################################################




## U9.5: This is the expected global reduction in product emissions
# Suggestion - Just give the user one of three options, with the default being normal

fast = 0.07
normal = 0.03
slow = 0.01

eff_scaling = 1 - normal #USER_INPUT



##############################################################
# Forming data for the calculations
# These are needed for holding the results
DF = pd.DataFrame(np.zeros((30,8)),index = list(range(2020,2050)), 
            columns = IW_sectors.columns)  # Holds final data in sectors 7 (+ sum)

DF_tot = pd.DataFrame(np.zeros((30,200)), index = list(range(2020,2050)),
            columns = products) # holds final data in products (200)

DF_area = pd.DataFrame(np.zeros((30,8)),index = list(range(2020,2050)),
            columns = IW_sectors.columns)  # Holds area emissions (multiplies by pop_size
                                                      
direct_ab = "direct_"+ab
indirect_ab = "indirect_"+ab
M_countries.loc[direct_ab:indirect_ab,:].copy()

# Here the emission intensities are selected                                                                        
ab_M = locals() [ab + "_M"] = M_countries.loc[direct_ab:indirect_ab,:].copy()

# These are needed for the use phase emissions
Tail_pipe_ab = Tail_pipe[country].copy()
Use_phase_ab = Use_phase[country].copy()

# This is needed for calculating the amount of electricity coming from heating
ad = Adjustable_amounts[country].copy()
elec_price = Electricity_prices[country]["BP_2019_S2_Euro"] 

# Baseline Modifications go here  ##Possibly not included in this version of the tool###########
################ end of the mandatory questions #######################


#################################################################################################
## Optional questions
# Here the user can modify the default values for the the demand. IF THEY DON'T WANT TO THEN SKIP THIS PART.


######### Question 8 ##########################################################
# Public Transport types
public_transport = ['Railway transportation services', 
                    'Other land transportation services', 
                    'Sea and coastal water transportation services',
                    'Inland water transportation services']

Public_transport_sum = demand_KV[public_transport].sum()  # This describes the total use of public transport
    
rail_prop = demand_KV['Railway transportation services'] / Public_transport_sum
bus_prop = demand_KV['Other land transportation services'] / Public_transport_sum
ferry_prop = demand_KV['Sea and coastal water transportation services'] / Public_transport_sum
river_prop = demand_KV['Inland water transportation services'] / Public_transport_sum
    
    
# These 'prop' values can be adjustable by the user. 
# For example, if the user thinks there should be no water based travel this can be set to 0
# but then the other values should be increased so that total proportions sum to equal to 1
    
# In such a case, the code to do this would be
    
#river_prop = 0#USER_INPUT (often 0)
#ferry_prop = 0#USER_INPUT (often 0)
#bus_prop = bus_prop / (bus_prop + rail_prop) #USER_INPUT - code maintains the ratio between bus and rail
#rail_prop = rail_prop / (bus_prop + rail_prop) #USER_INPUT - code maintains the ratio between bus and rail

#ferry_prop = ferry_prop / (bus_prop + ferry_prop+ rail_prop)

# The values that should be adjusted are:

demand_KV['Railway transportation services'] = rail_prop * Public_transport_sum
demand_KV['Other land transportation services'] = bus_prop * Public_transport_sum
demand_KV['Sea and coastal water transportation services'] = ferry_prop * Public_transport_sum
demand_KV['Inland water transportation services'] = river_prop * Public_transport_sum

   
# Otherwise, if there is no rail travel or river/sea travel then it should be:
#rail_prop = 0
#river_prop = 0
#ferry_prop = 0
#bus_prop = 1
       
########## end Question 8 ############################################################


######### Question 9 ##################################################################################
# Electricity _ mix
# IT SHOULD BE SUGGESTED TO LEAVE THE DEFAULT VALUES 
# As above, the user can specify if the electricity mix is different to the country average for the BL

# Types of electricity
# No electricity goes in 'electricity nec'. This is used for local electricity production    
electricity = [
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
    'Electricity nec'] 


elec_total = demand_KV[electricity].sum()
    
# The code works the same as above the the public transport.    
# e.g.   
#hydro_prop = 0.7
#solar_pvc_prop = 0.3
#coal_prop = 0
#gas_prop = 0
#nuclear_prop = 0
#wind_prop = 0
#petrol_prop = 0
#solar_thermal_prop = 0
#tide_prop = 0
#geo_prop = 0
#nec_prop = 0

# Then the total kWh is determined from these props
#demand_KV[electricity] = 0
    
#demand_KV['Electricity by solar photovoltaic'] = solar_pvc_prop * elec_total
#demand_KV['Electricity by hydro'] = hydro_prop * elec_total
    
    
# if the user specifies the mix, then the electricity values change to the LCA values:

# for elec in electricity:  
#   ab_M.loc[direct_ab:indirect_ab,electricity] = M_countries_LCA.loc[direct_ab:indirect_ab,electricity] 

#IT SHOULD BE SUGGESTED THAT THE USER DOES NOT ALTER THE ELECTRICITY MIX
####### end of Question 9 #############################################################################


####### Question 10 ##########################################################
    
# Supply of household heating
liquids = [
    'Natural Gas Liquids', 
    'Kerosene', 
    'Heavy Fuel Oil', 
    'Other Liquid Biofuels']
solids = [
    'Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)',
    'Coke Oven Coke']
gases = [
    'Distribution services of gaseous fuels through mains', 
    'Biogas']
        
district = 'Steam and hot water supply services'
        
electricity_heat = (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"]) * elec_total * elec_price
        
Total_Fuel = demand_KV[solids].sum() + demand_KV[liquids].sum() + demand_KV[gases].sum() + demand_KV[district].sum() + electricity_heat

# We assume all 'fuels' are the same efficiency (obviously wrong, but no time to fix)
        
#########################
# PART 1 - The user selects the heating proportions from district heating, electricity and household combustion
#########################


# Default values are given by:
district_prop = demand_KV[district] / Total_Fuel

electricity_heat_prop = electricity_heat / Total_Fuel

combustable_fuels_prop = (demand_KV[solids].sum() + demand_KV[liquids].sum() + demand_KV[gases].sum()) / Total_Fuel

### THE USER CAN ALTER THESE BY::

# THESE NUMBERS NEED TO SUM TO 1
#district_prop = 0.0 #district_prop#1##USER_INPUT
#electricity_heat_prop = 1.0 #electricity_heat_prop##USER_INPUT
#combustable_fuels_prop = 0.0 #combustable_fuels_prop##USER_INPUT

######################################
## Part 2 - Determine final values
######################################

# Then, the final values are given by:

# DISTRICT HEATING
demand_KV[district] = Total_Fuel * district_prop


#ELECTRICITY
for elec in electricity:
    prop = demand_KV[elec] / elec_total #determine amount of each electricity source in total electricity mix.
    elec_hold = (1 - (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"])) * demand_KV[elec] #electricity for appliances
    demand_KV[elec] = prop * electricity_heat_prop * Total_Fuel / elec_price #Scale based on electricity use in heat and elec mix
    demand_KV[elec] += elec_hold #Add on the parts to do with appliances
    
        
# COMBUSTABLE FUELS

# Here, the user can also alter the mix of the combustable fuels.

liquids_prop = demand_KV[liquids].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())
solids_prop = demand_KV[solids].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())
gases_prop = demand_KV[gases].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())

#THE USER CAN CHANGE THESE VALUES BUT THE SUM MUST BE EQUAL TO 1!

############Question 10.1######################
#liquids_prop = 0 # #USER INPUT
#solids_prop = 0 ##USER_INPUT
#gases_prop = 1 # #USER_INPUT


#Then

for liquid in liquids:
    
    if demand_KV[liquids].sum() != 0:
        
        prop = demand_KV[liquid] / demand_KV[liquids].sum()  #Amount of each liquid in total liquid expenditure
        demand_KV[liquid] = prop * liquids_prop * combustable_fuels_prop * Total_Fuel
    else:
        
        demand_KV['Kerosene'] = liquids_prop * combustable_fuels_prop * Total_Fuel
        

        
for solid in solids:
    
    if demand_KV[solids].sum() != 0:
        prop = demand_KV[solid] / demand_KV[solids].sum()  #Amount of each solid in total solid expenditure
        demand_KV[solid] = prop * solids_prop * combustable_fuels_prop * Total_Fuel
    
    else:
        demand_KV['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)'] = solids_prop * combustable_fuels_prop * Total_Fuel

        
for gas in gases:
    
    if demand_KV[gases].sum() != 0:
        prop = demand_KV[gas] / demand_KV[gases].sum()  #Amount of each gas in total gas expenditure
        demand_KV[gas] = prop * gases_prop * combustable_fuels_prop * Total_Fuel

    else:
        demand_KV['Distribution services of gaseous fuels through mains'] = gases_prop * combustable_fuels_prop * Total_Fuel

######QUESTION 11###########################################
    #The 'direct_ab' value should be changed to the value the user wants. 
    #The user needs to convert the value into kg CO2e / Euro 
direct_district_emissions = ab_M.loc[direct_ab,district]#1.0475#USER_INPUT
ab_M.loc[direct_ab,district] = direct_district_emissions
################################################################

###This is the end of the additional baseline questions################################################
######################################################################

##Basic policy questions go here######################################

###Here, we are essentially just asking the questions we asked for the BL again. The problem is that before the 
##policy year (in this case 2025), the values should be equal to the baseline. So I have just redefined the variables
##here. But for the tool if all variables are predefined and then sent to a funciton to run the calculation, would they 
## need to be new variables?



if policy_label != "BL":   #Not sure if I need. Maybe can just set the policy year to 2050 as default
    
    ####################User enters the policy year U10.1
    policy_year = 2025#USER_INPUT
    
    ####################################################
    
    #
    ############Question U10.2############################################################
   ######### Population_size

    pop_size_policy = 205000 #USER_INPUT
    locals() ["pop_size" + Policy_label] = pop_size
    #######################

    #############################
    
    #######Question U10.xx#################################
    ##We are not reasking this question in the new current description of the tool
    
    #U_type = "average" #'average', 'town', 'city', 'rural'  #This is to select the demand vector - the user should choose

    #Extracting the correct demand vector

    #demand_KV_policy = locals() ["Y_" + U_type][country].copy()
    

    

################################################################################

    #################################################################
    
    
    ###########Question U 10.xx#########################################################
    #####We are not reasking this question in the new version of the tool
    
    #Income_scaler

    #Income_choice =  "3rd_household"###options are "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
                                ###1st household is the richest.

    #Otherwise,  the user selects the income level of the household (they choose by quntiles)

    #Income_scaler = Income_scaling.loc[Income_choice,country] / Income_scaling.loc['Total_household',country] #USER_INPUT
    #Elasticity = 1 # Random number for now. It should be specific to country and product

    #if Income_choice == "3rd_household":
    #    Income_scaler = 1

    #demand_KV_policy *= Income_scaler * Elasticity
##############################################################################################



    

    

##############################################################


###########################################
#     NEW PART FOR THE CONSTRUCTION EMISSIONS!
#######################################################       
##Construction emissions#############################################################################################
        
##U 10.3#############################################
       
New_floor_area = 0   #USER_INPUT
        
#    END OF PART FOR THE CONSTRUCTION EMISSIONS!    
        
###############################################################################################################


###############################################################
#############The actual calculation starts here################
#################################################################


income_scaling = Income_proj.loc[country]    #Scale factor applied to income - unique value for each decade
house_scaling = House_proj.loc[country]      #Scale factor applied to household size - unique value for each decade

while year <= 2050:
    
    #check the policy part
    
    if year == 2020:
   
        income_mult = 1 #This is just for the year 2020
        house_mult = 1  #This is just for the year 2020
        eff_factor = 1  #This is just for the year 2020
    
    
###########Policies are from here################################################################
    if policy_label != "BL" and year == policy_year: #& policy_label != "BL":
        
        #demand_KV = demand_KV_policy
        #house_size_ab = house_size_ab_policy  #Because we are not asking these questions
        pop_size = pop_size_policy
        
        #Questions should be asked in this order! Some depend on the results of others
##############Household Efficiency###################################################

###########U11.1#################################
        EFF_gain = "FALSE" #USER_INPUT U11.1.0
        EFF_scaler = 0.5 #USER_INPUT   U11.1.1
        
        if EFF_gain == "TRUE":
            
            Eff_improvements(demand_KV, EFF_scaler)
            
########################################################################################################################

##############Local_Electricity########################################################################################
######################U11.2######################################
        Local_electricity = "FALSE" #USER_INPUT  U11.2.0
        EL_Type = 'Electricity by solar photovoltaic'#USER_INPUT U11.2.1  'Electricity by solar photovoltaic','Electricity by biomass and waste','Electricity by wind','Electricity by Geothermal'  
        EL_scaler = 0.5 #User_Input U11.2.2

        if Local_electricity == "TRUE":
            
            Local_generation(ab_M,demand_KV, EL_scaler, EL_Type)
        
#########################################################################################################################

##############Sustainable_Heating######################################################################################
    ############# U11.3#########################
    
    
        S_heating = "FALSE" #USER_INPUT   U11.3.0
        
        #district_prop = 0.25 #USER_INPUT  U11.3.1
        #electricity_heat_prop = 0.75 #USER_INPUT
        #combustable_fuels_prop = 0.25 #USER_INPUT
        
        #solids_prop = 0.0 #USER_INPUT   U11.3.2
        #gases_prop = 0.0 #USER_INPUT
        #liquids_prop = 0.0 #USER_INPUT
        
        
        #District_value = ab_M.loc[direct_ab,district].sum()# ab_M   0.0 # USER_INPUT  U11.3.3
        
        if S_heating == "TRUE":
            
            local_heating(ab_M, demand_KV, district_prop, electricity_heat_prop, 
                          combustable_fuels_prop, liquids_prop, gases_prop, solids_prop, District_value)
        
            #This is just a repeat of the baseline part
        
#########################################################################################################################

###########Biofuel_in_transport########################################################################################
    ########### U12.1##############   
    
        Biofuel_takeup = "FALSE" #USER_INPUT  U12.1.0
        bio_scaler = 0.5 #USER_INPUT      U12.1.1        
        if Biofuel_takeup == "TRUE":
            
            BioFuels(demand_KV, bio_scaler)

##########################################################################################################################

########Electric_Vehicles##################################################################################################
       ###### U12.2#############
    
        EV_takeup = "FALSE" #USER_INPUT  U12.2.0
        EV_scaler = 0.5     #User_Input U12.2.1
        
        if EV_takeup == "TRUE":
            
            Electric_Vehicles(demand_KV, EV_scaler)
        
############################################################################################################################

#########Modal_Shift#######################################################################################################
    #########U12.3#################    
    
        Modal_Shift = "FALSE" #USER_INPUT U12.3.0
        MS_fuel_scaler = 0.5 #USER_INPUT U12.3.1
        MS_veh_scaler = 0.5 #USER_INPUT U12.3.2
        MS_pt_scaler = 0.2  #USER_INPUT U12.3.3
        
        if Modal_Shift == "TRUE":
            
            Transport_Modal_Shift(demand_KV, MS_fuel_scaler, MS_pt_scaler, MS_veh_scaler)
        
###########################################################################################################################            
        
    if year > 2020 and year <= 2030:
                
        income_mult = income_scaling['2020-2030']   #Select the income multiplier for this decade
        house_mult = house_scaling['2020-2030']     #Select the house multiplier for this decade
        eff_factor = eff_scaling
        
    if  year > 2030 and year <= 2040: 
        
        income_mult = income_scaling['2030-2040']   #Seclectthe income multiplier for this decade
        house_mult = house_scaling['2030-2040']     #select the house multiplier for this decade
        eff_factor = eff_scaling
        
    if year > 2040 and year <=2050:
        
        income_mult = income_scaling['2040-2050']   #Seclectthe income multiplier for this decade
        house_mult = house_scaling['2040-2050']     #select the house multiplier for this decade
        eff_factor = eff_scaling
        
        
    demand_KV *= income_mult
        
    ab_M *=eff_factor
        
    Use_phase_ab *=eff_factor
        
    Tail_pipe_ab *=eff_factor
        
        
    #Then we have to recalculate
        
        
    GWP_ab = pd.DataFrame(ab_M.to_numpy().dot(np.diag(demand_KV.to_numpy()))) # This is the basic calculation

    GWP_ab.index = ['direct' , 'indirect']

    GWP_ab.columns = products

    Use_phase_ab_GWP = demand_KV * Use_phase_ab # This adds in the household heating fuel use

    Tail_pipe_ab_GWP = demand_KV * Tail_pipe_ab # This adds in the burning of fuel for cars

    Total_use_ab = Tail_pipe_ab_GWP.fillna(0) + Use_phase_ab_GWP.fillna(0) #This puts together in the same table (200 x 1)
                                                                           #all of the other 200 products are zero
    #Put together the IO and use phase

    GWP_ab.loc['Use phase',:] = Total_use_ab
        
        
    #GWP_EE_pc = GWP_EE/House_size_EE
        
    #print(year)
    
        
        
    #GWP_EE = GWP_EE * (eff_factor) * (income_mult)
        
    GWP_ab_pc = GWP_ab / (House_size_ab * house_mult)   
    
#Put the results into sectors  
    
    DF.loc[year] =IW_sectors_np_tr.dot(GWP_ab_pc.sum().to_numpy())
    DF_tot.loc[year] = GWP_ab_pc.sum()
    
    DF_area.loc[year] = IW_sectors_np_tr.dot(GWP_ab_pc.sum().to_numpy()) * pop_size
    
    
    
    year +=1
    
DF['Total_Emissions'] = DF.sum(axis = 1)
DF_area['Total_Emissions'] = DF_area.sum(axis =1)


###########################################################################################################
#New Construction Emissions part!
#################################################################################################################

if policy_label != "BL":
    if country in North:
    
        Building_Emissions = 350 * New_floor_area/pop_size
    
    if country in West:
    
        Building_Emissions = 520 * New_floor_area/pop_size

    if country in East:
    
        Building_Emissions = 580 * New_floor_area/pop_size

    DF.loc[policy_year, 'Total_Emissions'] += Building_Emissions

    DF_area.loc[policy_year,'Total_Emissions'] += Building_Emissions * pop_size


 
##############################################################################################################
#End of Construction Emissions part!
#############################################################################################################
##Adding total emissions by multiplying by population



#F_tot.columns = Exio_products
locals()[region + "_Emissions_" + policy_label] = DF
locals()[region+ "_Emissions_tot_" + policy_label] = DF_tot

locals ()[region + "_Area_Emissions_" + policy_label] = DF_area



# In[25]:


#Baseline calculation here - policies is essentially the same calcualtion
###########Explanation#######################
#The calculations work by describing the economy as being composed of 200 products, given by 'products'. 
#For each product there is an emission intensity and they are collected together in ab_M. There are seperate emission
#intensties for the 'direct production' and the 'indirect production' (rest of the supply chain). So ab_M is a 200 x 2
#table
#Some products that describe household fuel use for heat and also transport fuel use for cars have another emission 
#intesntiy as well. These are held in seperate tables 'use_phase' and 'tail_pipe' (all other products have 0 here)

#To calculate the Emissions, each value in ab_M + the values in use_phase and tail_pipe are multiplied by the amount
#the household spends on each of the 200 products. These are stored in another table caled demand_KV (demand vector)
#The emissions for each product from the direct production, indirect production, and use_phase/tail_pipe are summed 
#to get the total emissions for that product.

#Once we have the total emissions for each product for that year, they are grouped together into 'sectors' that describe different things.
#There are 7 in total: Household Energy, Household Other, transport fuels, transport other, air transport, food, 
#tangible goods and  services

#The calculations are performed every year until 2050, with the values of demand_KV and ab_M changing slighting each year.
#This is based on 3 factors, efficiency improvements, changes in income and changes in household size. There is also a 
#section where these projections can change as a result of different policies (for the baseline no policies are introduced)

##################################################################################################################
##################################################################################################################
#Determine Emissions for all years

########INcluded in the start screen##############################

################Question 9.0 starts here##################################
year = 2022


##########################################
region = "County_Meath" #User_input

###U9.1####################
policy_label = "P1"  #This is just a label for the policy. Or the tool has a way to select different policies.

###############################


#########U9.0#####################################
country = "Ireland"  #This is to choose the country - USER_INPUT
ab = "IE"            #This is to identify the country, should match above
####################################################################


############Question 9.0#################
#Population_size

pop_size = 195000 #USER_INPUT
locals() ["pop_size" + Policy_label] = pop_size   #Sorry! Don't know how to do this without using locals!

##################################################################################


#Additional questions for the baseline################################

#######Question U9.2#################################################
U_type = "average" #'average', 'town', 'city', 'rural'  #This is to select the demand vector - the user should choose

#Extracting the correct demand vector

demand_KV = locals() ["Y_" + U_type][country].copy()


#House_size U9.3


#We also extract the house_size from this###########
House_size_ab = House_size.loc['Average_size_'+ U_type, country] #This is the default
#House_size_ab = 2.14#xx###USER_INPUT
################################################################################

#################################################################

#################################################################

###########Question U 9.4###############################################################
#Income_scaler

Income_choice =  "3rd_household"###options are "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
                                ###1st household is the richest.

#Otherwise,  the user selects the income level of the household (they choose by quntiles)

Income_scaler = Income_scaling.loc[Income_choice,country] / Income_scaling.loc['Total_household',country] #USER_INPUT
Elasticity = 1 # Random number for now. It should be specific to country and product

#if Income_choice == "3rd_household":
#    Income_scaler = 1
    
    

demand_KV *= Income_scaler * Elasticity
##############################################################################################




######### Question U9.5########################################


#This is the expected global reduction in product emissions

#Suggestion - Just give the user one of three options, with the default being normal

fast = 0.07
normal = 0.03
slow = 0.01

eff_scaling = 1 - normal #USER_INPUT



##############################################################


#Forming data for the calculations

#These are needed for holding the results
DF = pd.DataFrame(np.zeros((30,8)),index = list(range(2020,2050))
                                                      , columns = IW_sectors.columns)  #Holds final data in sectors 7 (+ sum)

DF_tot = pd.DataFrame(np.zeros((30,200)),index = list(range(2020,2050))
                                                      ,columns = products) #holds final data in products (200)

DF_area = pd.DataFrame(np.zeros((30,8)),index = list(range(2020,2050))
                                                      , columns = IW_sectors.columns)  #Holds area emissions (multiplies by pop_size
                                                      
direct_ab = "direct_"+ab
indirect_ab = "indirect_"+ab
M_countries.loc[direct_ab:indirect_ab,:].copy()
                                                      
ab_M = locals() [ab + "_M"] = M_countries.loc[direct_ab:indirect_ab,:].copy()  #Here the emission intensities                                                 
                                                                               #are selected
                                                                        



#These are needed for the use phase emissions

Tail_pipe_ab = Tail_pipe[country].copy()

Use_phase_ab = Use_phase[country].copy()

#This is needed for calculating the amount of electricity coming from heating

ad = Adjustable_amounts[country].copy()

elec_price = Electricity_prices[country]["BP_2019_S2_Euro"] 


#Baseline Modifications go here  ##Possibly not included in this version of the tool###########




##############################################################



##This is the end of the mandatory questions


##Optional questions
#################################################################################################
#Here the user can modify the default values for the the demand. IF THEY DON'T WANT TO THEN SKIP THIS PART.


#########Question 8#############################################################################
    #Public Transport types

public_transport = ['Railway transportation services', 'Other land transportation services', 
                    'Sea and coastal water transportation services', 'Inland water transportation services']
    
    
Public_transport_sum = demand_KV[public_transport].sum()    ###This describes the total use of public transport
    
rail_prop = demand_KV['Railway transportation services'] / Public_transport_sum
bus_prop = demand_KV['Other land transportation services'] / Public_transport_sum
ferry_prop = demand_KV['Sea and coastal water transportation services'] / Public_transport_sum
river_prop = demand_KV['Inland water transportation services'] / Public_transport_sum
    
    
#These 'prop' values can be adjustable by the user. 
#For example, if the user thinks there should be no water based travel this can be set to 0
#but then the other values should be increased so that total proportions sum to equal to 1
    
#In such a case, the code to do this would be
    
#river_prop = 0#USER_INPUT (often 0)
#ferry_prop = 0#USER_INPUT (often 0)
#bus_prop = bus_prop / (bus_prop + rail_prop) #USER_INPUT - code maintains the ratio between bus and rail
#rail_prop = rail_prop / (bus_prop + rail_prop) #USER_INPUT - code maintains the ratio between bus and rail

#ferry_prop = ferry_prop / (bus_prop + ferry_prop+ rail_prop)

#The values that should be adjusted are:

demand_KV['Railway transportation services'] = rail_prop * Public_transport_sum
demand_KV['Other land transportation services'] = bus_prop * Public_transport_sum
demand_KV['Sea and coastal water transportation services'] = ferry_prop * Public_transport_sum
demand_KV['Inland water transportation services'] = river_prop * Public_transport_sum

##############################################################################
    
#Otherwise, if there is no rail travel or river/sea travel then it should be:

#rail_prop = 0
#river_prop = 0
#ferry_prop = 0
#bus_prop = 1
       
######################################################################################################


#########Question 9##################################################################################
    #Electricity _ mix
#IT SHOULD BE SUGGESTED TO LEAVE THE DEFAULT VALUES 
#As above, the user can specify if the electricity mix is different to the country average for the BL
    
electricity = ['Electricity by coal', 'Electricity by gas','Electricity by nuclear',
                      'Electricity by hydro', 'Electricity by wind','Electricity by petroleum and other oil derivatives',
                      'Electricity by biomass and waste', 'Electricity by solar photovoltaic',
                      'Electricity by solar thermal', 'Electricity by tide, wave, ocean',
                      'Electricity by Geothermal', 'Electricity nec'] 

#No electricity goes in 'electricity nec'. This is used for local electricity production
    
elec_total = demand_KV[electricity].sum()
    
#The code works the same as above the the public transport. 
    
#e.g.
    
#hydro_prop = 0.7
#solar_pvc_prop = 0.3
#coal_prop = 0
#gas_prop = 0
#nuclear_prop = 0
#wind_prop = 0
#petrol_prop = 0
#solar_thermal_prop = 0
#tide_prop = 0
#geo_prop = 0
#nec_prop = 0

#Then the total kWh is determined from these props
#demand_KV[electricity] = 0
    
#demand_KV['Electricity by solar photovoltaic'] = solar_pvc_prop * elec_total
#demand_KV['Electricity by hydro'] = hydro_prop * elec_total
    
    
#if the user specifies the mix, then the electricity values change to the LCA values:

#for elec in electricity:
        
    #ab_M.loc[direct_ab:indirect_ab,electricity] = M_countries_LCA.loc[direct_ab:indirect_ab,electricity] 

#IT SHOULD BE SUGGESTED THAT THE USER DOES NOT ALTER THE ELECTRICITY MIX
################################################################################################################

#######Question 10#####################################################################################
    
    
    #Supply of household heating

liquids = ['Natural Gas Liquids', 'Kerosene', 'Heavy Fuel Oil', 'Other Liquid Biofuels']
solids = ['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)',
                  'Coke Oven Coke']
gases = ['Distribution services of gaseous fuels through mains', 'Biogas']
        
district = 'Steam and hot water supply services'
        
electricity_heat = (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"]) * elec_total * elec_price
        
Total_Fuel = demand_KV[solids].sum() + demand_KV[liquids].sum() + demand_KV[gases].sum() + demand_KV[district].sum() + electricity_heat

#We assume all 'fuels' are the same efficiency (obviously wrong, but no time to fix)
        
#########################
#PART 1 - The user selects the heating proportions from district heating, electricity and household combustion
#########################


#Default values are given by:
district_prop = demand_KV[district] / Total_Fuel

electricity_heat_prop = electricity_heat / Total_Fuel

combustable_fuels_prop = (demand_KV[solids].sum() + demand_KV[liquids].sum() + demand_KV[gases].sum()) / Total_Fuel

###THE USER CAN ALTER THESE BY::

#THESE NUMBERS NEED TO SUM TO 1
#district_prop = 0.0#district_prop#1##USER_INPUT
#electricity_heat_prop = 1.0#electricity_heat_prop##USER_INPUT
#combustable_fuels_prop = 0.0#combustable_fuels_prop##USER_INPUT

######################################
##Part 2 - Determine final values
######################################

#Then, the final values are given by:

#DISTRICT HEATING
demand_KV[district] = Total_Fuel * district_prop


#ELECTRICITY
for elec in electricity:
    
    prop = demand_KV[elec] / elec_total #determine amount of each electricity source in total electricity mix.
    elec_hold = (1 - (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"])) * demand_KV[elec] #electricity for appliances
    demand_KV[elec] = prop * electricity_heat_prop * Total_Fuel / elec_price #Scale based on electricity use in heat and elec mix
    demand_KV[elec] += elec_hold #Add on the parts to do with appliances
    
        
#COMBUSTABLE FUELS

#Here, the user can also alter the mix of the combustable fuels.

liquids_prop = demand_KV[liquids].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())
solids_prop = demand_KV[solids].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())
gases_prop = demand_KV[gases].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())

#THE USER CAN CHANGE THESE VALUES BUT THE SUM MUST BE EQUAL TO 1!

############Question 10.1######################
#liquids_prop = 0 # #USER INPUT
#solids_prop = 0 ##USER_INPUT
#gases_prop = 1 # #USER_INPUT


#Then

for liquid in liquids:
    
    if demand_KV[liquids].sum() != 0:
        
        prop = demand_KV[liquid] / demand_KV[liquids].sum()  #Amount of each liquid in total liquid expenditure
        demand_KV[liquid] = prop * liquids_prop * combustable_fuels_prop * Total_Fuel
    else:
        
        demand_KV['Kerosene'] = liquids_prop * combustable_fuels_prop * Total_Fuel
        

        
for solid in solids:
    
    if demand_KV[solids].sum() != 0:
        prop = demand_KV[solid] / demand_KV[solids].sum()  #Amount of each solid in total solid expenditure
        demand_KV[solid] = prop * solids_prop * combustable_fuels_prop * Total_Fuel
    
    else:
        demand_KV['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)'] = solids_prop * combustable_fuels_prop * Total_Fuel

        
for gas in gases:
    
    if demand_KV[gases].sum() != 0:
        prop = demand_KV[gas] / demand_KV[gases].sum()  #Amount of each gas in total gas expenditure
        demand_KV[gas] = prop * gases_prop * combustable_fuels_prop * Total_Fuel

    else:
        demand_KV['Distribution services of gaseous fuels through mains'] = gases_prop * combustable_fuels_prop * Total_Fuel

######QUESTION 11###########################################
    #The 'direct_ab' value should be changed to the value the user wants. 
    #The user needs to convert the value into kg CO2e / Euro 
direct_district_emissions = ab_M.loc[direct_ab,district]#1.0475#USER_INPUT
ab_M.loc[direct_ab,district] = direct_district_emissions
################################################################

###This is the end of the additional baseline questions################################################
######################################################################

##Basic policy questions go here######################################

###Here, we are essentially just asking the questions we asked for the BL again. The problem is that before the 
##policy year (in this case 2025), the values should be equal to the baseline. So I have just redefined the variables
##here. But for the tool if all variables are predefined and then sent to a funciton to run the calculation, would they 
## need to be new variables?



if policy_label != "BL":   #Not sure if I need. Maybe can just set the policy year to 2050 as default
    
    ####################User enters the policy year U10.1
    policy_year = 2025#USER_INPUT
    
    ####################################################
    
    #
    ############Question U10.2############################################################
   ######### Population_size

    pop_size_policy = 205000 #USER_INPUT
    locals() ["pop_size" + Policy_label] = pop_size
    #######################

    #############################
    
    #######Question U10.xx#################################
    ##We are not reasking this question in the new current description of the tool
    
    #U_type = "average" #'average', 'town', 'city', 'rural'  #This is to select the demand vector - the user should choose

    #Extracting the correct demand vector

    #demand_KV_policy = locals() ["Y_" + U_type][country].copy()
    

    

################################################################################

    #################################################################
    
    
    ###########Question U 10.xx#########################################################
    #####We are not reasking this question in the new version of the tool
    
    #Income_scaler

    #Income_choice =  "3rd_household"###options are "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
                                ###1st household is the richest.

    #Otherwise,  the user selects the income level of the household (they choose by quntiles)

    #Income_scaler = Income_scaling.loc[Income_choice,country] / Income_scaling.loc['Total_household',country] #USER_INPUT
    #Elasticity = 1 # Random number for now. It should be specific to country and product

    #if Income_choice == "3rd_household":
    #    Income_scaler = 1

    #demand_KV_policy *= Income_scaler * Elasticity
##############################################################################################



    

    

##############################################################


        ###########################################
#     NEW PART FOR THE CONSTRUCTION EMISSIONS!
#######################################################       
##Construction emissions#############################################################################################
        
##U 10.3#############################################
       
New_floor_area = 500000   #USER_INPUT
        
#    END OF PART FOR THE CONSTRUCTION EMISSIONS!    
        
###############################################################################################################


###############################################################
#############The actual calculation starts here################
#################################################################


income_scaling = Income_proj.loc[country]    #Scale factor applied to income - unique value for each decade
house_scaling = House_proj.loc[country]      #Scale factor applied to household size - unique value for each decade

while year <= 2050:
    
    #check the policy part
    
    if year == 2020:
   
        income_mult = 1 #This is just for the year 2020
        house_mult = 1  #This is just for the year 2020
        eff_factor = 1  #This is just for the year 2020
    
    
###########Policies are from here################################################################
    if policy_label != "BL" and year == policy_year: #& policy_label != "BL":
        
        #demand_KV = demand_KV_policy
        #house_size_ab = house_size_ab_policy  #Because we are not asking these questions
        pop_size = pop_size_policy
        
        #Questions should be asked in this order! Some depend on the results of others
##############Household Efficiency###################################################

###########U11.1#################################
        EFF_gain = "TRUE" #USER_INPUT U11.1.0
        EFF_scaler = 0.1 #USER_INPUT   U11.1.1
        
        if EFF_gain == "TRUE":
            
            Eff_improvements(demand_KV, EFF_scaler)
            
########################################################################################################################

##############Local_Electricity########################################################################################
######################U11.2######################################
        Local_electricity = "TRUE" #USER_INPUT  U11.2.0
        EL_Type = 'Electricity by solar photovoltaic'#USER_INPUT U11.2.1  'Electricity by solar photovoltaic','Electricity by biomass and waste','Electricity by wind','Electricity by Geothermal'  
        EL_scaler = 0.05 #User_Input U11.2.2

        if Local_electricity == "TRUE":
            
            Local_generation(ab_M,demand_KV, EL_scaler, EL_Type)
        
#########################################################################################################################

##############Sustainable_Heating######################################################################################
    ############# U11.3#########################
    
    
        S_heating = "FALSE" #USER_INPUT   U11.3.0
        
        #district_prop = 0.25 #USER_INPUT  U11.3.1
        #electricity_heat_prop = 0.75 #USER_INPUT
        #combustable_fuels_prop = 0.25 #USER_INPUT
        
        #solids_prop = 0.0 #USER_INPUT   U11.3.2
        #gases_prop = 0.0 #USER_INPUT
        #liquids_prop = 0.0 #USER_INPUT
        
        
        #District_value = ab_M.loc[direct_ab,district].sum()# ab_M   0.0 # USER_INPUT  U11.3.3
        
        if S_heating == "TRUE":
            
            local_heating(ab_M, demand_KV, district_prop, electricity_heat_prop, 
                          combustable_fuels_prop, liquids_prop, gases_prop, solids_prop, District_value)
        
            #This is just a repeat of the baseline part
        
#########################################################################################################################

###########Biofuel_in_transport########################################################################################
    ########### U12.1##############   
    
        Biofuel_takeup = "FALSE" #USER_INPUT  U12.1.0
        bio_scaler = 0.5 #USER_INPUT      U12.1.1        
        if Biofuel_takeup == "TRUE":
            
            BioFuels(demand_KV, bio_scaler)

##########################################################################################################################

########Electric_Vehicles##################################################################################################
       ###### U12.2#############
    
        EV_takeup = "FALSE" #USER_INPUT  U12.2.0
        EV_scaler = 0.5     #User_Input U12.2.1
        
        if EV_takeup == "TRUE":
            
            Electric_Vehicles(demand_KV, EV_scaler)
        
############################################################################################################################

#########Modal_Shift#######################################################################################################
    #########U12.3#################    
    
        Modal_Shift = "TRUE" #USER_INPUT U12.3.0
        MS_fuel_scaler = 0.04 #USER_INPUT U12.3.1
        MS_veh_scaler = 0.04 #USER_INPUT U12.3.2
        MS_pt_scaler = -0.04  #USER_INPUT U12.3.3
        
        if Modal_Shift == "TRUE":
            
            Transport_Modal_Shift(demand_KV, MS_fuel_scaler, MS_pt_scaler, MS_veh_scaler)
        
###########################################################################################################################            
        
    if year > 2020 and year <= 2030:
                
        income_mult = income_scaling['2020-2030']   #Select the income multiplier for this decade
        house_mult = house_scaling['2020-2030']     #Select the house multiplier for this decade
        eff_factor = eff_scaling
        
    if  year > 2030 and year <= 2040: 
        
        income_mult = income_scaling['2030-2040']   #Seclectthe income multiplier for this decade
        house_mult = house_scaling['2030-2040']     #select the house multiplier for this decade
        eff_factor = eff_scaling
        
    if year > 2040 and year <=2050:
        
        income_mult = income_scaling['2040-2050']   #Seclectthe income multiplier for this decade
        house_mult = house_scaling['2040-2050']     #select the house multiplier for this decade
        eff_factor = eff_scaling
        
        
    demand_KV *= income_mult
        
    ab_M *=eff_factor
        
    Use_phase_ab *=eff_factor
        
    Tail_pipe_ab *=eff_factor
        
        
    #Then we have to recalculate
        
        
    GWP_ab = pd.DataFrame(ab_M.to_numpy().dot(np.diag(demand_KV.to_numpy()))) # This is the basic calculation

    GWP_ab.index = ['direct' , 'indirect']

    GWP_ab.columns = products

    Use_phase_ab_GWP = demand_KV * Use_phase_ab # This adds in the household heating fuel use

    Tail_pipe_ab_GWP = demand_KV * Tail_pipe_ab # This adds in the burning of fuel for cars

    Total_use_ab = Tail_pipe_ab_GWP.fillna(0) + Use_phase_ab_GWP.fillna(0) #This puts together in the same table (200 x 1)
                                                                           #all of the other 200 products are zero
    #Put together the IO and use phase

    GWP_ab.loc['Use phase',:] = Total_use_ab
        
        
    #GWP_EE_pc = GWP_EE/House_size_EE
        
    #print(year)
    
        
        
    #GWP_EE = GWP_EE * (eff_factor) * (income_mult)
        
    GWP_ab_pc = GWP_ab / (House_size_ab * house_mult)   
    
#Put the results into sectors  
    
    DF.loc[year] =IW_sectors_np_tr.dot(GWP_ab_pc.sum().to_numpy())
    DF_tot.loc[year] = GWP_ab_pc.sum()
    
    DF_area.loc[year] = IW_sectors_np_tr.dot(GWP_ab_pc.sum().to_numpy()) * pop_size
    
    
    
    year +=1
    
DF['Total_Emissions'] = DF.sum(axis = 1)
DF_area['Total_Emissions'] = DF_area.sum(axis =1)


###########################################################################################################
#New Construction Emissions part!
#################################################################################################################

if policy_label != "BL":
    if country in North:
    
        Building_Emissions = 350 * New_floor_area/pop_size
    
    if country in West:
    
        Building_Emissions = 520 * New_floor_area/pop_size

    if country in East:
    
        Building_Emissions = 580 * New_floor_area/pop_size

    DF.loc[policy_year, 'Total_Emissions'] += Building_Emissions

    DF_area.loc[policy_year,'Total_Emissions'] += Building_Emissions * pop_size


 
##############################################################################################################
#End of Construction Emissions part!
#############################################################################################################
##Adding total emissions by multiplying by population



#F_tot.columns = Exio_products
locals()[region + "_Emissions_" + policy_label] = DF
locals()[region+ "_Emissions_tot_" + policy_label] = DF_tot

locals ()[region + "_Area_Emissions_" + policy_label] = DF_area



# In[26]:


#Baseline calculation here - policies is essentially the same calcualtion
###########Explanation#######################
#The calculations work by describing the economy as being composed of 200 products, given by 'products'. 
#For each product there is an emission intensity and they are collected together in ab_M. There are seperate emission
#intensties for the 'direct production' and the 'indirect production' (rest of the supply chain). So ab_M is a 200 x 2
#table
#Some products that describe household fuel use for heat and also transport fuel use for cars have another emission 
#intesntiy as well. These are held in seperate tables 'use_phase' and 'tail_pipe' (all other products have 0 here)

#To calculate the Emissions, each value in ab_M + the values in use_phase and tail_pipe are multiplied by the amount
#the household spends on each of the 200 products. These are stored in another table caled demand_KV (demand vector)
#The emissions for each product from the direct production, indirect production, and use_phase/tail_pipe are summed 
#to get the total emissions for that product.

#Once we have the total emissions for each product for that year, they are grouped together into 'sectors' that describe different things.
#There are 7 in total: Household Energy, Household Other, transport fuels, transport other, air transport, food, 
#tangible goods and  services

#The calculations are performed every year until 2050, with the values of demand_KV and ab_M changing slighting each year.
#This is based on 3 factors, efficiency improvements, changes in income and changes in household size. There is also a 
#section where these projections can change as a result of different policies (for the baseline no policies are introduced)

##################################################################################################################
##################################################################################################################
#Determine Emissions for all years

########INcluded in the start screen##############################

################Question 9.0 starts here##################################
year = 2025


##########################################
region = "County_Meath" #User_input

###U9.1####################
policy_label = "P4"  #This is just a label for the policy. Or the tool has a way to select different policies.

###############################


#########U9.0#####################################
country = "Ireland"  #This is to choose the country - USER_INPUT
ab = "IE"            #This is to identify the country, should match above
####################################################################


############Question 9.0#################
#Population_size

pop_size = 10000 #USER_INPUT
locals() ["pop_size" + Policy_label] = pop_size   #Sorry! Don't know how to do this without using locals!

##################################################################################


#Additional questions for the baseline################################

#######Question U9.2#################################################
U_type = "city" #'average', 'town', 'city', 'rural'  #This is to select the demand vector - the user should choose

#Extracting the correct demand vector

demand_KV = locals() ["Y_" + U_type][country].copy()


#House_size U9.3


#We also extract the house_size from this###########
House_size_ab = House_size.loc['Average_size_'+ U_type, country] #This is the default
#House_size_ab = 2.14#xx###USER_INPUT
################################################################################

#################################################################

#################################################################

###########Question U 9.4###############################################################
#Income_scaler

Income_choice =  "4th_household"###options are "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
                                ###1st household is the richest.

#Otherwise,  the user selects the income level of the household (they choose by quntiles)

Income_scaler = Income_scaling.loc[Income_choice,country] / Income_scaling.loc['Total_household',country] #USER_INPUT
Elasticity = 1 # Random number for now. It should be specific to country and product

#if Income_choice == "3rd_household":
#    Income_scaler = 1
    
    

demand_KV *= Income_scaler * Elasticity
##############################################################################################




######### Question U9.5########################################


#This is the expected global reduction in product emissions

#Suggestion - Just give the user one of three options, with the default being normal

fast = 0.07
normal = 0.03
slow = 0.01

eff_scaling = 1 - normal #USER_INPUT



##############################################################


#Forming data for the calculations

#These are needed for holding the results
DF = pd.DataFrame(np.zeros((30,8)),index = list(range(2020,2050))
                                                      , columns = IW_sectors.columns)  #Holds final data in sectors 7 (+ sum)

DF_tot = pd.DataFrame(np.zeros((30,200)),index = list(range(2020,2050))
                                                      ,columns = products) #holds final data in products (200)

DF_area = pd.DataFrame(np.zeros((30,8)),index = list(range(2020,2050))
                                                      , columns = IW_sectors.columns)  #Holds area emissions (multiplies by pop_size
                                                      
direct_ab = "direct_"+ab
indirect_ab = "indirect_"+ab
M_countries.loc[direct_ab:indirect_ab,:].copy()
                                                      
ab_M = locals() [ab + "_M"] = M_countries.loc[direct_ab:indirect_ab,:].copy()  #Here the emission intensities                                                 
                                                                               #are selected
                                                                        



#These are needed for the use phase emissions

Tail_pipe_ab = Tail_pipe[country].copy()

Use_phase_ab = Use_phase[country].copy()

#This is needed for calculating the amount of electricity coming from heating

ad = Adjustable_amounts[country].copy()

elec_price = Electricity_prices[country]["BP_2019_S2_Euro"] 


#Baseline Modifications go here  ##Possibly not included in this version of the tool###########




##############################################################



##This is the end of the mandatory questions


##Optional questions
#################################################################################################
#Here the user can modify the default values for the the demand. IF THEY DON'T WANT TO THEN SKIP THIS PART.


#########Question 8#############################################################################
    #Public Transport types

public_transport = ['Railway transportation services', 'Other land transportation services', 
                    'Sea and coastal water transportation services', 'Inland water transportation services']
    
    
Public_transport_sum = demand_KV[public_transport].sum()    ###This describes the total use of public transport
    
rail_prop = demand_KV['Railway transportation services'] / Public_transport_sum
bus_prop = demand_KV['Other land transportation services'] / Public_transport_sum
ferry_prop = demand_KV['Sea and coastal water transportation services'] / Public_transport_sum
river_prop = demand_KV['Inland water transportation services'] / Public_transport_sum
    
    
#These 'prop' values can be adjustable by the user. 
#For example, if the user thinks there should be no water based travel this can be set to 0
#but then the other values should be increased so that total proportions sum to equal to 1
    
#In such a case, the code to do this would be
    
#river_prop = 0#USER_INPUT (often 0)
#ferry_prop = 0#USER_INPUT (often 0)
#bus_prop = bus_prop / (bus_prop + rail_prop) #USER_INPUT - code maintains the ratio between bus and rail
#rail_prop = rail_prop / (bus_prop + rail_prop) #USER_INPUT - code maintains the ratio between bus and rail

#ferry_prop = ferry_prop / (bus_prop + ferry_prop+ rail_prop)

#The values that should be adjusted are:

demand_KV['Railway transportation services'] = rail_prop * Public_transport_sum
demand_KV['Other land transportation services'] = bus_prop * Public_transport_sum
demand_KV['Sea and coastal water transportation services'] = ferry_prop * Public_transport_sum
demand_KV['Inland water transportation services'] = river_prop * Public_transport_sum

##############################################################################
    
#Otherwise, if there is no rail travel or river/sea travel then it should be:

#rail_prop = 0
#river_prop = 0
#ferry_prop = 0
#bus_prop = 1
       
######################################################################################################


#########Question 9##################################################################################
    #Electricity _ mix
#IT SHOULD BE SUGGESTED TO LEAVE THE DEFAULT VALUES 
#As above, the user can specify if the electricity mix is different to the country average for the BL
    
electricity = ['Electricity by coal', 'Electricity by gas','Electricity by nuclear',
                      'Electricity by hydro', 'Electricity by wind','Electricity by petroleum and other oil derivatives',
                      'Electricity by biomass and waste', 'Electricity by solar photovoltaic',
                      'Electricity by solar thermal', 'Electricity by tide, wave, ocean',
                      'Electricity by Geothermal', 'Electricity nec'] 

#No electricity goes in 'electricity nec'. This is used for local electricity production
    
elec_total = demand_KV[electricity].sum()
    
#The code works the same as above the the public transport. 
    
#e.g.
    
#hydro_prop = 0.7
#solar_pvc_prop = 0.3
#coal_prop = 0
#gas_prop = 0
#nuclear_prop = 0
#wind_prop = 0
#petrol_prop = 0
#solar_thermal_prop = 0
#tide_prop = 0
#geo_prop = 0
#nec_prop = 0

#Then the total kWh is determined from these props
#demand_KV[electricity] = 0
    
#demand_KV['Electricity by solar photovoltaic'] = solar_pvc_prop * elec_total
#demand_KV['Electricity by hydro'] = hydro_prop * elec_total
    
    
#if the user specifies the mix, then the electricity values change to the LCA values:

#for elec in electricity:
        
    #ab_M.loc[direct_ab:indirect_ab,electricity] = M_countries_LCA.loc[direct_ab:indirect_ab,electricity] 

#IT SHOULD BE SUGGESTED THAT THE USER DOES NOT ALTER THE ELECTRICITY MIX
################################################################################################################

#######Question 10#####################################################################################
    
    
    #Supply of household heating

liquids = ['Natural Gas Liquids', 'Kerosene', 'Heavy Fuel Oil', 'Other Liquid Biofuels']
solids = ['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)',
                  'Coke Oven Coke']
gases = ['Distribution services of gaseous fuels through mains', 'Biogas']
        
district = 'Steam and hot water supply services'
        
electricity_heat = (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"]) * elec_total * elec_price
        
Total_Fuel = demand_KV[solids].sum() + demand_KV[liquids].sum() + demand_KV[gases].sum() + demand_KV[district].sum() + electricity_heat

#We assume all 'fuels' are the same efficiency (obviously wrong, but no time to fix)
        
#########################
#PART 1 - The user selects the heating proportions from district heating, electricity and household combustion
#########################


#Default values are given by:
district_prop = demand_KV[district] / Total_Fuel

electricity_heat_prop = electricity_heat / Total_Fuel

combustable_fuels_prop = (demand_KV[solids].sum() + demand_KV[liquids].sum() + demand_KV[gases].sum()) / Total_Fuel

###THE USER CAN ALTER THESE BY::

#THESE NUMBERS NEED TO SUM TO 1
#district_prop = 0.0#district_prop#1##USER_INPUT
#electricity_heat_prop = 1.0#electricity_heat_prop##USER_INPUT
#combustable_fuels_prop = 0.0#combustable_fuels_prop##USER_INPUT

######################################
##Part 2 - Determine final values
######################################

#Then, the final values are given by:

#DISTRICT HEATING
demand_KV[district] = Total_Fuel * district_prop


#ELECTRICITY
for elec in electricity:
    
    prop = demand_KV[elec] / elec_total #determine amount of each electricity source in total electricity mix.
    elec_hold = (1 - (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"])) * demand_KV[elec] #electricity for appliances
    demand_KV[elec] = prop * electricity_heat_prop * Total_Fuel / elec_price #Scale based on electricity use in heat and elec mix
    demand_KV[elec] += elec_hold #Add on the parts to do with appliances
    
        
#COMBUSTABLE FUELS

#Here, the user can also alter the mix of the combustable fuels.

liquids_prop = demand_KV[liquids].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())
solids_prop = demand_KV[solids].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())
gases_prop = demand_KV[gases].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())

#THE USER CAN CHANGE THESE VALUES BUT THE SUM MUST BE EQUAL TO 1!

############Question 10.1######################
#liquids_prop = 0 # #USER INPUT
#solids_prop = 0 ##USER_INPUT
#gases_prop = 1 # #USER_INPUT


#Then

for liquid in liquids:
    
    if demand_KV[liquids].sum() != 0:
        
        prop = demand_KV[liquid] / demand_KV[liquids].sum()  #Amount of each liquid in total liquid expenditure
        demand_KV[liquid] = prop * liquids_prop * combustable_fuels_prop * Total_Fuel
    else:
        
        demand_KV['Kerosene'] = liquids_prop * combustable_fuels_prop * Total_Fuel
        

        
for solid in solids:
    
    if demand_KV[solids].sum() != 0:
        prop = demand_KV[solid] / demand_KV[solids].sum()  #Amount of each solid in total solid expenditure
        demand_KV[solid] = prop * solids_prop * combustable_fuels_prop * Total_Fuel
    
    else:
        demand_KV['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)'] = solids_prop * combustable_fuels_prop * Total_Fuel

        
for gas in gases:
    
    if demand_KV[gases].sum() != 0:
        prop = demand_KV[gas] / demand_KV[gases].sum()  #Amount of each gas in total gas expenditure
        demand_KV[gas] = prop * gases_prop * combustable_fuels_prop * Total_Fuel

    else:
        demand_KV['Distribution services of gaseous fuels through mains'] = gases_prop * combustable_fuels_prop * Total_Fuel

######QUESTION 11###########################################
    #The 'direct_ab' value should be changed to the value the user wants. 
    #The user needs to convert the value into kg CO2e / Euro 
direct_district_emissions = ab_M.loc[direct_ab,district]#1.0475#USER_INPUT
ab_M.loc[direct_ab,district] = direct_district_emissions
################################################################

###This is the end of the additional baseline questions################################################
######################################################################

##Basic policy questions go here######################################

###Here, we are essentially just asking the questions we asked for the BL again. The problem is that before the 
##policy year (in this case 2025), the values should be equal to the baseline. So I have just redefined the variables
##here. But for the tool if all variables are predefined and then sent to a funciton to run the calculation, would they 
## need to be new variables?



if policy_label != "BL":   #Not sure if I need. Maybe can just set the policy year to 2050 as default
    
    ####################User enters the policy year U10.1
    policy_year = 2025#USER_INPUT
    
    ####################################################
    
    #
    ############Question U10.2############################################################
   ######### Population_size

    pop_size_policy = 10000 #USER_INPUT
    locals() ["pop_size" + Policy_label] = pop_size
    #######################

    #############################
    
    #######Question U10.xx#################################
    ##We are not reasking this question in the new current description of the tool
    
    #U_type = "average" #'average', 'town', 'city', 'rural'  #This is to select the demand vector - the user should choose

    #Extracting the correct demand vector

    #demand_KV_policy = locals() ["Y_" + U_type][country].copy()
    

    

################################################################################

    #################################################################
    
    
    ###########Question U 10.xx#########################################################
    #####We are not reasking this question in the new version of the tool
    
    #Income_scaler

    #Income_choice =  "3rd_household"###options are "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
                                ###1st household is the richest.

    #Otherwise,  the user selects the income level of the household (they choose by quntiles)

    #Income_scaler = Income_scaling.loc[Income_choice,country] / Income_scaling.loc['Total_household',country] #USER_INPUT
    #Elasticity = 1 # Random number for now. It should be specific to country and product

    #if Income_choice == "3rd_household":
    #    Income_scaler = 1

    #demand_KV_policy *= Income_scaler * Elasticity
##############################################################################################



    

    

##############################################################


        ###########################################
#     NEW PART FOR THE CONSTRUCTION EMISSIONS!
#######################################################       
##Construction emissions#############################################################################################
        
##U 10.3#############################################
       
New_floor_area = 500000   #USER_INPUT
        
#    END OF PART FOR THE CONSTRUCTION EMISSIONS!    
        
###############################################################################################################


###############################################################
#############The actual calculation starts here################
#################################################################


income_scaling = Income_proj.loc[country]    #Scale factor applied to income - unique value for each decade
house_scaling = House_proj.loc[country]      #Scale factor applied to household size - unique value for each decade

while year <= 2050:
    
    #check the policy part
    
    if year == 2020:
   
        income_mult = 1 #This is just for the year 2020
        house_mult = 1  #This is just for the year 2020
        eff_factor = 1  #This is just for the year 2020
    
    
###########Policies are from here################################################################
    if policy_label != "BL" and year == policy_year: #& policy_label != "BL":
        
        #demand_KV = demand_KV_policy
        #house_size_ab = house_size_ab_policy  #Because we are not asking these questions
        pop_size = pop_size_policy
        
        #Questions should be asked in this order! Some depend on the results of others
##############Household Efficiency###################################################

###########U11.1#################################
        EFF_gain = "TRUE" #USER_INPUT U11.1.0
        EFF_scaler = 0.5 #USER_INPUT   U11.1.1
        
        if EFF_gain == "TRUE":
            
            Eff_improvements(demand_KV, EFF_scaler)
            
########################################################################################################################

##############Local_Electricity########################################################################################
######################U11.2######################################
        Local_electricity = "TRUE" #USER_INPUT  U11.2.0
        EL_Type = 'Electricity by solar photovoltaic'#USER_INPUT U11.2.1  'Electricity by solar photovoltaic','Electricity by biomass and waste','Electricity by wind','Electricity by Geothermal'  
        EL_scaler = 0.5 #User_Input U11.2.2

        if Local_electricity == "TRUE":
            
            Local_generation(ab_M,demand_KV, EL_scaler, EL_Type)
        
#########################################################################################################################

##############Sustainable_Heating######################################################################################
    ############# U11.3#########################
    
    
        S_heating = "FALSE" #USER_INPUT   U11.3.0
        
        #district_prop = 0.25 #USER_INPUT  U11.3.1
        #electricity_heat_prop = 0.75 #USER_INPUT
        #combustable_fuels_prop = 0.25 #USER_INPUT
        
        #solids_prop = 0.0 #USER_INPUT   U11.3.2
        #gases_prop = 0.0 #USER_INPUT
        #liquids_prop = 0.0 #USER_INPUT
        
        
        #District_value = ab_M.loc[direct_ab,district].sum()# ab_M   0.0 # USER_INPUT  U11.3.3
        
        if S_heating == "TRUE":
            
            local_heating(ab_M, demand_KV, district_prop, electricity_heat_prop, 
                          combustable_fuels_prop, liquids_prop, gases_prop, solids_prop, District_value)
        
            #This is just a repeat of the baseline part
        
#########################################################################################################################

###########Biofuel_in_transport########################################################################################
    ########### U12.1##############   
    
        Biofuel_takeup = "FALSE" #USER_INPUT  U12.1.0
        bio_scaler = 0.5 #USER_INPUT      U12.1.1        
        if Biofuel_takeup == "TRUE":
            
            BioFuels(demand_KV, bio_scaler)

##########################################################################################################################

########Electric_Vehicles##################################################################################################
       ###### U12.2#############
    
        EV_takeup = "FALSE" #USER_INPUT  U12.2.0
        EV_scaler = 0.5     #User_Input U12.2.1
        
        if EV_takeup == "TRUE":
            
            Electric_Vehicles(demand_KV, EV_scaler)
        
############################################################################################################################

#########Modal_Shift#######################################################################################################
    #########U12.3#################    
    
        Modal_Shift = "TRUE" #USER_INPUT U12.3.0
        MS_fuel_scaler = 0.04 #USER_INPUT U12.3.1
        MS_veh_scaler = 0.04 #USER_INPUT U12.3.2
        MS_pt_scaler = -0.04  #USER_INPUT U12.3.3
        
        if Modal_Shift == "TRUE":
            
            Transport_Modal_Shift(demand_KV, MS_fuel_scaler, MS_pt_scaler, MS_veh_scaler)
        
###########################################################################################################################            
        
    if year > 2020 and year <= 2030:
                
        income_mult = income_scaling['2020-2030']   #Select the income multiplier for this decade
        house_mult = house_scaling['2020-2030']     #Select the house multiplier for this decade
        eff_factor = eff_scaling
        
    if  year > 2030 and year <= 2040: 
        
        income_mult = income_scaling['2030-2040']   #Seclectthe income multiplier for this decade
        house_mult = house_scaling['2030-2040']     #select the house multiplier for this decade
        eff_factor = eff_scaling
        
    if year > 2040 and year <=2050:
        
        income_mult = income_scaling['2040-2050']   #Seclectthe income multiplier for this decade
        house_mult = house_scaling['2040-2050']     #select the house multiplier for this decade
        eff_factor = eff_scaling
        
        
    demand_KV *= income_mult
        
    ab_M *=eff_factor
        
    Use_phase_ab *=eff_factor
        
    Tail_pipe_ab *=eff_factor
        
        
    #Then we have to recalculate
        
        
    GWP_ab = pd.DataFrame(ab_M.to_numpy().dot(np.diag(demand_KV.to_numpy()))) # This is the basic calculation

    GWP_ab.index = ['direct' , 'indirect']

    GWP_ab.columns = products

    Use_phase_ab_GWP = demand_KV * Use_phase_ab # This adds in the household heating fuel use

    Tail_pipe_ab_GWP = demand_KV * Tail_pipe_ab # This adds in the burning of fuel for cars

    Total_use_ab = Tail_pipe_ab_GWP.fillna(0) + Use_phase_ab_GWP.fillna(0) #This puts together in the same table (200 x 1)
                                                                           #all of the other 200 products are zero
    #Put together the IO and use phase

    GWP_ab.loc['Use phase',:] = Total_use_ab
        
        
    #GWP_EE_pc = GWP_EE/House_size_EE
        
    #print(year)
    
        
        
    #GWP_EE = GWP_EE * (eff_factor) * (income_mult)
        
    GWP_ab_pc = GWP_ab / (House_size_ab * house_mult)   
    
#Put the results into sectors  
    
    DF.loc[year] =IW_sectors_np_tr.dot(GWP_ab_pc.sum().to_numpy())
    DF_tot.loc[year] = GWP_ab_pc.sum()
    
    DF_area.loc[year] = IW_sectors_np_tr.dot(GWP_ab_pc.sum().to_numpy()) * pop_size
    
    
    
    year +=1
    
DF['Total_Emissions'] = DF.sum(axis = 1)
DF_area['Total_Emissions'] = DF_area.sum(axis =1)


###########################################################################################################
#New Construction Emissions part!
#################################################################################################################

if policy_label != "BL":
    if country in North:
    
        Building_Emissions = 350 * New_floor_area/pop_size
    
    if country in West:
    
        Building_Emissions = 520 * New_floor_area/pop_size

    if country in East:
    
        Building_Emissions = 580 * New_floor_area/pop_size

    DF.loc[policy_year, 'Total_Emissions'] += Building_Emissions

    DF_area.loc[policy_year,'Total_Emissions'] += Building_Emissions * pop_size


 
##############################################################################################################
#End of Construction Emissions part!
#############################################################################################################
##Adding total emissions by multiplying by population



#F_tot.columns = Exio_products
locals()[region + "_Emissions_" + policy_label] = DF
locals()[region+ "_Emissions_tot_" + policy_label] = DF_tot

locals ()[region + "_Area_Emissions_" + policy_label] = DF_area


# In[27]:


#Baseline calculation here - policies is essentially the same calcualtion
###########Explanation#######################
#The calculations work by describing the economy as being composed of 200 products, given by 'products'. 
#For each product there is an emission intensity and they are collected together in ab_M. There are seperate emission
#intensties for the 'direct production' and the 'indirect production' (rest of the supply chain). So ab_M is a 200 x 2
#table
#Some products that describe household fuel use for heat and also transport fuel use for cars have another emission 
#intesntiy as well. These are held in seperate tables 'use_phase' and 'tail_pipe' (all other products have 0 here)

#To calculate the Emissions, each value in ab_M + the values in use_phase and tail_pipe are multiplied by the amount
#the household spends on each of the 200 products. These are stored in another table caled demand_KV (demand vector)
#The emissions for each product from the direct production, indirect production, and use_phase/tail_pipe are summed 
#to get the total emissions for that product.

#Once we have the total emissions for each product for that year, they are grouped together into 'sectors' that describe different things.
#There are 7 in total: Household Energy, Household Other, transport fuels, transport other, air transport, food, 
#tangible goods and  services

#The calculations are performed every year until 2050, with the values of demand_KV and ab_M changing slighting each year.
#This is based on 3 factors, efficiency improvements, changes in income and changes in household size. There is also a 
#section where these projections can change as a result of different policies (for the baseline no policies are introduced)

##################################################################################################################
##################################################################################################################
#Determine Emissions for all years

########INcluded in the start screen##############################

################Question 9.0 starts here##################################
year = 2025


##########################################
region = "County_Meath" #User_input

###U9.1####################
policy_label = "P2"  #This is just a label for the policy. Or the tool has a way to select different policies.

###############################


#########U9.0#####################################
country = "Ireland"  #This is to choose the country - USER_INPUT
ab = "IE"            #This is to identify the country, should match above
####################################################################


############Question 9.0#################
#Population_size

pop_size = 10000 #USER_INPUT
locals() ["pop_size" + Policy_label] = pop_size   #Sorry! Don't know how to do this without using locals!

##################################################################################


#Additional questions for the baseline################################

#######Question U9.2#################################################
U_type = "city" #'average', 'town', 'city', 'rural'  #This is to select the demand vector - the user should choose

#Extracting the correct demand vector

demand_KV = locals() ["Y_" + U_type][country].copy()


#House_size


#We also extract the house_size from this###########
House_size_ab = House_size.loc['Average_size_'+ U_type, country] #This is the default
#House_size_ab = 2.14#xx###USER_INPUT
################################################################################

#################################################################

#################################################################

###########Question U 9.4###############################################################
#Income_scaler

Income_choice =  "3rd_household"###options are "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
                                ###1st household is the richest.

#Otherwise,  the user selects the income level of the household (they choose by quntiles)

Income_scaler = Income_scaling.loc[Income_choice,country] / Income_scaling.loc['Total_household',country] #USER_INPUT
Elasticity = 1 # Random number for now. It should be specific to country and product

#if Income_choice == "3rd_household":
#    Income_scaler = 1
    
    

demand_KV *= Income_scaler * Elasticity
##############################################################################################




######### Question U9.4########################################


#This is the expected global reduction in product emissions

#Suggestion - Just give the user one of three options, with the default being normal

fast = 0.07
normal = 0.03
slow = 0.01

eff_scaling = 1 - normal #USER_INPUT



##############################################################


#Forming data for the calculations

#These are needed for holding the results
DF = pd.DataFrame(np.zeros((30,8)),index = list(range(2020,2050))
                                                      , columns = IW_sectors.columns)  #Holds final data in sectors 7 (+ sum)

DF_tot = pd.DataFrame(np.zeros((30,200)),index = list(range(2020,2050))
                                                      ,columns = products) #holds final data in products (200)

DF_area = pd.DataFrame(np.zeros((30,8)),index = list(range(2020,2050))
                                                      , columns = IW_sectors.columns)  #Holds area emissions (multiplies by pop_size
                                                      
direct_ab = "direct_"+ab
indirect_ab = "indirect_"+ab
M_countries.loc[direct_ab:indirect_ab,:].copy()
                                                      
ab_M = locals() [ab + "_M"] = M_countries.loc[direct_ab:indirect_ab,:].copy()  #Here the emission intensities                                                 
                                                                               #are selected
                                                                        



#These are needed for the use phase emissions

Tail_pipe_ab = Tail_pipe[country].copy()

Use_phase_ab = Use_phase[country].copy()

#This is needed for calculating the amount of electricity coming from heating

ad = Adjustable_amounts[country].copy()

elec_price = Electricity_prices[country]["BP_2019_S2_Euro"] 


#Baseline Modifications go here  ##Possibly not included in this version of the tool###########




##############################################################



##This is the end of the mandatory questions


##Optional questions
#################################################################################################
#Here the user can modify the default values for the the demand. IF THEY DON'T WANT TO THEN SKIP THIS PART.


#########Question 8#############################################################################
    #Public Transport types

public_transport = ['Railway transportation services', 'Other land transportation services', 
                    'Sea and coastal water transportation services', 'Inland water transportation services']
    
    
Public_transport_sum = demand_KV[public_transport].sum()    ###This describes the total use of public transport
    
rail_prop = demand_KV['Railway transportation services'] / Public_transport_sum
bus_prop = demand_KV['Other land transportation services'] / Public_transport_sum
ferry_prop = demand_KV['Sea and coastal water transportation services'] / Public_transport_sum
river_prop = demand_KV['Inland water transportation services'] / Public_transport_sum
    
    
#These 'prop' values can be adjustable by the user. 
#For example, if the user thinks there should be no water based travel this can be set to 0
#but then the other values should be increased so that total proportions sum to equal to 1
    
#In such a case, the code to do this would be
    
#river_prop = 0#USER_INPUT (often 0)
#ferry_prop = 0#USER_INPUT (often 0)
#bus_prop = bus_prop / (bus_prop + rail_prop) #USER_INPUT - code maintains the ratio between bus and rail
#rail_prop = rail_prop / (bus_prop + rail_prop) #USER_INPUT - code maintains the ratio between bus and rail

#ferry_prop = ferry_prop / (bus_prop + ferry_prop+ rail_prop)

#The values that should be adjusted are:

demand_KV['Railway transportation services'] = rail_prop * Public_transport_sum
demand_KV['Other land transportation services'] = bus_prop * Public_transport_sum
demand_KV['Sea and coastal water transportation services'] = ferry_prop * Public_transport_sum
demand_KV['Inland water transportation services'] = river_prop * Public_transport_sum

##############################################################################
    
#Otherwise, if there is no rail travel or river/sea travel then it should be:

#rail_prop = 0
#river_prop = 0
#ferry_prop = 0
#bus_prop = 1
       
######################################################################################################


#########Question 9##################################################################################
    #Electricity _ mix
#IT SHOULD BE SUGGESTED TO LEAVE THE DEFAULT VALUES 
#As above, the user can specify if the electricity mix is different to the country average for the BL
    
electricity = ['Electricity by coal', 'Electricity by gas','Electricity by nuclear',
                      'Electricity by hydro', 'Electricity by wind','Electricity by petroleum and other oil derivatives',
                      'Electricity by biomass and waste', 'Electricity by solar photovoltaic',
                      'Electricity by solar thermal', 'Electricity by tide, wave, ocean',
                      'Electricity by Geothermal', 'Electricity nec'] 

#No electricity goes in 'electricity nec'. This is used for local electricity production
    
elec_total = demand_KV[electricity].sum()
    
#The code works the same as above the the public transport. 
    
#e.g.
    
#hydro_prop = 0.7
#solar_pvc_prop = 0.3
#coal_prop = 0
#gas_prop = 0
#nuclear_prop = 0
#wind_prop = 0
#petrol_prop = 0
#solar_thermal_prop = 0
#tide_prop = 0
#geo_prop = 0
#nec_prop = 0

#Then the total kWh is determined from these props
#demand_KV[electricity] = 0
    
#demand_KV['Electricity by solar photovoltaic'] = solar_pvc_prop * elec_total
#demand_KV['Electricity by hydro'] = hydro_prop * elec_total
    
    
#if the user specifies the mix, then the electricity values change to the LCA values:

#for elec in electricity:
        
    #ab_M.loc[direct_ab:indirect_ab,electricity] = M_countries_LCA.loc[direct_ab:indirect_ab,electricity] 

#IT SHOULD BE SUGGESTED THAT THE USER DOES NOT ALTER THE ELECTRICITY MIX
################################################################################################################

#######Question 10#####################################################################################
    
    
    #Supply of household heating

liquids = ['Natural Gas Liquids', 'Kerosene', 'Heavy Fuel Oil', 'Other Liquid Biofuels']
solids = ['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)',
                  'Coke Oven Coke']
gases = ['Distribution services of gaseous fuels through mains', 'Biogas']
        
district = 'Steam and hot water supply services'
        
electricity_heat = (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"]) * elec_total * elec_price
        
Total_Fuel = demand_KV[solids].sum() + demand_KV[liquids].sum() + demand_KV[gases].sum() + demand_KV[district].sum() + electricity_heat

#We assume all 'fuels' are the same efficiency (obviously wrong, but no time to fix)
        
#########################
#PART 1 - The user selects the heating proportions from district heating, electricity and household combustion
#########################


#Default values are given by:
district_prop = demand_KV[district] / Total_Fuel

electricity_heat_prop = electricity_heat / Total_Fuel

combustable_fuels_prop = (demand_KV[solids].sum() + demand_KV[liquids].sum() + demand_KV[gases].sum()) / Total_Fuel

###THE USER CAN ALTER THESE BY::

#THESE NUMBERS NEED TO SUM TO 1
#district_prop = 0.0#district_prop#1##USER_INPUT
#electricity_heat_prop = 1.0#electricity_heat_prop##USER_INPUT
#combustable_fuels_prop = 0.0#combustable_fuels_prop##USER_INPUT

######################################
##Part 2 - Determine final values
######################################

#Then, the final values are given by:

#DISTRICT HEATING
demand_KV[district] = Total_Fuel * district_prop


#ELECTRICITY
for elec in electricity:
    
    prop = demand_KV[elec] / elec_total #determine amount of each electricity source in total electricity mix.
    elec_hold = (1 - (ad["elec_water"] +ad["elec_heat"] + ad["elec_cool"])) * demand_KV[elec] #electricity for appliances
    demand_KV[elec] = prop * electricity_heat_prop * Total_Fuel / elec_price #Scale based on electricity use in heat and elec mix
    demand_KV[elec] += elec_hold #Add on the parts to do with appliances
    
        
#COMBUSTABLE FUELS

#Here, the user can also alter the mix of the combustable fuels.

liquids_prop = demand_KV[liquids].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())
solids_prop = demand_KV[solids].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())
gases_prop = demand_KV[gases].sum()/ (demand_KV[liquids].sum() + demand_KV[solids].sum() + demand_KV[gases].sum())

#THE USER CAN CHANGE THESE VALUES BUT THE SUM MUST BE EQUAL TO 1!

############Question 10.1######################
#liquids_prop = 0 # #USER INPUT
#solids_prop = 0 ##USER_INPUT
#gases_prop = 1 # #USER_INPUT


#Then

for liquid in liquids:
    
    if demand_KV[liquids].sum() != 0:
        
        prop = demand_KV[liquid] / demand_KV[liquids].sum()  #Amount of each liquid in total liquid expenditure
        demand_KV[liquid] = prop * liquids_prop * combustable_fuels_prop * Total_Fuel
    else:
        
        demand_KV['Kerosene'] = liquids_prop * combustable_fuels_prop * Total_Fuel
        

        
for solid in solids:
    
    if demand_KV[solids].sum() != 0:
        prop = demand_KV[solid] / demand_KV[solids].sum()  #Amount of each solid in total solid expenditure
        demand_KV[solid] = prop * solids_prop * combustable_fuels_prop * Total_Fuel
    
    else:
        demand_KV['Wood and products of wood and cork (except furniture); articles of straw and plaiting materials (20)'] = solids_prop * combustable_fuels_prop * Total_Fuel

        
for gas in gases:
    
    if demand_KV[gases].sum() != 0:
        prop = demand_KV[gas] / demand_KV[gases].sum()  #Amount of each gas in total gas expenditure
        demand_KV[gas] = prop * gases_prop * combustable_fuels_prop * Total_Fuel

    else:
        demand_KV['Distribution services of gaseous fuels through mains'] = gases_prop * combustable_fuels_prop * Total_Fuel

######QUESTION 11###########################################
    #The 'direct_ab' value should be changed to the value the user wants. 
    #The user needs to convert the value into kg CO2e / Euro 
direct_district_emissions = ab_M.loc[direct_ab,district]#1.0475#USER_INPUT
ab_M.loc[direct_ab,district] = direct_district_emissions
################################################################

###This is the end of the additional baseline questions################################################
######################################################################

##Basic policy questions go here######################################

###Here, we are essentially just asking the questions we asked for the BL again. The problem is that before the 
##policy year (in this case 2025), the values should be equal to the baseline. So I have just redefined the variables
##here. But for the tool if all variables are predefined and then sent to a funciton to run the calculation, would they 
## need to be new variables?



if policy_label != "BL":   #Not sure if I need. Maybe can just set the policy year to 2050 as default
    
    ####################User enters the policy year U10.1
    policy_year = 2025#USER_INPUT
    
    ####################################################
    
    #
    ############Question U10.2############################################################
   ######### Population_size

    pop_size_policy = 10000 #USER_INPUT
    locals() ["pop_size" + Policy_label] = pop_size
    #######################

    #############################
    
    #######Question U10.xx#################################
    ##We are not reasking this question in the new current description of the tool
    
    #U_type = "average" #'average', 'town', 'city', 'rural'  #This is to select the demand vector - the user should choose

    #Extracting the correct demand vector

    #demand_KV_policy = locals() ["Y_" + U_type][country].copy()
    

    

################################################################################

    #################################################################
    
    
    ###########Question U 10.xx#########################################################
    #####We are not reasking this question in the new version of the tool
    
    #Income_scaler

    #Income_choice =  "3rd_household"###options are "1st_household" , "2nd_household", "3rd_household", "4th_household", "5th_household"
                                ###1st household is the richest.

    #Otherwise,  the user selects the income level of the household (they choose by quntiles)

    #Income_scaler = Income_scaling.loc[Income_choice,country] / Income_scaling.loc['Total_household',country] #USER_INPUT
    #Elasticity = 1 # Random number for now. It should be specific to country and product

    #if Income_choice == "3rd_household":
    #    Income_scaler = 1

    #demand_KV_policy *= Income_scaler * Elasticity
##############################################################################################



    

    

##############################################################


        ###########################################
#     NEW PART FOR THE CONSTRUCTION EMISSIONS!
#######################################################       
##Construction emissions#############################################################################################
        
##U 10.3#############################################
       
New_floor_area = 500000   #USER_INPUT
        
#    END OF PART FOR THE CONSTRUCTION EMISSIONS!    
        
###############################################################################################################


###############################################################
#############The actual calculation starts here################
#################################################################


income_scaling = Income_proj.loc[country]    #Scale factor applied to income - unique value for each decade
house_scaling = House_proj.loc[country]      #Scale factor applied to household size - unique value for each decade

while year <= 2050:
    
    #check the policy part
    
    if year == 2020:
   
        income_mult = 1 #This is just for the year 2020
        house_mult = 1  #This is just for the year 2020
        eff_factor = 1  #This is just for the year 2020
    
    
###########Policies are from here################################################################
    if policy_label != "BL" and year == policy_year: #& policy_label != "BL":
        
        #demand_KV = demand_KV_policy
        #house_size_ab = house_size_ab_policy  #Because we are not asking these questions
        pop_size = pop_size_policy
        
        #Questions should be asked in this order! Some depend on the results of others
##############Household Efficiency###################################################

###########U11.1#################################
        EFF_gain = "TRUE" #USER_INPUT U11.1.0
        EFF_scaler = 0.1 #USER_INPUT   U11.1.1
        
        if EFF_gain == "TRUE":
            
            Eff_improvements(demand_KV, EFF_scaler)
            
########################################################################################################################

##############Local_Electricity########################################################################################
######################U11.2######################################
        Local_electricity = "TRUE" #USER_INPUT  U11.2.0
        EL_Type = 'Electricity by solar photovoltaic'#USER_INPUT U11.2.1  'Electricity by solar photovoltaic','Electricity by biomass and waste','Electricity by wind','Electricity by Geothermal'  
        EL_scaler = 0.05 #User_Input U11.2.2

        if Local_electricity == "TRUE":
            
            Local_generation(ab_M,demand_KV, EL_scaler, EL_Type)
        
#########################################################################################################################

##############Sustainable_Heating######################################################################################
    ############# U11.3#########################
    
    
        S_heating = "FALSE" #USER_INPUT   U11.3.0
        
        #district_prop = 0.25 #USER_INPUT  U11.3.1
        #electricity_heat_prop = 0.75 #USER_INPUT
        #combustable_fuels_prop = 0.25 #USER_INPUT
        
        #solids_prop = 0.0 #USER_INPUT   U11.3.2
        #gases_prop = 0.0 #USER_INPUT
        #liquids_prop = 0.0 #USER_INPUT
        
        
        #District_value = ab_M.loc[direct_ab,district].sum()# ab_M   0.0 # USER_INPUT  U11.3.3
        
        if S_heating == "TRUE":
            
            local_heating(ab_M, demand_KV, district_prop, electricity_heat_prop, 
                          combustable_fuels_prop, liquids_prop, gases_prop, solids_prop, District_value)
        
            #This is just a repeat of the baseline part
        
#########################################################################################################################

###########Biofuel_in_transport########################################################################################
    ########### U12.1##############   
    
        Biofuel_takeup = "FALSE" #USER_INPUT  U12.1.0
        bio_scaler = 0.5 #USER_INPUT      U12.1.1        
        if Biofuel_takeup == "TRUE":
            
            BioFuels(demand_KV, bio_scaler)

##########################################################################################################################

########Electric_Vehicles##################################################################################################
       ###### U12.2#############
    
        EV_takeup = "FALSE" #USER_INPUT  U12.2.0
        EV_scaler = 0.5     #User_Input U12.2.1
        
        if EV_takeup == "TRUE":
            
            Electric_Vehicles(demand_KV, EV_scaler)
        
############################################################################################################################

#########Modal_Shift#######################################################################################################
    #########U12.3#################    
    
        Modal_Shift = "TRUE" #USER_INPUT U12.3.0
        MS_fuel_scaler = 0.04 #USER_INPUT U12.3.1
        MS_veh_scaler = 0.04 #USER_INPUT U12.3.2
        MS_pt_scaler = -0.04  #USER_INPUT U12.3.3
        
        if Modal_Shift == "TRUE":
            
            Transport_Modal_Shift(demand_KV, MS_fuel_scaler, MS_pt_scaler, MS_veh_scaler)
        
###########################################################################################################################            
        
    if year > 2020 and year <= 2030:
                
        income_mult = income_scaling['2020-2030']   # Select the income multiplier for this decade
        house_mult = house_scaling['2020-2030']     # Select the house multiplier for this decade
        eff_factor = eff_scaling
        
    if  year > 2030 and year <= 2040: 
        
        income_mult = income_scaling['2030-2040']   # Select the income multiplier for this decade
        house_mult = house_scaling['2030-2040']     # Select the house multiplier for this decade
        eff_factor = eff_scaling
        
    if year > 2040 and year <=2050:
        
        income_mult = income_scaling['2040-2050']   # Select the income multiplier for this decade
        house_mult = house_scaling['2040-2050']     # Select the house multiplier for this decade
        eff_factor = eff_scaling
        
        
    demand_KV *= income_mult
        
    ab_M *=eff_factor
        
    Use_phase_ab *=eff_factor
        
    Tail_pipe_ab *=eff_factor
        
        
    #Then we have to recalculate
        
        
    GWP_ab = pd.DataFrame(ab_M.to_numpy().dot(np.diag(demand_KV.to_numpy()))) # This is the basic calculation

    GWP_ab.index = ['direct' , 'indirect']

    GWP_ab.columns = products

    Use_phase_ab_GWP = demand_KV * Use_phase_ab # This adds in the household heating fuel use

    Tail_pipe_ab_GWP = demand_KV * Tail_pipe_ab # This adds in the burning of fuel for cars

    Total_use_ab = Tail_pipe_ab_GWP.fillna(0) + Use_phase_ab_GWP.fillna(0) #This puts together in the same table (200 x 1)
                                                                           #all of the other 200 products are zero
    #Put together the IO and use phase

    GWP_ab.loc['Use phase',:] = Total_use_ab
        
        
    #GWP_EE_pc = GWP_EE/House_size_EE
        
    #print(year)
    
        
        
    #GWP_EE = GWP_EE * (eff_factor) * (income_mult)
        
    GWP_ab_pc = GWP_ab / (House_size_ab * house_mult)   
    
#Put the results into sectors  
    
    DF.loc[year] =IW_sectors_np_tr.dot(GWP_ab_pc.sum().to_numpy())
    DF_tot.loc[year] = GWP_ab_pc.sum()
    
    DF_area.loc[year] = IW_sectors_np_tr.dot(GWP_ab_pc.sum().to_numpy()) * pop_size
    
    
    
    year +=1
    
DF['Total_Emissions'] = DF.sum(axis = 1)
DF_area['Total_Emissions'] = DF_area.sum(axis =1)


###########################################################################################################
#New Construction Emissions part!
#################################################################################################################

if policy_label != "BL":
    if country in North:
    
        Building_Emissions = 350 * New_floor_area/pop_size
    
    if country in West:
    
        Building_Emissions = 520 * New_floor_area/pop_size

    if country in East:
    
        Building_Emissions = 580 * New_floor_area/pop_size

    DF.loc[policy_year, 'Total_Emissions'] += Building_Emissions

    DF_area.loc[policy_year,'Total_Emissions'] += Building_Emissions * pop_size


 
##############################################################################################################
#End of Construction Emissions part!
#############################################################################################################
##Adding total emissions by multiplying by population



#F_tot.columns = Exio_products
locals()[region + "_Emissions_" + policy_label] = DF
locals()[region+ "_Emissions_tot_" + policy_label] = DF_tot

locals ()[region + "_Area_Emissions_" + policy_label] = DF_area


print("County_Meath_Emissions_P2", County_Meath_Emissions_P2)


print("County_Meath_Emissions_P1", County_Meath_Emissions_P1)

# Graphs are from here

#First Graph is a breakdown of the Emissions as a stacked bar graph. Maybe best to just show this one by itself?

#Describe Emissions over time 
#The construction Emissions are now shown here. I just added very quickly so please make better!

fig, ax = plt.subplots(1,figsize = (15,10))
#Name of country Emissions
country = "County_Meath"
Policy_label = "BL"

DF = locals()[country + "_Emissions_" + Policy_label].copy()

###
#x = np.arange(list(range(2020,2050)))
#plot bars

Labels = ['HE','HO','TF','TO','AT','F','TG','S']
sectors = list(IW_sectors.columns)

bottom = len(DF) * [0]
for idx, name in enumerate(sectors):
    plt.bar(DF.index, DF[name], bottom = bottom)
    bottom = bottom + DF[name]
 
plt.bar(DF.index, DF['Total_Emissions'], edgecolor = 'black', color = 'none')

ax.set_title("Annual Household Emissions for %s" % country, fontsize = 20)
ax.set_ylabel('Emissions / kG CO2 eq', fontsize = 15)
ax.tick_params(axis="y", labelsize=15)
ax.set_xlabel('Year', fontsize = 15)
ax.tick_params(axis="x", labelsize=15)

ax.legend(Labels, bbox_to_anchor=([1, 1, 0, 0]), ncol=8, prop={'size': 15})



plt.show()


#Clicking on a bar or looking at a comparison between policies should generate this second graph
#The labels below are just for different policies.

#There should also be an option to remove the total emissions part (This is basically only useful for new areas)



# Now_make_graphs_of these

#os.chdir("C:/Users/PeterRobertWalke/Documents/QGASSP/Data sources/Calculation_Data/Updated/Graphs")



width = 0.2
x = np.arange(len(County_Meath_Emissions_BL.columns))

fig, ax = plt.subplots(figsize = (15,10))

rects1 = ax.bar(x + 0 * width, County_Meath_Emissions_BL.loc[2025], width, label='BL')
rects2 = ax.bar(x - 1.5 * width, County_Meath_Emissions_P1.loc[2025], width, label='P1') # Extra policies
rects3 = ax.bar(x + 1.5 * width, County_Meath_Emissions_P2.loc[2025], width, label='P2')   # Extra Policies
#rects4 = ax.bar(x - width / 2, Berlin_Emissions_NA.loc[2025], width, label='NA')  # Extra Policies


#plt.bar(x_sectors, E_countries_GWP_sectors_pp['EE'], width = 0.5,  color='green')
#plt.bar(x_sectors, E_countries_GWP_sectors_pp['FI'], width = 0.5, color='blue', alpha = 0.5)
ax.legend_size = 20
ax.set_ylabel('Emissions / kG CO2 eq', fontsize = 20)
ax.set_xlabel('Emissions sector', fontsize = 20)
ax.set_title('Per capita emissions by sector for County Meath policies', fontsize = 25)
ax.set_xticks(x)
ax.set_xticklabels(County_Meath_Emissions_BL.columns, fontsize = 15)
#ax.set_yticklabels( fontsize = 15)
ax.tick_params(axis="y", labelsize=15)
ax.legend(prop={'size': 15})



#x.label(rects1, padding=3)
#x.label(rects2, padding=3)                                                        
                                                        
#lt.xlabel("Sectors")
#lt.ylabel("CO2 eq /  kG?")
#lt.title("Global Emissions by Sector")

plt.xticks(x, County_Meath_Emissions_BL.columns, rotation = 90)

#plt.savefig("Sectoral_Graphs_breakdown.jpg",bbox_inches='tight', dpi=300)


plt.show()


# In[34]:


#Finally, there should be some sort of cumulative emissions measurement. Ths is also important in the case of delaying policies


# In[35]:


#This calculates the different cumulative emissions
#Policy_labels = ["BL", "MSx50", "SHx50", "EVx50", "NA", "ALLx50_2035", "ALLx50_2025"]   #THIS is just all the policies I made 
Policy_labels = ["BL", "P1", "P2"]
#Policy_labels = ["BL", "RFx50_2025", "RFx50_2035"]#for the graphs
region = "County_Meath"
for policy in Policy_labels:
    
    locals()[region + "_summed_" + policy] = pd.DataFrame(np.zeros((30,1)),index = list(range(2020,2050)), columns = ["Summed_Emissions"])

    locals()[region + "_summed_" + policy].loc[2020, "Summed_Emissions"] = locals()[region + "_Emissions_" + policy].loc[2020,'Total_Emissions']
    years = list(range(2020,2050))
    for year in years:
        locals()[region + "_summed_" + policy].loc[year+1,"Summed_Emissions"] = locals()[region + "_summed_" + policy].loc[year,"Summed_Emissions"]+ locals()[region + "_Emissions_" + policy].loc[year+1,'Total_Emissions']
        
    print("The Emissions in 2025 for %s is" % policy, locals()[region + "_Emissions_" + policy].loc[2025,'Total_Emissions'])


# In[36]:


#Make the graph 

#Describe Emissions over time


fig, ax = plt.subplots(1,figsize = (15,10))
#Name of country Emissions
country = "County_Meath"
#Policy_labels = ["BL","EVx50", "MSx50", "SHx50", "NA"]
Policy_labels = ["BL", "P1", "P2"]


counter = 0
for policy in Policy_labels:
    
    

    DF = locals()[country + "_summed_" + policy].copy()

###
#x = np.arange(list(range(2020,2050)))
#plot bars

#Labels = ['HE','HO','TF','TO','AT','F','TG','S']
    sectors = list(IW_sectors.columns)

#bottom = len(DF) * [0]
#for idx, name in enumerate(sectors):
 #   plt.bar(DF.index, DF[name], bottom = bottom)
  #  bottom = bottom + DF[name]

    plt.plot(DF.index, DF.Summed_Emissions, )
    
    plt.fill_between(DF.index, DF.Summed_Emissions,alpha = 0.4)#+counter)
    
    counter+=0.1

#x = np.arange(len(Ireland_Emissions.index))
#width = 0.8

#rects1 = ax.bar(x, Ireland_Emissions['Housing_Energy'], width, label=ab)

ax.set_title("Aggregated per capita Emissions for %s 2020-2050" % country, fontsize = 20)
ax.set_ylabel('Emissions / kG CO2 eq', fontsize = 15)
ax.tick_params(axis="y", labelsize=15)
ax.set_xlabel('Year', fontsize = 15)
ax.tick_params(axis="x", labelsize=15)

ax.legend(Policy_labels, loc='upper left' , ncol=2, prop={'size': 15})

#plt.savefig("Cumulatove_example_high_buildphase.jpg",bbox_inches='tight', dpi=300)


plt.show()

print("County_Meath_Emissions_P1", County_Meath_Emissions_P1)

print("County_Meath_Emissions_P4", County_Meath_Emissions_P4)
