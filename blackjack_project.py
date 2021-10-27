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

#For local running/troubleshooting, trigger plotting in broser
import plotly.io as pio
pio.renderers.default='browser'

class shoe:
    def __init__(self, decks):
        #Assign card types and values
        card_faces = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        card_values = [2,3,4,5,6,7,8,9,10,10,10,10,[1,11]]
        suits = ['Hearts','Diamonds','Spades','Clubs']
        self.card_dict = {}
        for face,value in zip(card_faces,card_values):
            self.card_dict[face]=value
        #Build a deck based on the suits and card-value dictionary
        deck = []
        for suit in suits:
            for key,value in self.card_dict.items():
                name = key + ' of ' + suit
                deck.append((name, value))
        #Assemble the decks into the shoe, then shuffle
        self.cards = deck*decks #Deck replicates
        self.bin = [] # Used cards
        self.shuffle()
        return
    
    def shuffle(self):
        #Recombine and shuffle the deck
        for card in self.bin:
            self.cards.append(card)
            self.bin.remove(card)
        random.shuffle(self.cards)
        return
          
class player:
    def __init__(self,ID,role,strat,dealerhitsoft17):
        #Store basic player information
        self.ID = ID
        self.role = role
        #Store player cards, will get reset after every hand
        #Cards and their related properties must reflect that a player might have multiple hands
        #(In the case of a split)
        self.cards = [[]]
        self.cardsums = []
        self.surrender = []
        self.double = 0 #Double is a single flag, can only be done on first deal
        #Record bank value
        self.value = 0
        
        #Load in dealer and optimal strategies for the two major variations
        if dealerhitsoft17 == 1:
            char = 'H'
        else:
            char = 'S'
        dealer_strat = pd.ExcelFile(f'Strategies/strategy_dealer_{char}17.xlsx')
        optimal_strat = pd.ExcelFile(f'Strategies/strategy_optimal_{char}17.xlsx')
        
        #Load player strategies from CSV decision tables
        self.strat = strat
        if 'Special' in strat.keys():
            if strat['Special'] == 'Dealer':
                self.hard_strategy = pd.read_excel(dealer_strat, 'hard').set_index('Player')
                self.soft_strategy = pd.read_excel(dealer_strat, 'soft').set_index('Player')
                self.split_strategy = None
            elif strat['Special'] == 'Custom':
                custom_strat = pd.ExcelFile(strat['Path'])
                self.hard_strategy = pd.read_excel(custom_strat, 'hard').set_index('Player')
                self.soft_strategy = pd.read_excel(custom_strat, 'soft').set_index('Player')
                self.split_strategy = pd.read_excel(custom_strat, 'split').set_index('Player')
        else:
            if strat['Hard'] == 0:
                self.hard_strategy = pd.read_excel(dealer_strat, 'hard').set_index('Player')     
            else:
                self.hard_strategy = pd.read_excel(optimal_strat, 'hard').set_index('Player')  
            if strat['Soft'] == 0:
                self.soft_strategy = pd.read_excel(dealer_strat, 'soft').set_index('Player')
            else:
                self.soft_strategy = pd.read_excel(optimal_strat, 'soft').set_index('Player')
            if strat['Split'] == 0:
                self.split_strategy = None
            elif strat['Split'] == 1:
                self.split_strategy = pd.read_excel(optimal_strat, 'split').set_index('Player')
        return
    
    def calc_sum(self,cardset):
        #Add up all of the cards, start with all aces high (11)
        card_sum = 0
        aces_high = 0
        for card in self.cards[cardset]:
            if type(card[1]) is list:
                aces_high += 1
                card_sum += max(card[1])
            else:
                card_sum += card[1]
        #If the count is too high and aces are present, decrease until < 21
        #Same algorithm will apply for both players and dealer
        while aces_high > 0 and card_sum > 21:
            card_sum -= 10
            aces_high -= 1         
        return card_sum
    
    def act(self,upcard,cardset,react):
        
        #Decide what to do based on cards and the dealer card
        #Convert Ace to singular 11 value
        if type(upcard[1]) is list:
            upcard = max(upcard[1])
        else:
            upcard = upcard[1]
        
        #Default action is stand
        action = 'Stand'
        
        #React determines whether or not the player can continue to hit
        if not react:
            action = 'Stand'
        else:
            player_cards = self.cards[cardset]
            
            #First count the aces in the cards
            ace_count = 0
            have_one_ace = False
            for card in range(len(player_cards)):
                if player_cards[card][1] is list:
                    ace_count += 1
            if ace_count>0:
                have_one_ace = True
            
            #If we have at least one ace, calc the sum of the other cards
            if have_one_ace:
                #If we do, what's the SUM of the other cards
                other_card = 0
                for card in range(len(player_cards)):
                    other_card += np.min(player_cards[card][1])
            
            #Start by checking for a potential split
            if player_cards[0][1]==player_cards[1][1] and len(player_cards)==2 and self.split_strategy is not None:
                if type(player_cards[0][1]) is list:
                    double_card = 11
                else:
                    double_card = player_cards[0][1]
                    
                #If we have two cards and they are the same value...
                action = self.split_strategy.loc[double_card,f'Dealer{upcard}']

            #If we don't qualify for a split, check for a soft hand
            elif have_one_ace and other_card < 10:
                action = self.soft_strategy.loc[other_card,f'Dealer{upcard}']
                      
            #If we don't quality for a split or soft, do the hard total
            else:
                card_sum = self.calc_sum(cardset)
                if card_sum >= 21:
                    action = 'Stand'
                else:
                    action = self.hard_strategy.loc[card_sum,f'Dealer{upcard}']
                    
            #Only allow doubling after the dealing of the first 2 cards (any cardset)
            if action in ['DoubleH','DoubleS'] and len(self.cards[cardset])>2:
                if action == 'DoubleH':
                    action = 'Hit'
                else:
                    action = 'Stand'
            
            #Allow doubling after split
            # if action in ['DoubleH','DoubleS'] and len(self.cards)>1:
            #     if action == 'DoubleH':
            #         action = 'Hit'
            #     else:
            #         action = 'Stand'
            
            #Resolve Doubles if if dis-allowed
            if action == 'DoubleH':
                if self.strat['Double'] == 1:
                    action = 'Double'
                else:
                    action = 'Hit'
            if action == 'DoubleS':
                if self.strat['Double'] == 1:
                    action = 'Double'
                else:
                    action = 'Stand'
                    
            #Resolve Surrender if dis-alowed
            if action == 'SurrenderH':
                if self.strat['Surrender'] == 0:
                    action = 'Hit'
                else:
                    action = 'Surrender'
            if action == 'SurrenderS':
                if self.strat['Surrender'] == 0:
                    action = 'Stand'
                else:
                    action = 'Surrender'
            if action == 'SurrenderSplit':
                if self.strat['Surrender'] == 0:
                    if self.split_strategy is not None:
                        action = 'Split'
                    else:
                        action = 'Hit'
                else:
                    action = 'Surrender'
            
            #Resolve conditional splits
            if action == 'SplitH':
                if self.split_strategy is not None:
                    action = 'Split'
                else:
                    action = 'Hit'

        return action

class game:
    def __init__(self,options):
        #Store all of the options as class attributes
        for key in options.keys():
            setattr(self, key, options[key])
        
        #Generate each player, with given strategy, as required
        self.players = []
        for p_ in range(self.player_count):
            self.players.append(player(p_+1,'Guest',self.player_strat[p_],self.dealerhitsoft17))
            
        self.players.append(player(self.player_count+1,'Dealer',{'Special':'Dealer'},self.dealerhitsoft17))
            
        #Generate the shoe
        self.shoe = shoe(self.decks_per_shoe)
        return
    
    def collect(self):
        #Removes all of the cards from every player and adds them to the shoe's discard pile
        for player in self.players:
            for cardset in range(len(player.cards)):
                for card in list(player.cards[cardset]):
                    self.shoe.bin.append(card)
                    player.cards[cardset].remove(card)
            player.cards = [[]]
        return
    
    def deal(self,deck,player,cardset):
        #Deal a single card from the shoe to the player's cardset
        player.cards[cardset].append(deck.cards[0])
        deck.cards.remove(deck.cards[0])
        return
    
    def resolve(self,player,cardset,dealer_sum):
        player_sum = player.calc_sum(cardset)
        
        #Player surrendered
        if player.surrender[cardset]==1:
            result = 'Surrender'
            dvalue = -0.5*(2**player.double)
        #Player gets blackjack
        elif player_sum == 21 and len(player.cards[cardset])==2 and dealer_sum != 21:
            result = 'Blackjack'
            dvalue = self.blackjack
        #Player busts, always a loss
        elif player_sum > 21:
            result = 'Bust'
            dvalue = -2**player.double
        #Dealer busts, player doesn't 
        elif dealer_sum > 21 and player_sum <= 21:
            result = 'DealerBust'
            dvalue = 2**player.double
        #No one busts
        elif dealer_sum <= 21 and player_sum <= 21:
            if player_sum > dealer_sum:
                result = 'Win'
                dvalue = 2**player.double
            elif player_sum == dealer_sum:
                result = 'Push'
                dvalue = 0
            else:
                result = 'Beat'
                dvalue = -2**player.double
      
        return dvalue, result

    def score(self):
        #Assemble a table of player statistics from the game's record keeper
        stats = self.record_keeper[self.record_keeper['Role']!='Dealer']
        stats = stats.groupby(by=['Player','Result','Double']).size().reset_index(name='Count')
        stats['Frequency'] = 0
        for p_ in range(1,self.player_count+1):
            stats.loc[stats['Player']==p_,'Frequency'] = stats.query(f'Player=={p_}').loc[:,'Count']/stats.query(f'Player=={p_}').loc[:,'Count'].sum()
        
        #Calculate house edges per player
        edges = []
        for player in self.players:
            if player.role != 'Dealer':
                edge = {'Player':player.ID}
                value = 0
                player_stats = stats[stats['Player']==player.ID]
                for index,row in player_stats.iterrows():
                    if row['Result'] in ['DealerBust','Win']:
                        value += row['Frequency']*(2**row['Double'])
                    elif row['Result'] in ['Bust','Beat']:
                        value -= row['Frequency']*(2**row['Double'])
                    elif row['Result'] == 'Surrender':
                        value -= 0.5*row['Frequency']*(2**row['Double'])
                    elif row['Result'] == 'Blackjack':
                        value += row['Frequency']*self.blackjack
                edge['House Edge (%)'] = -value*100
                edges.append(edge)
        edges = pd.DataFrame(edges).set_index('Player')
        stats = stats.set_index('Player')

        return stats, edges
    
    def decide(self, player, dealer_card, firstaction=False, action=None):
        #Decide what to do based on player and dealer cards (precedes player.act)
        #If it's the first deal, or there is an active split to be handled
        while 'None' in player.actions:
            for cardset in range(len(player.cards)):
                #Make a decision for each cardset
                if firstaction == True and player.role != 'Dealer':
                    player.actions[cardset] = action
                    firstaction = False
                else:
                    player.actions[cardset] = player.act(dealer_card,cardset,1)
                #HIT: Deal one more card
                while player.actions[cardset] == 'Hit':
                    self.deal(self.shoe,player,cardset)
                    player.actions[cardset]  = player.act(dealer_card,cardset,1)
                #DOUBLE DOWN: Hit, then stop
                if player.actions[cardset] == 'Double':
                    player.double = 1
                    #This will only ever apply to the first 2 cards, no need to worry about splits
                    self.deal(self.shoe,player,cardset)
                    player.actions[cardset] = player.act(dealer_card,cardset,0)
                #SURRENDER: Stop
                if player.actions[cardset] == 'Surrender':
                    player.surrender[cardset] = 1
                #SPLIT: Split current cardset into two cardsets
                if player.actions[cardset] == 'Split':
                    #Take the second card from the current cardset, add it as a new cardset
                    player.cards.append([player.cards[cardset][1]])
                    player.cards[cardset].remove(player.cards[cardset][1])
                    #Splitting demands re-evaluation for each card set
                    player.actions.append('None')
                    player.actions[cardset] == 'None'
                    player.surrender.append([0])
                    max_cardset = len(player.cards)-1
                    self.deal(self.shoe,player,cardset)
                    self.deal(self.shoe,player,max_cardset)

        return
    
    def value_actions(self, dealer_card, cards, ID, iterations):
        #Determine the expected value for an action given the player and dealer cards through simulation 
        actions = ['Hit','Stand','Double']
        if cards[0][1]==cards[1][1]:
            actions.append('Split')
                      
        #Use the selected player's actions for anything that follow the first, fixed action (i.e. in case of split or re-hit)
        test_players = [self.players[ID-1], self.players[-1]]
       
        #Use dealer strategy after first action
        test_players[0].hard_strategy = test_players[1].hard_strategy
        test_players[0].soft_strategy = test_players[1].soft_strategy
        test_players[0].split_strategy = test_players[1].split_strategy
       
        values = {}
        results = {}
        summary = {}
        for action in actions:
            values[action] = [] #Collect a list of results, and we'll get mean and var from Numpy later
            summary[action] = {}
            results[action] = []
        
        optimizer_prog = st.progress(0)
        for action in actions:
            multiplier = actions.index(action)
            for i_ in range(iterations):
                optimizer_prog.progress((iterations*multiplier+i_++1)/(iterations*4))               
 
                
                #NOTE: ISSUE MAY HAVE BEEN THAT YOU WERE REMOVING THE FIRST INSTANCE OF THE MATCHING CARD
                
                # #Remove the chosen cards from the shoe
                # card_values_remove = [cards[0][1], cards[1][1], dealer_card[1]]
                # for card_value in card_values_remove:
                #     i=0
                #     while self.shoe.cards[i][1] != card_value:
                #         i+=1
                #     self.shoe.cards.remove(self.shoe.cards[i])

                #Give the chosen cards out
                for card in cards:
                    test_players[0].cards[0].append(card) 
                
                self.players[-1].cards[0].append(dealer_card)
                self.deal(self.shoe,self.players[-1],0)
                
                player_sum = test_players[0].calc_sum(0)
                
                for player in test_players:
                    #Reset the flag for double down and reset the player decision
                    player.double = 0
                    player.surrender = [0]
                    player.actions = ['None']
                    self.decide(player, dealer_card, firstaction = True, action = action)

                dealer_sum = test_players[1].calc_sum(0) 
                for cardset in range(len(test_players[0].cards)):
                    dvalue, result = self.resolve(test_players[0],cardset,dealer_sum)
                    values[action].append(dvalue)
                    results[action].append(result)
                    
                for player in test_players:
                    player.cards = [[]]
                self.shoe = shoe(self.decks_per_shoe)
                self.shoe.shuffle()
                
            summary[action]['Mean'] = np.mean(np.array(values[action]))
            summary[action]['Variance'] = np.var(np.array(values[action]))
            results[action] = pd.Series(results[action])
            results[action] = results[action].groupby(results[action]).size()/len(results[action]) #Convert list of actions to a value-grouped Pd Series
        
        results = pd.DataFrame(results).reset_index()
        results = pd.melt(results, id_vars = 'index', value_vars=actions)
        results = results.rename(columns={"index": "Outcome", "variable": "First Action", "value":"Frequency"})
        
        summary = pd.DataFrame(summary)
        optimizer_prog.empty()
        return summary, values, results

    def play(self):        
        self.record_keeper = []
        #Repeat the steps for N hands in the simulation
        sim_prog = st.progress(0)
        for hand in range(self.hands):  
            sim_prog.progress((hand+1)/self.hands)
            #STEP 1: Shuffle and deal cards if the cut card is passed
            if len(self.shoe.bin)>self.cut_in*52:
                self.shoe.shuffle()
            
            #STEP 2: Deal 2 cards to each player, one at a time, dealer last
            for card in range(2):
                for player in self.players:
                    self.deal(self.shoe,player,0) 
                    #Reset the flag for double down and reset the player decision
                    player.double = 0
                    player.surrender = [0]
                    player.actions = ['None']
            
            #STEP 3: "Announce" the dealer upcard, the first card dealt to the dealer
            dealer_card = self.players[-1].cards[0][0]
            
            #STEP 4: Each player, dealer last, decides what to do with their hand
            for player in self.players:
                self.decide(player, dealer_card)
            
            #STEP 5: Determine whether each player won or lost and how
            dealer_sum = self.players[-1].calc_sum(0)
            for player in self.players:
                for cardset in range(len(player.cards)):
                    dvalue, result = self.resolve(player,cardset,dealer_sum)
                    player.value += dvalue
                    record = {'Hand':hand,'Cardset':cardset, 'Player':player.ID, 'Role':player.role, 'Value':player.value,
                              'PlayerCards':copy.deepcopy(player.cards), 'DealerUpcard':dealer_card}
                    record['Result'] = result
                    record['Double'] = (player.double==1)
                    #Add the record of this hand/player to the record keeper
                    self.record_keeper.append(record)
                    
            #STEP 6: Collect the cards from each player and put them in the discard pile
            self.collect()
            
        #Once all of the hands have been dealt and resolved, reformat the record keeper
        sim_prog.empty()
        self.record_keeper = pd.DataFrame(self.record_keeper)
        return

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
        run_p.append(records[(records['Player']==player.ID)&(records['Hand']%batch_size==0)][['Hand','Player','Value']])
        run_p[p_]['dV'] = run_p[p_]['Value'] - run_p[p_].shift(1)['Value']
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
        
        label = f'Player {player.ID}'
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
        run_p = records[(records['Player']==player.ID)][['Hand','Player','Value']]
        label = f'Player {player.ID}'
        fig.add_trace(go.Scatter(x=run_p['Hand'],y=run_p['Value'],name=label))
    fig.update_xaxes(title_text='Hand No.')
    fig.update_yaxes(title_text='Net Number of Bets Won')
    fig.update_layout(title_text=f'Player Value over Simulation ')
    return fig

def card_heatmap(game, player_ID):
    #Creates a heatmap of realized card values for a particular player in the game
    all_records = game.record_keeper.set_index('Player')
    record_p = all_records.loc[player_ID]
    record_p['Cards_in_Set'] = record_p.apply(lambda x: list(x['PlayerCards'])[x['Cardset']], axis=1)
    record_p['Card1'] = record_p.apply(lambda x: x['Cards_in_Set'][0][1], axis=1)
    record_p['Card2'] = record_p.apply(lambda x: x['Cards_in_Set'][1][1], axis=1)
    record_p['Dealer'] = record_p['DealerUpcard'].apply(lambda x: x[1])
    record_p = record_p[['Result','Double','Dealer','Card1','Card2']].reset_index(drop=True)

    #Assign value for each hand, IGNORING DOUBLES
    win_rules = {'DealerBust':1,'Win':1,'Bust':-1,'Beat':-1,'Surrender':-0.5,'Blackjack':game.blackjack,'Push':0}
    record_p['Value'] = record_p.apply(lambda x: win_rules[x['Result']],axis=1)
    #Convert aces to a single 11 value
    for cardtype in ['Card1','Card2','Dealer']:
        record_p[cardtype] = [max(x) if type(x) is list else x for x in record_p[cardtype]]
    
    #Aggregate data for hard-totals (no aces, one cardset at a time)
    hards = record_p[-((record_p['Card1']==11)^(record_p['Card2']==11))]
    hards['HardTotal'] = record_p['Card1']+record_p['Card2']
    #If the player isn't splitting, double aces will show up; don't report this as 22
    if game.players[player_ID-1].strat['Split']==1:
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
                                      colorscale = 'Electric',
                                      colorbar = {'title':'Average Hand Value'}))
    fig_hard.update_xaxes(title_text='Player Hard Total')
    fig_hard.update_xaxes(side='top')
    fig_hard.update_yaxes(title_text='Dealer UpCard')
    
    #Plot soft total performance
    fig_soft = go.Figure(data = go.Heatmap(z = softs['AvgValue'],
                                      x = softs['NonAce'],
                                      y = softs['Dealer'],
                                      colorscale = 'Electric',
                                      colorbar = {'title':'Average Hand Value'}))
    fig_soft.update_xaxes(title_text='Player Non-Ace Card in Soft Hand')
    fig_soft.update_xaxes(side='top')
    fig_soft.update_yaxes(title_text='Dealer UpCard')
    
    return fig_hard, fig_soft