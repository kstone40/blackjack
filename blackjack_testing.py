# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 19:29:10 2021

@author: kevin
"""
from blackjack_project_v2 import *
import plotly 

random.seed('6644')
options = {'hands':1000000,
            'player_count':2,
            'player_names':['Kevin','Hannah'],
            'player_strat':[{'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1},
                            {'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1}],
            'decks_per_shoe':8,
            'cut_in':1,
            #'blackjack':1,
            'blackjack':3/2,
            'H17':1}

test_game = Game(options)
test_game.play()
records = test_game.record_keeper
stats, edges = test_game.score()
batch_means_results, batch_vars, fig_pmf, fig_ecdf = batch_means(test_game,20)
#plotly.offline.plot(fig_ecdf)
#plotly.offline.plot(fig_pmf)

fig_val = val_over_time(test_game)
# plotly.offline.plot(fig_val)

fig_hard, fig_soft = card_heatmap(test_game,1)
# plotly.offline.plot(fig_hard)
# plotly.offline.plot(fig_soft)

# test_cards = [8,8]
# test_upcard = 7
# summary, values, results = test_game.value_actions(test_upcard,test_cards,1,1000)