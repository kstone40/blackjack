# -*- coding: utf-8 -*-
"""
@author: Kevin Stone
Simulation and analysis of Blackjack strategies
for GATech ISyE6644 Fall 2021 Course Project

Running and troubleshooting of blackjack_project.py
"""

from blackjack_project import *
import plotly

random.seed('6644')
options = {'hands':100,
            'player_count':1,
            'player_strat':[{'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1}],
            'decks_per_shoe':6,
            'cut_in':4,
            'blackjack':3/2,
            'dealerhitsoft17':1}
my_game = game(options)
my_game.play()
stats, edges = my_game.score()
batch_means_results, batch_vars, fig_pmf, fig_ecdf = batch_means(my_game,20)
fig_hard, fig_soft = card_heatmap(my_game,1)
# plotly.offline.plot(fig_soft)

test_cards = [('Dummy',10),('Dummy',7)]
test_upcard = ('Dummy',10)
summary, values, results = my_game.value_actions(test_upcard,test_cards,1,500)