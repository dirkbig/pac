import numpy as np
import source.const as const

""" Grid Configuration """


class ConfigurationUtilityEly:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""

        """ 
            Simulation environment
        """
        self.num_days = const.num_steps * const.market_interval / 60 / 24
        self.market_interval = const.market_interval  # minutes

        # time
        self.start = 0

        self.num_steps = const.num_steps

        """ 
            Market structure 
        """
        # TODO: this is already defined in const.py
        self.pricing_rule = 'pac'  # or 'pab'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = True
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'
        # Define for how many time steps in the future a forecast is supposed to be used for optimizing bidding
        # strategies of the electrolyzer.
        self.forecast_horizon = 96 * 7

        """
            Battery
        """
        self.battery_presence = False

        """
            PV commercial
        """
        self.pv_presence = False
        self.pv_commercial_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'

        """ 
            Utility 
        """
        self.utility_presence = True

        self.negative_pricing = False
        self.dynamical_pricing = False
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'

        """ 
            Households basic configuration 
        """
        self.consumers = 0
        self.prosumers_with_only_pv = 0
        self.prosumers_with_ess = 0
        self.prosumers_with_pv_and_ess = 0
        self.num_households = self.consumers + self.prosumers_with_only_pv + self.prosumers_with_ess + \
            self.prosumers_with_pv_and_ess
        self.classification_array = []

        """ consumers"""
        for agent in range(self.consumers):
            self.classification_array.append([True, False, False])

        """ prosumers with only PV """
        for agent in range(self.prosumers_with_only_pv):
            self.classification_array.append([True, True, False])

        """ prosumers with only ESS"""
        for agent in range(self.prosumers_with_ess):
            self.classification_array.append([True, False, True])

        """ prosumers with both PV and ESS"""
        for agent in range(self.prosumers_with_pv_and_ess):
            self.classification_array.append([True, True, True])

        """ 
            Load data
        """
        self.household_loads_folder = 'household_load_profiles_htw'
        self.num_households_with_consumption = self.num_households

        """ 
            PV data
        """
        self.num_pv_panels = self.prosumers_with_only_pv + self.prosumers_with_pv_and_ess
        self.pv_output_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'

        """    
            ESS data
        """
        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 10)
        initial_capacity_list = np.full(self.num_households_with_ess, 9)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)


class ConfigurationUtilityElyPv:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""

        """ 
            Simulation environment
        """
        self.num_days = const.num_steps * const.market_interval / 60 / 24
        self.market_interval = const.market_interval  # minutes

        # time
        self.start = 0

        self.num_steps = const.num_steps

        """ 
            Market structure 
        """
        # TODO: this is already defined in const.py
        self.pricing_rule = 'pac'  # or 'pab'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = True
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'
        # Define for how many time steps in the future a forecast is supposed to be used for optimizing bidding
        # strategies of the electrolyzer.
        self.forecast_horizon = 96 * 7

        """
            Battery
        """
        self.battery_presence = False

        """
            PV commercial
        """
        self.pv_presence = True
        self.pv_commercial_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'


        """ 
            Utility 
        """
        self.utility_presence = True

        self.negative_pricing = False
        self.dynamical_pricing = False
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'

        """ 
            Households basic configuration 
        """
        self.consumers = 0
        self.prosumers_with_only_pv = 0
        self.prosumers_with_ess = 0
        self.prosumers_with_pv_and_ess = 0
        self.num_households = self.consumers + self.prosumers_with_only_pv + self.prosumers_with_ess + \
            self.prosumers_with_pv_and_ess
        self.classification_array = []

        """ consumers"""
        for agent in range(self.consumers):
            self.classification_array.append([True, False, False])

        """ prosumers with only PV """
        for agent in range(self.prosumers_with_only_pv):
            self.classification_array.append([True, True, False])

        """ prosumers with only ESS"""
        for agent in range(self.prosumers_with_ess):
            self.classification_array.append([True, False, True])

        """ prosumers with both PV and ESS"""
        for agent in range(self.prosumers_with_pv_and_ess):
            self.classification_array.append([True, True, True])

        """ 
            Load data
        """
        self.household_loads_folder = 'household_load_profiles_htw'
        self.num_households_with_consumption = self.num_households

        """ 
            PV data
        """
        self.num_pv_panels = self.prosumers_with_only_pv + self.prosumers_with_pv_and_ess
        self.pv_output_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'

        """    
            ESS data
        """
        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 10)
        initial_capacity_list = np.full(self.num_households_with_ess, 9)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)


class ConfigurationUtility10prosumer:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""

        """ 
            Simulation environment
        """
        self.num_days = const.num_steps * const.market_interval / 60 / 24
        self.market_interval = const.market_interval  # minutes

        # time
        self.start = 0

        self.num_steps = const.num_steps

        """ 
            Market structure 
        """
        # TODO: this is already defined in const.py
        self.pricing_rule = 'pac'  # or 'pab'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = False
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'
        # Define for how many time steps in the future a forecast is supposed to be used for optimizing bidding
        # strategies of the electrolyzer.
        self.forecast_horizon = 96 * 7

        """
            Battery
        """
        self.battery_presence = False

        """
            PV commercial
        """
        self.pv_presence = False
        self.pv_commercial_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'


        """ 
            Utility 
        """
        self.utility_presence = True

        self.negative_pricing = False
        self.dynamical_pricing = False
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'

        """ 
            Households basic configuration 
        """
        self.consumers = 0
        self.prosumers_with_only_pv = 0
        self.prosumers_with_ess = 0
        self.prosumers_with_pv_and_ess = 10
        self.num_households = self.consumers + self.prosumers_with_only_pv + self.prosumers_with_ess + \
            self.prosumers_with_pv_and_ess
        self.classification_array = []

        """ consumers"""
        for agent in range(self.consumers):
            self.classification_array.append([True, False, False])

        """ prosumers with only PV """
        for agent in range(self.prosumers_with_only_pv):
            self.classification_array.append([True, True, False])

        """ prosumers with only ESS"""
        for agent in range(self.prosumers_with_ess):
            self.classification_array.append([True, False, True])

        """ prosumers with both PV and ESS"""
        for agent in range(self.prosumers_with_pv_and_ess):
            self.classification_array.append([True, True, True])

        """ 
            Load data
        """
        self.household_loads_folder = 'household_load_profiles_htw'
        self.num_households_with_consumption = self.num_households

        """ 
            PV data
        """
        self.num_pv_panels = self.prosumers_with_only_pv + self.prosumers_with_pv_and_ess
        self.pv_output_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'

        """    
            ESS data
        """
        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 10)
        initial_capacity_list = np.full(self.num_households_with_ess, 9)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)