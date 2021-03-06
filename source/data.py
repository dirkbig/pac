from source.data_methods import *
import plots
from grid_config import ConfigurationMixin
import numpy as np
from copy import deepcopy


import logging
data_log = logging.getLogger('run_microgrid.data')


class Data(ConfigurationMixin, object):
    def __init__(self, run_configuration, model):
        super().__init__()

        self.model = model
        """initialise data sets"""
        data_type = "data_set_time_series"  # random_1_step, custom_load_profiles, data_set_time_series

        # If a new run configuration is given, update the configuration fields.
        if run_configuration is not None:
            self.update_config(run_configuration)

        if data_type == 'random_1_step':
            """ check whether the market platform can complete a full run, using random numbers of simplicity
                -> do not use for testing, since input is all random, just for bug finding"""
            self.load_list = np.random.rand(self.num_households)
            self.pv_gen_list = np.random.rand(self.num_households)
            self.ess_list = [[np.random.randint(0, 1) for _ in range(2)] for _ in range(self.num_households)]
            self.electrolyzer_list = [None for _ in range(self.num_households)]
            assert len(self.load_list) == len(self.ess_list) == len(self.pv_gen_list)
            self.agent_data_array = np.asarray([self.load_list, self.pv_gen_list, self.ess_list])

        elif data_type == 'custom_load_profiles':
            """ create simple (non random) test-profiles, currently also 1 step only
                -> use for testing of simply grids and hypotheses, check whether strategies are behaving"""
            self.load_list = [0, 0, 100, 10]
            self.pv_gen_list = [3, None, 3, None]
            self.ess_list = [[0.5, 5], [0.5, 5], [0, 5], [0, 5]]
            self.electrolyzer_list = [None, None, None, None]

            assert len(self.load_list) == len(self.ess_list) == len(self.pv_gen_list)
            self.agent_data_array = np.asarray([self.load_list, self.pv_gen_list, self.ess_list])

        elif data_type == 'data_set_time_series':
            """ run model with real data, check if the strategies are performing, and for research results """
            self.load_array = self.get_load_profiles()
            self.pv_gen_array = self.get_pv_house_profiles()
            self.ess_list = self.ess_characteristics_list
            self.electrolyzer_list = self.get_electrolyzer_profiles()
            self.pv_commercial_list = self.get_pv_commercial_profiles()
            if self.num_households > 0:
                assert len(self.load_array) == self.num_households
            if self.num_pv_panels > 0:
                assert len(self.pv_gen_array) == self.num_pv_panels
            if self.num_households_with_ess > 0:
                assert len(self.ess_list) == self.num_households_with_ess
            self.agent_data_array = self.fill_in_classification_array()

        else:
            data_log.error("data type not found")
            exit()

        if self.utility_presence is True:
            if self.utility_dynamical_pricing is True:
                self.utility_pricing_profile = self.get_utility_profile()
                assert len(self.utility_pricing_profile) >= self.num_steps
                self.utility_pricing_profile = np.asarray(self.utility_pricing_profile)

                if self.negative_pricing is False:
                    self.utility_pricing_profile[self.utility_pricing_profile < 0] = 0
            else:
                self.utility_pricing_profile = []

        """ MEASUREMENTS """
        # data array to capture: num_households x num_steps
        self.soc_list_over_time = np.zeros([self.num_households, self.num_steps])
        self.deficit_over_time = np.zeros([self.num_households, self.num_steps])
        self.overflow_over_time = np.zeros([self.num_households, self.num_steps])
        # data array to capture: num_steps
        self.clearing_price_min_avg_max = np.zeros([self.num_steps, 3])
        self.clearing_quantity = np.zeros([self.num_steps, 1])
        self.utility_price = np.zeros([self.num_steps, 1])
        self.household_demand = np.zeros([self.num_steps, 1])

        # to be expanded after all agents are initialized
        self.agent_measurements = {}

    def initiate_measurement_dict(self):

        for _, agent in self.model.agents.items():
            self.agent_measurements[agent.id] = {
                "energy_surplus_over_time": np.zeros(self.num_steps),
                "bid_energy_over_time": np.zeros(self.num_steps),
                "traded_volume_over_time": np.zeros(self.num_steps),
                "revenue_over_time": np.zeros(self.num_steps),
            }

    def fill_measurement_dict(self, agent_id):

        # self.model.data.agent_measurements[agent_id]["energy_surplus_over_time"][self.model.step_count] = \

        # self.model.data.agent_measurements[agent_id]["bid_energy_over_time"][self.model.step_count] =
        self.model.data.agent_measurements[agent_id]["traded_volume_over_time"][self.model.step_count] = \
            sum(self.model.auction.who_gets_what_dict[agent_id])
        #
        # self.model.data.agent_measurements[agent_id]["revenue_over_time"][self.model.step_count] = \
        #     self.model.agents[agent_id].wallet.payment_history[self.model.step_count]

    def plots(self):
        # traded_volume_over_time(self.num_steps, self.agent_measurements)
        plots.soc_over_time(self.num_steps, self.soc_list_over_time)
        plots.households_deficit_overflow(self.num_steps, self.deficit_over_time, self.overflow_over_time)
        plots.clearing_over_utility_price(
            self.num_steps, self.utility_price, self.clearing_price_min_avg_max, self.clearing_quantity)
        plots.clearing_quantity(self.num_steps, self.clearing_quantity)
        plots.clearing_quantity_over_demand(self.num_steps, self.clearing_quantity, self.household_demand)
        # If an electrolyzer is present, plot its behaviour.
        if 'Electrolyzer' in self.model.agents:
            plots.electrolyzer(self.num_steps, self.model.agents['Electrolyzer'])

        plots.show()

    def get_load_profiles(self):
        """ loading in household load profiles """
        if self.num_households == 0:
            # Case: No households are in the system, thus the time series do not have to be loaded.
            return []

        test = False
        if test is True:
            load_list = np.ones([self.num_households, self.num_steps]) * 0.01
            return load_list

        load_list = csv_read_load_file(self.num_households, self.household_loads_folder)

        """ load is in minutes, now convert to intervals """
        # TODO: add all consumption within 15 step interval to i interval element, instead of (naive) sampling
        # for i in range(len(load_list)):
        #     load_list[i] = load_list[i][0::self.market_interval]
        #

        load_list = self.slice_from_to(load_list, self.forecast_horizon)
        assert [len(load_list[i]) == self.num_steps for i in range(len(load_list))]

        """ manual tuning of data can happen here """
        load_array = np.array(load_list)
        load_array[np.isnan(load_array)] = 0
        # TODO: german consumption rates?
        # WHAT WAS HAPPENING HERE? LOAD PROFILES WERE TUNED, THIS SHOULDN'T HAPPEN????
        """
        for i in range(len(load_list)):
            max_element = np.amax(load_array[i])
            if max_element > 1:
                load_array[i] = load_array[i] / max_element
                print(max_element)

        ''' manual tuning of data can happen here '''
        load_array = load_array*2
        """

        return load_array

    def get_pv_house_profiles(self):
        """ loading in load profiles """
        # TODO: currently, all agents get the same profile :( """
        pv_gen_list = []
        if self.num_pv_panels > 0:
            # Case: There is PV present, thus the timeseries has to be loaded.
            pv_gen_list = csv_read_pv_output_file(self.num_pv_panels, self.pv_output_profile)
            # pv_gen_array = np.array(pv_gen_list)

            pv_gen_list = self.slice_from_to(pv_gen_list)
            if self.num_pv_panels > 0:
                # Case: PV panels are present. Then test if the pv time series have the correct length.
                assert [len(pv_gen_list[i]) == self.num_steps for i in range(len(pv_gen_list))]

        return pv_gen_list

    def get_utility_profile(self):
        """ loads in utility pricing profile

        electricity_price = csv_read_electricity_price()
        # Return only the values (second column of the matrix) [EUR/kWh].
        return [x[1] for x in electricity_price]
        """
        utility_profile_dict = csv_read_utility_file(self.utility_profile)
        utility_profile_dict = self.slice_from_to(utility_profile_dict, self.forecast_horizon)
        assert len(utility_profile_dict) == self.num_steps + self.forecast_horizon


        # utility_profile_dict = utility_profile_dict[0::self.market_interval]
        return utility_profile_dict

    def get_electrolyzer_profiles(self):
        """ loading in load profiles

        # loading in load profiles
        h2_load = csv_read_load_h2()
        # Return only the H2 load values of the matrix (second column) [kg].
        return [x[1] for x in h2_load]
        """
        electrolyzer_list = csv_read_electrolyzer_profile(self.fuel_station_load)
        electrolyzer_list = self.slice_from_to(electrolyzer_list, self.forecast_horizon)
        assert len(electrolyzer_list) == self.num_steps + self.forecast_horizon

        return electrolyzer_list

    def get_pv_commercial_profiles(self):
        pv_commercial_list = csv_read_pv_profile(self.pv_commercial_profile)
        pv_commercial_list = self.slice_from_to(pv_commercial_list, self.forecast_horizon)
        assert len(pv_commercial_list) == self.num_steps + self.forecast_horizon

        return pv_commercial_list

    def fill_in_classification_array(self):
        """ fill_in_classification_array according to configuration Mixin """
        agent_data_array = deepcopy(self.classification_array)

        load = 0
        pv = 0
        ess = 0
        for agent in range(len(self.classification_array)):
            if self.classification_array[agent][0]:
                agent_data_array[agent][0] = self.load_array[load]
                load += 1
            else:
                agent_data_array[agent][0] = None

            if self.classification_array[agent][1]:
                agent_data_array[agent][1] = self.pv_gen_array[pv]
                if type(self.classification_array[agent][1]) is not bool:
                    # If the classification value for PV for this household is not a boolean, it is treated as a
                    # multiplier for the PV time series.
                    multiplier = self.classification_array[agent][1]
                    agent_data_array[agent][1] = [i * multiplier for i in agent_data_array[agent][1]]
                pv += 1
            else:
                agent_data_array[agent][1] = None

            if self.classification_array[agent][2]:
                agent_data_array[agent][2] = self.ess_list[ess]
                ess += 1
            else:
                agent_data_array[agent][2] = None

        return agent_data_array

    def slice_from_to(self, file, foresight_timeframe=0):
        # Slice the loaded timeseries to the needed length, which is the simulation time frame plus for some time series
        # the amount of time steps that are looked into with the optimization.
        if type(file[0]) == list:
            # Case: the first list entry is also a list, thus we have multiple timeseries here.
            for profile in range(len(file)):
                file[profile] = file[profile][self.sim_start:self.sim_start + self.num_steps + foresight_timeframe]
        elif type(file) == list:
            # Case: file is a list but values in the list are not also lists, thus this is only one time series.
            file = file[self.sim_start:self.sim_start + self.num_steps + foresight_timeframe]
        else:
            # file is not a list, this is a wrong format, thus an exception is raised.
            raise TypeError('Expected time series date in the format list or list of lists.')

        return file


if __name__ == "__main__":
    path = os.chdir("..")
    data = Data()
    # print('fuel station load: ', data.fuel_station_load)
    # print('utility prices data: ', data.utility_profile)
    # print('household load data set: ', data.household_loads_folder)
    # print('total ess storage capacity: %d kWh' % data.total_ess_capacity)

    plot_avg_load_profile(data.num_steps, data.load_array)
    plot_avg_pv_profile(data.num_steps, data.pv_gen_array)
    plot_fuel_station_profile(data.num_steps, data.electrolyzer_list)
    total_generation_vs_consumption(data.num_steps, data.pv_gen_array, data.load_array)
    show()
