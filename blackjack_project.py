# -*- coding: utf-8 -*-
"""
@author: Kevin Stone
Simulation and analysis of Blackjack strategies
for GATech ISyE6644 Fall 2021 Course Project
"""

import pandas as pd
import random
import copy
import time
import plotly.graph_objects as go
import plotly.figure_factory as ff
import numpy as np
import streamlit as st

def strat_loader(role,H17,hard=0,soft=0,split=0,custom_file=None):
    #Load in dealer and optimal strategies for the two major variations
    if H17:
        HS17 = 'H'
    else:
        HS17 = 'S'
    dealer_strat = pd.ExcelFile(f'Strategies/strategy_dealer_{HS17}17.xlsx')
    optimal_strat = pd.ExcelFile(f'Strategies/strategy_optimal_{HS17}17.xlsx')
    #Load player strategies from CSV decision tables
    if role == 'Dealer':
        hard_strategy = pd.read_excel(dealer_strat, 'hard').set_index('Player')
        soft_strategy = pd.read_excel(dealer_strat, 'soft').set_index('Player')
        split_strategy = pd.read_excel(dealer_strat, 'split').set_index('Player')
    if custom_file is not None:
        hard_strategy = pd.read_excel(custom_file, 'hard').set_index('Player')
        soft_strategy = pd.read_excel(custom_file, 'soft').set_index('Player')
        split_strategy = pd.read_excel(custom_file, 'split').set_index('Player')
    else:
        if hard:
            hard_strategy = pd.read_excel(optimal_strat, 'hard').set_index('Player')      
        else:
            hard_strategy = pd.read_excel(dealer_strat, 'hard').set_index('Player')     
        if soft:
            soft_strategy = pd.read_excel(optimal_strat, 'soft').set_index('Player')
        else:
            soft_strategy = pd.read_excel(dealer_strat, 'soft').set_index('Player')
        if split:
            split_strategy = pd.read_excel(optimal_strat, 'split').set_index('Player')
        else:
            split_strategy = pd.read_excel(dealer_strat, 'split').set_index('Player')
    return (hard_strategy, soft_strategy, split_strategy)

def calc_sum(cards):
    cardsum = sum(cards)
    ace_high = cards.count(11)
    while cardsum > 21 and ace_high > 0:
        cardsum -= 10
        ace_high -= 1
    return cardsum

class Deck:
    def __init__(self, n_decks):
        #Create N 52-card decks
        cards = [val for val in range(2,10)] + [10]*4 + [11]
        self.cards = cards*4*n_decks
        self.discard = [] #Discard pile for played cards between shuffles
        self.shuffle()
        return

    def shuffle(self):
        #Recombine the deck and shuffle
        for card in self.discard:
            self.cards.append(card)
        self.discard = []
        random.shuffle(self.cards)
        return
    
    def deal(self,hand):
        #Deal 1 card to the hand
        hand['Cards'].append(self.cards[0])
        self.cards.pop(0)
        return

class Player:
    def __init__(self,ID,role,name,strat,game_rules):
        #Store basic information
        self.ID = ID
        self.role = role
        self.name = name
        self.strat = strat
        
        for rule in game_rules.keys():
            setattr(self, rule, game_rules[rule])
        
        self.hands=[]
        self.bank = 0
        custom_file = None
        if 'Custom' in strat.keys():
            custom_file = strat['Custom']
        self.strat_hard, self.strat_soft, self.strat_split = strat_loader(self.role,self.H17,strat['Hard'],strat['Soft'],strat['Split'],custom_file)
        return
    
    def decide(self,upcard):
        actions = []
        for hand in self.hands:           
            if hand['Action'] not in ['Stand','Surrender']:
                action = None
                cards = hand['Cards']
                player_sum = calc_sum(cards)
                
                #Special rules
                max_splits = self.MaxSplits
                DDAS = self.DDAS #Double after split
                
                allow_double = True
                if not DDAS and len(self.hands)>1:
                    allow_double = False
                if len(cards)>2:
                    allow_double = False
                if not self.strat['Double']:
                    allow_double = False
                    
                allow_surrender = True
                if not self.strat['Surrender']:
                    allow_surrender = False
                if len(cards)>2  or len(self.hands)>1: #Late surrender
                    allow_surrender = False
                
                allow_split = True
                if len(self.hands)>max_splits:
                    allow_split = False
                if cards[0]==11 and hand['Order']>0 and not self.ResplitAA: #If resplitting aces is not allowed
                    allow_split = False
                

                if len(cards)==2 and cards[0]==cards[1] and allow_split:
                    action = self.strat_split.loc[cards[0], f'Dealer{upcard}']
                elif 11 in cards:
                    ace_index = cards.index(11)
                    cards.remove(11)
                    ace_count = cards.count(11)
                    soft_sum = sum(cards)
                    soft_sum -= 10*ace_count
                    if soft_sum < 10:
                        action = self.strat_soft.loc[soft_sum, f'Dealer{upcard}']
                    cards.insert(ace_index,11)
                    
                if action in [None, 'No Split'] and player_sum <= 21:
                    action = self.strat_hard.loc[player_sum, f'Dealer{upcard}']
                    
                if action == None and player_sum >= 21:
                    action = 'Stand'
                              
                action_replacements = {'DoubleH':'Hit','DoubleS':'Stand','SurrenderH':'Hit','SurrenderS':'Stand',
                                       'SplitH':'Hit','SurrenderSplit':'Split'}
                
                if 'Double' in action:
                    if not allow_double:
                        action = action_replacements[action]
                    else:
                        action = 'Double'
                if 'Surrender' in action:
                    if not allow_surrender:
                        action = action_replacements[action]
                    else:
                        action = 'Surrender'
                if 'Split' in action:
                    if not allow_split:
                        action = action_replacements[action]
                    else:
                        action = 'Split'
                
                hand['Action'] = action
            actions.append(hand['Action'])
        return actions
    
class Game:
    def __init__(self,options):
        #Store all of the options as class attributes
        for key in options.keys():
            setattr(self, key, options[key])
        
        #Get ready to store hand results
        self.record_keeper = []
        self.house_bank= 0
        
        rules_to_extract = ['H17','DDAS','HitAASplit','ResplitAA','MaxSplits']
        game_rules = {rule: options[rule] for rule in rules_to_extract}
        
        #Generate each player, with given strategy, as required
        self.players = []
        for p_ in range(self.player_count):
            self.players.append(Player(p_+1,'Guest',self.player_names[p_],self.player_strat[p_],game_rules))
            
        self.players.append(Player(self.player_count+1,'Dealer','Dale',{'Hard':0,'Soft':0,'Split':0,'Double':0,'Surrender':0},game_rules))
            
        #Generate the shoe
        self.deck = Deck(self.decks_per_shoe)
        return
    
    def play(self):
        sim_prog = st.progress(0)
        for h in range(self.hands):
            if (h+1)%1000==0:
                print(f'Hand # {h+1}')
            #Repeat these steps every hand
            sim_prog.progress((h+1)/self.hands)
            
            #Step 1: Shuffle if necessary
            if len(self.deck.discard)>self.cut_in*52:
                self.deck.shuffle()
                
            #Step 2: Dealer two cards to each player, dealer last each time
            for player in self.players:
                player.hands.append({'Order':0,'Cards':[],'Action':None,'Double':False})
            for initial_card in range(2):
                for player in self.players:
                    self.deck.deal(player.hands[0])
            
            #Step 3: Assess the upcard and hole card
            upcard = self.players[-1].hands[0]['Cards'][0]
            holecard = self.players[-1].hands[0]['Cards'][1]
            
            #Step 4: Immediately after deal, check to see if dealer has natural blackjack
            if upcard+holecard == 21:
                self.resolve(h)
            else:            
                #Step 5: One player at a time, let each make decisions until all hands stand (or bust)
                for player in self.players:
                    if player.hands[0]['Action'] is None: #We may pass a first action in a testing script
                        actions = player.decide(upcard)
                    while not all(item in ['Stand','Surrender'] for item in actions):
                        self.act(player,actions)
                        actions = player.decide(upcard)
                #Last Step:
                self.resolve(h)
        self.record_keeper = pd.DataFrame(self.record_keeper)
        sim_prog.empty()
        return
    
        
    def act(self,player,actions):
        for h,action in enumerate(actions):
            if action == 'Hit':
                self.deck.deal(player.hands[h])
            if action == 'Double':
                self.deck.deal(player.hands[h])
                player.hands[h]['Double'] = True
                player.hands[h]['Action'] = 'Stand'
            if action == 'Split':
                h_len = len(player.hands)
                player.hands.append({'Order':h_len,'Cards':[],'Action':None,'Double':False})
                player.hands[-1]['Cards'].append(player.hands[h]['Cards'][0])
                player.hands[h]['Cards'].pop(0)
                self.deck.deal(player.hands[h])
                self.deck.deal(player.hands[-1])
                if player.hands[h]['Cards'][0]==11 and not self.HitAASplit: #If we can't re-hit split aces
                    player.hands[-1]['Action'] = 'Stand'
                    player.hands[h]['Action'] = 'Stand'
        return
    
    def resolve(self, h, ignore_record=False):
        #Outcome-Value Relationships
        values = {'Beat':-1,'Bust':-1,'Dealer Blackjack':-1,
                  'Surrender':-0.5,
                  'Push':0,
                  'Win':1,'Dealer Bust':1,
                  'Blackjack':self.blackjack}
        
        outcomes = []
        dvalues = []
        for player in self.players:
            for hand in player.hands:
                #Check the result and store all of the details in a record
                record = {'Simulation Hand Number':h, 'Player ID':player.ID, 'Player Name':player.name, 'Player Role':player.role,
                          'Player Hand Number':hand['Order'], 'Cards':hand['Cards']}
                player_sum = calc_sum(hand['Cards'])
                record['Player Sum'] = player_sum
                record['Dealer Upcard'] = self.players[-1].hands[0]['Cards'][0]
                record['Dealer Cards'] = self.players[-1].hands[0]['Cards']
                dealer_sum = calc_sum(self.players[-1].hands[0]['Cards'])
                record['Dealer Sum'] = dealer_sum
                dealer_ncards = len(self.players[-1].hands[0]['Cards'])
                player_ncards = len(hand['Cards'])
                
                if (dealer_sum == 21 and dealer_ncards == 2) and not (player_sum == 21 and player_ncards == 2 and hand['Order']==0):
                    outcome = 'Dealer Blackjack'
                elif (player_sum == 21 and player_ncards == 2 and hand['Order']==0) and not (dealer_sum == 21 and dealer_ncards == 2):
                    outcome = 'Blackjack'
                elif player_sum > 21:
                    outcome = 'Bust'
                elif hand['Action']=='Surrender':
                    outcome = 'Surrender'
                elif dealer_sum > 21 and player_sum <= 21:
                    outcome = 'Dealer Bust'
                elif dealer_sum <= 21 and player_sum <= 21:
                    if player_sum > dealer_sum:
                        outcome = 'Win'
                    elif dealer_sum > player_sum:
                        outcome = 'Beat'
                    elif dealer_sum == player_sum:
                        outcome = 'Push'
                    else:
                        outcome = 'Error'
                else:
                    outcome = 'Error'
                
                assert outcome != 'Error'
                
                record['Double'] = hand['Double']
                record['Outcome'] = outcome
                outcomes.append(outcome)
                
                dvalue = values[outcome]*(2**hand['Double'])
                record['dValue'] = dvalue
                player.bank += dvalue
                dvalues.append(dvalue)
                record['Player Bank'] = player.bank
                
                if player.role != 'Dealer' and not ignore_record:
                    self.record_keeper.append(record)
                
                #Collect all of the cards into the discard pile
                for card in hand['Cards']:
                    self.deck.discard.append(card)
            player.hands = []
        return dvalues, outcomes

    def score(self):
        #Assemble a table of player statistics from the game's record keeper
        stats = self.record_keeper[self.record_keeper['Player Role']!='Dealer']
        stats = stats.groupby(by=['Player ID','Outcome','Double']).size().reset_index(name='Count')
        stats['Frequency'] = 0
        for p_ in range(1,self.player_count+1):
            stats.loc[stats['Player ID']==p_,'Frequency'] = stats.query(f'`Player ID`=={p_}').loc[:,'Count']/stats.query(f'`Player ID`=={p_}').loc[:,'Count'].sum()
        
        #Calculate house edges per player
        edges = []
        for player in self.players:
            if player.role != 'Dealer':
                edge = {'Player ID':player.ID}
                value = self.record_keeper.query(f'`Player ID`=={player.ID}').iloc[-1,:]['Player Bank']
                edge['House Edge (%)'] = -(value/self.hands)*100
                edges.append(edge)
        edges = pd.DataFrame(edges).set_index('Player ID')
        stats = stats.set_index('Player ID')

        return stats, edges
    
    def value_actions(self, upcard, cards, ID, iterations):
        #Determine the expected value for an action given the player and dealer cards through simulation 
        test_actions = ['Hit','Stand','Double']
        if cards[0]==cards[1]:
            test_actions.append('Split')
        #Use the selected player's test_actions for anything that follow the first, fixed action (i.e. in case of split or re-hit)
        test_players = [self.players[ID-1], self.players[-1]]
       
        #Use dealer strategy after first action
        test_players[0].strat_hard = test_players[1].strat_hard
        test_players[0].strat_soft = test_players[1].strat_soft
        test_players[0].strat_split = test_players[1].strat_split
       
        values = {}
        results = {}
        summary = {}
        for action in test_actions:
            values[action] = [] #Collect a list of results, and we'll get mean and var from Numpy later
            summary[action] = {}
            results[action] = []
        
        optimizer_prog = st.progress(0)
        for action in test_actions:
            multiplier = test_actions.index(action)
            for i_ in range(iterations):
                optimizer_prog.progress((iterations*multiplier+i_++1)/(iterations*4))               
                #Give the chosen cards out
                test_players[0].hands.append({'Order':0,'Cards':cards.copy(),'Action':action,'Double':False})
                
                test_players[-1].hands.append({'Order':0,'Cards':[],'Action':None,'Double':False})
                test_players[-1].hands[0]['Cards'].append(upcard)
                self.deck.deal(test_players[-1].hands[0])

                player_sum = calc_sum(test_players[0].hands[0]['Cards'])

                #Need to correct for dealer blackjack
                for player in test_players:
                    if player.hands[0]['Action'] is None:
                        actions = player.decide(upcard)
                    else:
                        actions = [action]
                    while not all(item in ['Stand','Surrender'] for item in actions):
                        self.act(player,actions)
                        actions = player.decide(upcard)
                
                #Last Step:
                dvalues, outcomes = self.resolve(i_, ignore_record=True)
                if outcomes[0] in ['Dealer Blackjack', 'Blackjack']:
                    continue #No actions to decide on in these cases, so don't bother aggregating

                values[action].append(dvalues[0])
                results[action].append(outcomes[0])

                self.deck = Deck(self.decks_per_shoe)
            
            summary[action]['Mean'] = np.mean(np.array(values[action]))
            summary[action]['Variance'] = np.var(np.array(values[action]))
            results[action] = pd.Series(results[action])
            results[action] = results[action].groupby(results[action]).size()/len(results[action]) #Convert list of actions to a value-grouped Pd Series
        
        results = pd.DataFrame(results).reset_index()
        results = pd.melt(results, id_vars = 'index', value_vars=test_actions)
        results = results.rename(columns={"index": "Outcome", "variable": "First Action", "value":"Frequency"})
        
        summary = pd.DataFrame(summary)
        optimizer_prog.empty()
        return summary, values, results
                
def batch_means(game,batch_size):
    #Assembles a figure for the probability mass function (PMF) of bet outcomes
    #and a corresponding cumulative distribution function (CDF)
    records = game.record_keeper
    batch_means = []
    batch_vars = []
    dist_data = []
    dist_labels = []
    
    fig_ecdf = go.Figure()
    fig_pmf = go.Figure()
    
    run_p = []
    pdf_p = []    
    ecdf_p = []
    value_set = set()

    for p_,player in enumerate(game.players[:-1]):
        run_p.append(records[(records['Player ID']==player.ID)&(records['Simulation Hand Number']%batch_size==0)][['Simulation Hand Number','Player ID','Player Bank']])
        run_p[p_]['dV'] = run_p[p_]['Player Bank'] - run_p[p_].shift(1)['Player Bank']
        run_p[p_] = run_p[p_].dropna()
        pdf_p.append(run_p[p_].groupby(by=['dV']).size().reset_index(name='Freq'))
        batches = len(run_p[p_].index)
        pdf_p[p_]['Freq'] = pdf_p[p_]['Freq']/batches #Normalize to frequency
        value_set = value_set.union(run_p[p_]['dV'])
    
    for p_,player in enumerate(game.players[:-1]):
        ecdf_p.append(pd.DataFrame())
        for step in value_set:
            if step not in list(pdf_p[p_]['dV']):
                pdf_p[p_] = pdf_p[p_].append({'dV': step, 'Freq':0}, ignore_index=True)
            cumsum = pdf_p[p_][pdf_p[p_]['dV']>=step]['Freq'].sum()
            ecdf_p[p_] = ecdf_p[p_].append({'dV':step,'CumFreq':cumsum},ignore_index=True)
        
        pdf_p[p_] = pdf_p[p_].sort_values(by=['dV'])
        ecdf_p[p_] = ecdf_p[p_].sort_values(by=['dV'])

        batch_means.append(run_p[p_]['dV'].mean())
        batch_vars.append(run_p[p_]['dV'].var())
        
        label = player.name
        dist_data.append(run_p[p_]['dV'])
        dist_labels.append(label)
        
        fig_ecdf.add_trace(go.Scatter(x=ecdf_p[p_]['dV'],y=ecdf_p[p_]['CumFreq'],name=label))
        fig_pmf.add_trace(go.Scatter(x=pdf_p[p_]['dV'],y=pdf_p[p_]['Freq'],name=label))

    #Edit PDF
    fig_pmf.update_xaxes(title_text='Net Bets Won')
    fig_pmf.update_yaxes(title_text='Probability')
    fig_pmf.update_layout(title_text=f'Probability Mass Function of Return in {batch_size} Hands vs. Player Strategy ')
    
    #Edit eCDF
    fig_ecdf.update_xaxes(title_text='Net Bets Won (Minimum)')
    fig_ecdf.update_yaxes(title_text='Cumulative Probability')
    fig_ecdf.update_layout(title_text=f'Cumulative Distribution Function of Return in {batch_size} Hands vs. Player Strategy')
    return batch_means, batch_vars, fig_pmf, fig_ecdf

def val_over_time(game):
    records = game.record_keeper
    fig = go.Figure()
    for player in game.players[:-1]:
        run_p = records[(records['Player ID']==player.ID)][['Simulation Hand Number','Player ID','Player Bank']]
        label = player.name
        fig.add_trace(go.Scatter(x=run_p['Simulation Hand Number'],y=run_p['Player Bank'],name=label))
    fig.update_xaxes(title_text='Hand No.')
    fig.update_yaxes(title_text='Net Number of Bets Won')
    fig.update_layout(title_text=f'Player Value over Simulation ')
    return fig

def card_heatmap(game, player_ID):
    #Creates a heatmap of realized card values for a particular player in the game
    all_records = game.record_keeper.set_index('Player ID')
    record_p = all_records.loc[player_ID]
    record_p['Card1'] = record_p.apply(lambda x: x['Cards'][0], axis=1)
    record_p['Card2'] = record_p.apply(lambda x: x['Cards'][1], axis=1)
    record_p['Dealer'] = record_p['Dealer Upcard']
    record_p['Value'] = record_p['dValue']
    record_p = record_p[['Outcome','Double','Dealer','Card1','Card2','Value']].reset_index(drop=True)

    
    #Aggregate data for hard-totals (no aces, one cardset at a time)
    hards = record_p[-((record_p['Card1']==11)^(record_p['Card2']==11))]
    hards['HardTotal'] = record_p['Card1']+record_p['Card2']
    #If the player isn't splitting, double aces will show up; don't report this as 22
    if game.players[player_ID-1].strat['Split'] == 1:
        hards.loc[hards['HardTotal']==22,'HardTotal']=12
    hards = hards.groupby(by=['Dealer','HardTotal']).agg({'Value':'mean','Dealer':'count'}).rename(columns={'Value':'AvgValue','Dealer':'Count'}).reset_index()
    #Filter out any significantly under-represented values
    #Dealer card has 11 values, 22 rolls should average 2 each
    hards.loc[hards['Count']<22,'Count']=None

    
    #Aggregate data for soft-totals (one ace, one cardset at a time)
    #Even if the player can't do soft strategy, we want to see how these cards played out
    softs = record_p[(record_p['Card1']==11)^(record_p['Card2']==11)]
    softs['NonAce'] = softs[['Card1','Card2']].min(axis=1)
    softs = softs.groupby(by=['Dealer','NonAce']).agg({'Value':'mean','Dealer':'count'}).rename(columns={'Value':'AvgValue','Dealer':'Count'}).reset_index()
    
    #Plot hard total performance
    fig_hard = go.Figure(data = go.Heatmap(z = hards['AvgValue'],
                                      x = hards['HardTotal'],
                                      y = hards['Dealer'],
                                      zmin = -1,
                                      zmax = 1.5,
                                      colorscale = 'RdBu',
                                      colorbar = {'title':'Average Hand Value'}))
    fig_hard.update_xaxes(title_text='Player Hard Total')
    fig_hard.update_xaxes(side='top')
    fig_hard.update_yaxes(title_text='Dealer UpCard')
    
    #Plot soft total performance
    fig_soft = go.Figure(data = go.Heatmap(z = softs['AvgValue'],
                                      x = softs['NonAce'],
                                      y = softs['Dealer'],
                                      zmin = -1,
                                      zmax = 1.5,
                                      colorscale = 'RdBu',
                                      colorbar = {'title':'Average Hand Value'}))
    fig_soft.update_xaxes(title_text='Player Non-Ace Card in Soft Hand')
    fig_soft.update_xaxes(side='top')
    fig_soft.update_yaxes(title_text='Dealer UpCard')
    
    return fig_hard, fig_soft    
    
    
