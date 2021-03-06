from source import microgrid_environment
from eval_result.eval_verbose import eval_print
from grid_config_profile import ConfigurationUtility50prosumerEly as Config
# from grid_config import ConfigurationMixin as Config

import logging
import dill

logging.basicConfig(level=logging.WARNING)
grid_log = logging.getLogger('run_microgrid')

fh = logging.FileHandler('pac_log.txt')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
grid_log.addHandler(fh)

trade_deals_list_per_step = {}
clearing_price = {}
clearing_quantity = {}


def extract_data():
    trade_deals_list_per_step[microgrid.step_count] = microgrid.auction.trade_pairs
    clearing_price[microgrid.step_count] = microgrid.auction.clearing_price
    clearing_quantity[microgrid.step_count] = microgrid.auction.clearing_quantity


def create_microgrid():
    """create microgrid"""
    microgrid_ = microgrid_environment.MicroGrid(Config())
    grid_log.info('microgrid class created')
    return microgrid_


def step_microgrid():
    microgrid.sim_step()
    grid_log.info('Step %d' % microgrid.step_count)
    extract_data()


microgrid = create_microgrid()

for step in range(microgrid.data.num_steps):
    print("\n*******************************************************")
    print("                     step", microgrid.step_count)
    print("*******************************************************")
    step_microgrid()

assert microgrid.step_count == microgrid.data.num_steps

write_output_to_csv = False
if write_output_to_csv:
    import csv
    with open("test_result.csv", "w", newline='') as file:
        writer = csv.writer(file)
        for i in range(len(trade_deals_list_per_step)):
            this_row = []
            if trade_deals_list_per_step[i+1] is None:
                # Case: This trade entry is None. While a time step without a trade might lead to an entry of None or
                # an empty list, make all Nones to empty lists for further processing.
                trade_deals_list_per_step[i + 1] = []
            if len(trade_deals_list_per_step[i+1]) > 0:
                for row_entry in trade_deals_list_per_step[i+1]:
                    this_row += row_entry
            else:
                this_row = ['No trade was made']

            writer.writerow(this_row)

# Save the session result to, for example, create other plots later on.
save_session = True

if save_session:
    import pickle
    result_loc = 'eval_result/stored_session/test_pkl.pkl'
    filehandler = open(result_loc, 'wb')
    pickle.dump(microgrid, filehandler)
    filehandler.close()
    # dill.dump_session(session_name)
    print('Session saved at', result_loc)


eval_print(microgrid)
microgrid.data.plots()

print("\n*******************************************************")
print("                  Simulation finished")
print("*******************************************************")


