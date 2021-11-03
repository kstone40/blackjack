# -*- coding: utf-8 -*-
"""
@author: Kevin Stone
Simulation and analysis of Blackjack strategies
for GATech ISyE6644 Fall 2021 Course Project
"""
from blackjack_project import *
import plotly 

random.seed('6644')
options = {'hands':1000000,
            # 'player_count':7,
            # 'player_names':['No Rules (Dealer)','Hard Stands','Hard Doubles','Splits','Soft Doubles','Surrenders','Optimal'],
            # 'player_strat':[{'Hard':0, 'Soft':0, 'Split': 0, 'Double':0, 'Surrender':0},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1, 'Custom':'Strategies/strategy_K1.xlsx'},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1, 'Custom':'Strategies/strategy_K2.xlsx'},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1, 'Custom':'Strategies/strategy_K3.xlsx'},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1, 'Custom':'Strategies/strategy_K4.xlsx'},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1, 'Custom':'Strategies/strategy_K5.xlsx'},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1}],
            # 'player_count':1,
            # 'player_names':['Dealer Mimetic'],
            # 'player_strat':[{'Hard':0, 'Soft':0, 'Split': 0, 'Double':0, 'Surrender':0}],
            'player_count':1,
            'player_names':['Optimal'],
            'player_strat':[{'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1}],
            # 'player_count':6,
            # 'player_names':['Dealer Mimetic','Hard Only','Hard/Soft','Hard/Soft/Split','Double Allowed','Surrender Allowed'],
            # 'player_strat':[{'Hard':0, 'Soft':0, 'Split': 0, 'Double':0, 'Surrender':0},
            #                 {'Hard':1, 'Soft':0, 'Split': 0, 'Double':0, 'Surrender':0},
            #                 {'Hard':1, 'Soft':1, 'Split': 0, 'Double':0, 'Surrender':0},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':0, 'Surrender':0},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':0},
            #                 {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1}],
            'decks_per_shoe':6, 'cut_in':4,
            'blackjack':1.5, 'H17':1,
            'DDAS':1, 'HitAASplit':1, 'ResplitAA':1, 'MaxSplits':3}

test_game = Game(options)
test_game.play()
records = test_game.record_keeper
stats, edges = test_game.score()
batch_means_results, batch_vars, fig_pmf, fig_ecdf = batch_means(test_game,20)
# plotly.offline.plot(fig_ecdf)
# plotly.offline.plot(fig_pmf)

fig_val = val_over_time(test_game)
# plotly.offline.plot(fig_val)

fig_hard, fig_soft = card_heatmap(test_game,1)
# plotly.offline.plot(fig_hard)
# plotly.offline.plot(fig_soft)

# test_cards = [10,2]
# test_upcard = 11
# summary, values, results = test_game.value_actions(test_upcard,test_cards,1,1000)