# -*- coding: utf-8 -*-
"""
Created on Sat Oct 23 16:42:08 2021

@author: kevin
"""
from blackjack_project import *
import plotly.figure_factory as ff
import plotly.graph_objects as go
import plotly


#Set up a game class
random.seed('6644')
options = {'hands':10,
            'player_count':1,
            'player_names':['Kevin'],
            'player_strat':[{'Hard':1, 'Soft':1, 'Split': 1, 'Double':1, 'Surrender':1}],
            'decks_per_shoe':6,
            'cut_in':4,
            'blackjack':3/2,
            'H17':1}
my_game = Game(options)
my_game.play()

#Load in the alternative strategy
dealer_strat_hard = my_game.players[-1].strat_hard
dealer_strat_soft = my_game.players[-1].strat_soft

iterations = 5000

def record_actions(first_cards, second_card_ranges, strategy):
    #Strategy is 'hard' 'soft' or 'split'
    #Generate a list of possible dummy cards
    possible_cards = list(range(2,12))
    records = []
    for upcard in possible_cards:
        for first_card, second_card_range in zip(first_cards, second_card_ranges):
            if strategy == 'split':
                second_card_range = [first_card]
            for second_card in second_card_range:
                record = {}
                player_cards = [first_card, second_card]
                record['Player Cards'] = player_cards
                record['Dealer'] = upcard
                if strategy == 'hard':
                    player_sum = first_card + second_card
                    record['Hard Total'] = player_sum
                    alt_action = dealer_strat_hard.loc[player_sum,f'Dealer{upcard}']
                if strategy == 'soft':
                    record['Soft Other Card'] = second_card
                    alt_action = dealer_strat_soft.loc[second_card,f'Dealer{upcard}']
                if strategy == 'split':
                    record['Split Card'] = second_card
                    if second_card < 11:
                        alt_action = dealer_strat_hard.loc[2*second_card,f'Dealer{upcard}']
                    else:
                        alt_action = dealer_strat_hard.loc[12,f'Dealer{upcard}']
                summary, values, results = my_game.value_actions(upcard,player_cards,1,iterations)    
                record['Alt Action'] = alt_action
                alt_action_value = summary[alt_action]['Mean']
                record['Alt Action Value'] = alt_action_value
                best_action = summary.idxmax(axis = 1)['Mean']
                best_action_value = summary[best_action]['Mean']
                if best_action_value < -0.5:
                    best_action = 'Surrender'
                    best_action_value = -0.5
                record['Best Action'] = best_action
                record['Best Action Value'] = best_action_value
                record['Differential Value'] = best_action_value - alt_action_value
                records.append(record)
                print(record)
    return pd.DataFrame(records)         

first_cards = [2,10]
second_card_ranges = [list(range(3,11)),list(range(3,9))]
records_hard = record_actions(first_cards, second_card_ranges, 'hard')

first_cards = [11]
second_card_ranges = [list(range(2,10))]
records_soft = record_actions(first_cards, second_card_ranges, 'soft')

card_vals = list(range(2,11))
card_vals.append(11)
possible_cards = list(range(2,12))
records_split = record_actions(possible_cards, possible_cards, 'split')

card_probs = pd.read_csv('Card Probabilities.csv', index_col = 0)

records_hard[['Dealer','Player Cards']] = records_hard[['Dealer','Player Cards']].astype('string')
records_soft[['Dealer','Player Cards']] = records_soft[['Dealer','Player Cards']].astype('string')
records_split[['Dealer','Player Cards']] = records_split[['Dealer','Player Cards']].astype('string')

all_comp = records_hard.merge(records_soft, how='outer').merge(records_split, how='outer')
all_comp['Dealer'] = all_comp['Dealer'].astype('int64')

all_comp['Prob'] = 0
for index, row in all_comp.iterrows():
    if row['Hard Total'] > 0:
        all_comp.loc[index,'Prob'] = card_probs['Hard'][row['Hard Total']]*card_probs.loc[row['Dealer'],'Dealer']
    if row['Soft Other Card'] > 0:
        all_comp.loc[index,'Prob'] = card_probs['Soft'][row['Soft Other Card']]*card_probs.loc[row['Dealer'],'Dealer']
    if row['Split Card'] > 0:
        all_comp.loc[index,'Prob'] = card_probs['Split'][row['Split Card']]*card_probs.loc[row['Dealer'],'Dealer']

all_comp['Weighted Value'] = all_comp['Differential Value']*all_comp['Prob']
cols = ['Hard Total','Soft Other Card','Split Card','Player Cards',
        'Dealer','Alt Action','Alt Action Value','Best Action','Best Action Value','Differential Value','Prob','Weighted Value']

type_list = ['Hard Total', 'Soft Other Card', 'Split Card']
for type_i in type_list:
    all_comp_short = all_comp[cols].query(f"`{type_i}` > 0")
    annot_heatmap_x = list(all_comp_short['Dealer'].unique())
    annot_heatmap_y = list(all_comp_short[type_i].unique())
    annot_heatmap_ztext = []
    for col in annot_heatmap_y:
        annot_heatmap_ztext.append(all_comp_short.query(f'`{type_i}`=={col}')['Best Action'].tolist())
    
    fig = go.Figure(data = go.Heatmap(z=all_comp_short['Weighted Value'],
                                          y=all_comp_short[type_i],
                                          x=all_comp_short['Dealer'],
                                          zmin = 0,
                                          zmax = 0.0015,
                                          colorscale = 'GnBu',
                                          colorbar = {'title':'Value'}))
    
    for ix, x in enumerate(annot_heatmap_x):
        for iy, y in enumerate(annot_heatmap_y):
            fig.add_annotation(x=x, y=y,
                        text=annot_heatmap_ztext[iy][ix],
                        showarrow=False,
                        font=dict(#family='Courier New, monospace',
                                  size=10,color="#000000")) #ffffff is white
    fig.update_yaxes(title_text=f'Player {type_i}')
    fig.update_xaxes(side='top')
    fig.update_xaxes(title_text='Dealer UpCard')
    fig.update_layout(yaxis_nticks=len(annot_heatmap_y),
                      xaxis_nticks=len(annot_heatmap_x))
    plotly.offline.plot(fig)
