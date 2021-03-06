from source.auctioneer_methods import *

from plots import clearing_snapshot
from mesa import Agent
import seaborn as sns
from source.wallet import Wallet

sns.set()
auction_log = logging.getLogger('run_microgrid.auctioneer')


class Auctioneer(Agent):
    """ Pay as Clear auction market is created here"""
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        auction_log.info('auction of type %s created', _unique_id)
        self.model = model
        self.wallet = Wallet(_unique_id)

        self.snapshot_plot = False
        self.snapshot_plot_interval = 15

        self.id = _unique_id
        self.pricing_rule = self.model.data.pricing_rule
        self.aggregate_demand_curve = []
        self.aggregate_supply_curve = []

        self.bid_list = []
        self.offer_list = []
        self.utility_market_maker_rate = 10

        self.sorted_bid_list = None
        self.sorted_offer_list = None
        self.clearing_quantity = None
        self.clearing_price = None
        self.trade_pairs = None

        self.percentage_sellers = None
        self.percentage_buyers = None
        self.percentage_passive = None

        self.who_gets_what_dict = []

    def auction_round(self):
        """check whether all agents have submitted their bids"""
        self.user_participation()

        """ resets the acquired energy for all households """
        self.who_gets_what_dict = {}
        for agent_id in self.model.agents:
            self.who_gets_what_dict[agent_id] = []

        def empty(seq):
            try:
                return all(map(empty, seq))
            except TypeError:
                return False

        if empty(self.offer_list) is False and empty(self.bid_list) is False:
            """ only proceed to auction if there is demand and supply (i.e. supply in the form of
            prosumers or utility grid) 
            """
            self.sorted_bid_list, self.sorted_offer_list, sorted_x_y_y_pairs_list = self.sorting()
            self.execute_auction(sorted_x_y_y_pairs_list)

            if self.trade_pairs:
                self.clearing_of_market()
            else:
                auction_log.warning("no trade at this step")
                """ clear lists for later use in next step """
                self.bid_list = []
                self.offer_list = []
                return

            """ clear lists for later use in next step """
            self.bid_list = []
            self.offer_list = []
            return

        else:
            """ clear lists for later use in next step """
            self.bid_list = []
            self.offer_list = []
            auction_log.warning("no trade at this step")
            return

    @staticmethod
    def market_rules(sorted_x_y_y_pairs_list):
        # No zero volume trade pairs and no self-trades
        # TODO: find the source of zero volume bids and self-trades and fix it there!
        sorted_x_y_y_pairs_list[:] = [segment for segment in sorted_x_y_y_pairs_list
                                      if
                                      segment[3] != segment[4]
                                      and
                                      segment[0] != 0]

        # assert success of market rule filtering
        for segment in sorted_x_y_y_pairs_list:
            # agents buying from themselves; this should, rationally, never happen!!!
            assert segment[3] != segment[4]
            assert segment[0] != 0

        return sorted_x_y_y_pairs_list

    def execute_auction(self, sorted_x_y_y_pairs_list):
        """ auctioneer sets up the market and clears it according pricing rule """

        check_demand_supply(self.sorted_bid_list, self.sorted_offer_list)

        self.trade_pairs = None
        self.clearing_quantity = None
        self.clearing_price = None

        # filter sorted_x_y_y_pairs_list for market anomalies (to be added in the future)
        sorted_x_y_y_pairs_list = self.market_rules(sorted_x_y_y_pairs_list)

        """ picks pricing rule and generates trade_pairs"""
        if self.pricing_rule == 'pab':
            self.clearing_quantity, self.clearing_price, total_turnover, self.trade_pairs = \
                pab_pricing(sorted_x_y_y_pairs_list)
            # print(f"Clearing rate was (on average): {self.clearing_price} [EUR/kWh]")
            # print(f"Clearing volume was: {self.clearing_quantity} [kWh]")
            auction_log.info("Clearing quantity %f, avg price %f, total turnover is %f",
                             self.clearing_quantity, self.clearing_price,  total_turnover)

        elif self.pricing_rule == 'pac':
            self.clearing_quantity, self.clearing_price, total_turnover, self.trade_pairs = \
                pac_pricing(sorted_x_y_y_pairs_list)
            # print(f"Clearing rate was: {self.clearing_price} [EUR/kWh]")
            # print(f"Clearing volume was: {self.clearing_quantity} [kWh]")
            auction_log.info("Clearing quantity %f, price %f, total turnover is %f",
                             self.clearing_quantity, self.clearing_price, total_turnover)

        elif self.pricing_rule == 'mcafee':
            self.clearing_quantity, self.clearing_price, total_turnover, self.trade_pairs = \
                mcafee_pricing(sorted_x_y_y_pairs_list)
            # print(f"Clearing rate was (on average): {self.clearing_price} [EUR/kWh]")
            # print(f"Clearing volume was: {self.clearing_quantity} [kWh]")
            auction_log.info("Clearing quantity %f, price %f, total turnover is %f",
                             self.clearing_quantity, self.clearing_price, total_turnover)

        # Make snapshot of market clearing for market analysis
        if self.snapshot_plot is True and self.model.step_count % self.snapshot_plot_interval == 0:
            clearing_snapshot(self.clearing_quantity, self.clearing_price, sorted_x_y_y_pairs_list)

        if self.trade_pairs:
            list_of_buying_prices = [trade[-1] for trade in self.trade_pairs]

            try:
                average_clearing_price = sum(list_of_buying_prices) / len(list_of_buying_prices)
                clearing_price_min_avg_max = [min(list_of_buying_prices), average_clearing_price,
                                              max(list_of_buying_prices)]
            except TypeError:
                list_combined_price_pairs = [sum(price_pair) / len(price_pair) for price_pair in list_of_buying_prices]
                average_clearing_price = sum(list_combined_price_pairs) / len(list_combined_price_pairs)
                clearing_price_min_avg_max = [min(list_combined_price_pairs), average_clearing_price,
                                              max(list_combined_price_pairs)]
        else:
            # clearing_price_min_avg_max = [None, None, None]
            auction_log.warning("no trade pairs found by market mechanism at this step")
            # print("no trade pairs found by market mechanism at this step")

            return

        # Save "clearing_quantity, clearing_price, sorted_x_y_y_pairs_list" in an export file, to plots afterwards
        # Update track values for later plots and evaluation.
        self.model.data.clearing_price_min_avg_max[self.model.step_count] = clearing_price_min_avg_max
        self.model.data.clearing_quantity[self.model.step_count] = self.clearing_quantity

        # Track the demand of all households
        household_demand = 0.0
        for agent in self.model.agents:
            if type(self.model.agents[agent]).__name__ == 'HouseholdAgent':
                household_demand += self.model.agents[agent].load_data[self.model.step_count]
        self.model.data.household_demand[self.model.step_count] = household_demand

        # print(f"bids [price, quantity, id]: {self.sorted_bid_list}")
        # print(f"offers [price, quantity, id]: {self.sorted_offer_list}")
        # print(f"trade_pairs [id_seller, id_buyer, quantity, price*quantity]: {self.trade_pairs}")


    def sorting(self):
        """sorts bids and offers into an aggregated demand/supply curve"""

        # TODO: when ALL supply falls (far) under demand price, all supply is of course matched by pricing rule??
        # this creates a bug, which I currently avoid by breaking the sequence. But should be fixed
        # source of the bug is at the sorting algorithm, should allow a clearing also when supply completely falls
        # BELOW demand curve

        # sort on price, not quantity, so location[0]
        # print(self.bid_list)

        for bid in self.bid_list:
            if len(bid) is 0:
                self.bid_list.remove(bid)

        for offer in self.offer_list:
            if len(offer) is 0:
                self.offer_list.remove(offer)

        # print(self.bid_list)

        # bid = (price, quantity, id)
        sorted_bid_list = sorted(self.bid_list, key=lambda location: location[0], reverse=True)
        try:
            sorted_offer_list = sorted(self.offer_list, key=lambda location: location[0])
        except TypeError:
            pass

        # if self.model.data.utility_presence is not None:
        #     """ append (in a clever, semi-aesthetic way) the utility offer to the offer list according to the
        #         utility_market_maker_rate """
        #     sorted_bid_list, sorted_offer_list = self.append_utility_offer(sorted_bid_list, sorted_offer_list)

        # creation of aggregate supply/demand points
        aggregate_quantity_points = []

        aggregate_quantity_points_bid = []
        aggregate_quantity_points_offer = []

        x_y_y_pairs_list = []
        x_bid_pairs_list = []
        x_supply_pairs_list = []

        """ appending bid quantities to aggregate demand and supply curve, effort to make curves overlap """
        # start with construction of x-axis, starting at 0.
        prev = 0
        for i in range(len(sorted_bid_list)):
            # append bid quantity to aggregate demand/supply curve;
            # first create x-axis of curve
            aggregate_quantity_points_bid.append(sorted_bid_list[i][1])
            # move on this x-axis of curve for next item to be appended
            aggregate_quantity_points_bid[i] += prev
            prev = aggregate_quantity_points_bid[i]
            # append bid item to main bid curve: [x-axis location, bid price, offer quantity, buyer id, seller id]
            x_bid_pairs_list.append([aggregate_quantity_points_bid[i],
                                     sorted_bid_list[i][0], None,
                                     sorted_bid_list[i][2], None])

        """ appending offer quantities to aggregate demand and supply curve, effort to make curves overlap """
        # continuing where we left of while appending the bids on the x-axis.
        prev = 0
        for j in range(len(sorted_offer_list)):
            # append offer quantity to aggregate demand/supply curve
            aggregate_quantity_points_offer.append(sorted_offer_list[j][1])
            # move on this x-axis of curve for next item to be appended
            aggregate_quantity_points_offer[j] += prev
            prev = aggregate_quantity_points_offer[j]
            # append offer item to main bid curve: [x-axis location, bid quantity, offer price, buyer id, seller id]
            x_supply_pairs_list.append([aggregate_quantity_points_offer[j],
                                        None, sorted_offer_list[j][0],
                                        None, sorted_offer_list[j][2]])

        x_y_y_pairs_list.extend(x_bid_pairs_list)
        x_y_y_pairs_list.extend(x_supply_pairs_list)

        """sorted_x_y_y_pairs_list[agents][quantity_point, bid_price, offer_price]"""
        sorted_x_y_y_pairs_list = sorted(x_y_y_pairs_list, key=lambda l: l[0])

        # stupid comprehension proxy begins here...
        bid_list_proxy = []
        offer_list_proxy = []
        for i in range(len(sorted_x_y_y_pairs_list)):
            bid_list_proxy.append(sorted_x_y_y_pairs_list[i][1])
            offer_list_proxy.append(sorted_x_y_y_pairs_list[i][2])
        # stupid comprehension proxy stops here...

        # the sorted_x_x_y_pairs_list contains all bids and offers ordered by trade volume on x-axis
        # now, bids are linked to offers, searching for the next offer to be linked to it previous bid
        for segment in range(len(sorted_x_y_y_pairs_list)):
            j = 1
            _offer_list_proxy = offer_list_proxy[segment:]
            # this check "if offer_price_proxy is not empty", is pretty redundant
            if not all(offer_price is None for offer_price in _offer_list_proxy):
                # find next offer in line: run through sorted_x_x_y_pairs_list
                # starting from current quantity
                while sorted_x_y_y_pairs_list[segment][2] is None:
                    # if current selected quantity block is an offer
                    if sorted_x_y_y_pairs_list[segment+j][2] is not None:
                        # then the current selected quantity (which is a bid) is linked to this offer
                        # since sorted_x_x_y_pairs_list is sorted on
                        sorted_x_y_y_pairs_list[segment][2] = sorted_x_y_y_pairs_list[segment+j][2]
                        sorted_x_y_y_pairs_list[segment][4] = sorted_x_y_y_pairs_list[segment+j][4]
                    else:
                        j += 1
            else:
                break

        for segment in range(len(sorted_x_y_y_pairs_list)):
            j = 1
            _bid_list_proxy = bid_list_proxy[segment:]
            # this check "if bid_price_proxy is not empty", is pretty redundant
            if not all(v is None for v in _bid_list_proxy):
                #
                while sorted_x_y_y_pairs_list[segment][1] is None:
                    if sorted_x_y_y_pairs_list[segment+j][1] is not None:
                        sorted_x_y_y_pairs_list[segment][1] = sorted_x_y_y_pairs_list[segment+j][1]
                        sorted_x_y_y_pairs_list[segment][3] = sorted_x_y_y_pairs_list[segment+j][3]

                    else:
                        j += 1
            else:
                break

        return sorted_bid_list, sorted_offer_list, sorted_x_y_y_pairs_list

    def clearing_of_market(self):
        """clears market """
        def who_gets_what_bb(_id_seller, _id_buyer, _trade_quantity, _turnover):
            """ execute trade buy calling household agent's wallet settlement """
            # Settlement of seller revenue if market is budget balanced
            # Is this if statement necessary?
            assert _id_seller != _id_buyer

            self.who_gets_what_dict[_id_seller].append(-_trade_quantity)
            self.model.agents[_id_seller].wallet.settle_revenue(_turnover, self.model.step_count)

            # Settlement of buyer payments
            self.who_gets_what_dict[_id_buyer].append(_trade_quantity)
            self.model.agents[_id_buyer].wallet.settle_payment(_turnover, self.model.step_count)

        def who_gets_what_not_bb(_id_seller, _id_buyer, _trade_quantity, _trade_payment):
            """ execute trade buy calling household agent's wallet settlement """
            # Settlement of seller revenue if market is NOT budget balanced
            trade_revenue_seller, trade_payment_buyer = _trade_payment
            assert trade_payment_buyer >= trade_revenue_seller
            assert _id_seller != _id_buyer
            clearing_imbalance = trade_payment_buyer - trade_revenue_seller

            self.who_gets_what_dict[_id_seller].append(-_trade_quantity)
            self.who_gets_what_dict[_id_buyer].append(_trade_quantity)

            self.model.agents[_id_seller].wallet.settle_revenue(trade_revenue_seller, self.model.step_count)
            self.model.agents[_id_buyer].wallet.settle_payment(trade_payment_buyer, self.model.step_count)

            # tokens to be burned according to McAfee budget imbalance
            self.model.auction.wallet.settle_revenue(clearing_imbalance, self.model.step_count)

        """ listing of all offers/bids selected for trade """
        if self.trade_pairs is not None and self.pricing_rule in ['pac', 'pab']:
            assert np.shape(self.trade_pairs)[1] is 5
            for trade in range(len(self.trade_pairs)):
                # data structure: [seller_id, buyer_id, trade_quantity, turnover, rate]
                id_seller = self.trade_pairs[trade][0]
                id_buyer = self.trade_pairs[trade][1]
                trade_quantity = self.trade_pairs[trade][2]
                turnover = self.trade_pairs[trade][3]
                who_gets_what_bb(id_seller, id_buyer, trade_quantity, turnover)

        elif self.trade_pairs is not None and self.pricing_rule in ['mcafee']:
            # Mcafee pricing settlement
            try:
                # check whether trade_pairs elements contain 5 components
                # this will check in case the mcafee clearing is budget balanced
                assert len(self.trade_pairs) > 0
                assert np.shape(self.trade_pairs)[1] is 6
            except ValueError:
                # and this checks whether the 5th element is a list of two values
                # in case budget imbalanced; 5th element list are payments of both seller or buyer
                assert len(self.trade_pairs[0][4]) is 2

            for trade in range(len(self.trade_pairs)):
                id_seller = self.trade_pairs[trade][0]
                id_buyer = self.trade_pairs[trade][1]
                trade_quantity = self.trade_pairs[trade][2]
                budget_balanced = self.trade_pairs[trade][3]
                trade_payment = self.trade_pairs[trade][4]

                if budget_balanced is True:
                    # McAfee pricing settlement if budget balanced
                    # data structure: [seller_id, buyer_id, trade_quantity, budget_balanced, trade_payment]
                    assert np.shape(trade_payment) is ()
                    who_gets_what_bb(id_seller, id_buyer, trade_quantity, trade_payment)
                else:
                    # Mcafee pricing settlement if NOT budget balanced
                    # data structure: [seller_id, buyer_id, trade_quantity, budget_balanced, trade_payment_tuple]
                    assert len(trade_payment) is 2
                    who_gets_what_not_bb(id_seller, id_buyer, trade_quantity, trade_payment)

        else:
            auction_log.warning("Auction clearing did not result in trade at this interval")

        # Should happen inside the agent class
        """ resets the acquired energy for all households """
        for agent_id in self.model.agents:
            self.model.agents[agent_id].energy_trade_flux = 0
        # Should happen inside the agent class

    def user_participation(self):
        """ small analysis on user participation per step"""
        num_selling = 0
        num_buying = 0
        num_undefined = 0

        for agent_id in self.model.agents:
            if self.model.agents[agent_id].trading_state == 'supplying':
                num_selling += 1
            elif self.model.agents[agent_id].trading_state == 'buying':
                num_buying += 1
            else:
                num_undefined += 1
        total_num = num_selling + num_buying + num_undefined

        # assert total_num == self.model.data.num_households

        # TODO: translate this to percentage of households actually capable of selling or buying...
        # of course pure consumers will never be able to trade energy...
        self.percentage_sellers = num_selling / total_num
        self.percentage_buyers = num_buying / total_num
        self.percentage_passive = num_undefined / total_num

    def track_data(self):
        pass