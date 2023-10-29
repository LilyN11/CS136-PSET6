#!/usr/bin/env python

import sys

from gsp import GSP
from util import argmax_index

class Millybudget:
    """Balanced bidding agent"""
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget
        self.rates = []
        self.decay = 0.97
        self.threshold = 0.65

    def initial_bid(self, reserve):
        return self.value / 2


    def slot_info(self, t, history, reserve):
        """Compute the following for each slot, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns list of tuples [(slot_id, min_bid, max_bid)], where
        min_bid is the bid needed to tie the other-agent bid for that slot
        in the last round.  If slot_id = 0, max_bid is 2* min_bid.
        Otherwise, it's the next highest min_bid (so bidding between min_bid
        and max_bid would result in ending up in that slot)
        """
        prev_round = history.round(t-1)
        other_bids = [a_id_b for a_id_b in prev_round.bids if a_id_b[0] != self.id]

        clicks = prev_round.clicks
        def compute(s):
            (min, max) = GSP.bid_range_for_slot(s, clicks, reserve, other_bids)
            if max == None:
                max = 2 * min
            return (s, min, max)
            
        info = list(map(compute, list(range(len(clicks)))))
#        sys.stdout.write("slot info: %s\n" % info)
        return info


    def expected_utils(self, t, history, reserve):
        """
        Figure out the expected utility of bidding such that we win each
        slot, assuming that everyone else keeps their bids constant from
        the previous round.

        returns a list of utilities per slot.
        """
        info = self.slot_info(t, history, reserve)
        utilities = []
        for i in info:
            (slot_id, min_bid, max_bid) = i
            clicks = history.round(t-1).clicks[slot_id]
            utility = clicks * (self.value - min_bid)
            if min_bid != 0:
                self.rates.append(utility / min_bid)
            utilities.append(utility)
        return utilities

    def target_slot(self, t, history, reserve):
        """Figure out the best slot to target, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns (slot_id, min_bid, max_bid), where min_bid is the bid needed to tie
        the other-agent bid for that slot in the last round.  If slot_id = 0,
        max_bid is min_bid * 2
        """
        utilities = self.expected_utils(t, history, reserve)
        i =  argmax_index(utilities)
        info = self.slot_info(t, history, reserve)
        return info[i], utilities[i]

    def bid(self, t, history, reserve):
        # The Balanced bidding strategy (BB) is the strategy for a player j that, given
        # bids b_{-j},
        # - targets the slot s*_j which maximizes his utility, that is,
        # s*_j = argmax_s {clicks_s (v_j - t_s(j))}.
        # - chooses his bid b' for the next round so as to
        # satisfy the following equation:
        # clicks_{s*_j} (v_j - t_{s*_j}(j)) = clicks_{s*_j-1}(v_j - b')
        # (p_x is the price/click in slot x)
        # If s*_j is the top slot, bid the value v_j

        prev_round = history.round(t-1)
        (slot, min_bid, _max_bid), utility = self.target_slot(t, history, reserve)

        ###########
        if min_bid == 0:
            pass
        elif utility / min_bid <= sorted(self.rates)[int(len(self.rates) * self.threshold)]:
            return min(self.value, min_bid)
        self.threshold *= self.decay
        ###########

        if slot == 0:
            return self.value
        
        clicks_target = prev_round.clicks[slot]
        clicks_above = prev_round.clicks[slot - 1]
        
        bid = self.value - (clicks_target * (self.value - min_bid)) / clicks_above

        # bid *= self.bump
        # bid = 0.8*(min_bid+_max_bid)
        
        return bid

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)


