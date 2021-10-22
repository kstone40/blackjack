# -*- coding: utf-8 -*-
"""
@author: Kevin Stone

THINGS TO ADD:
    Adding custom strategy
    Show the optimal strategy in a DF
"""
import streamlit as st
import pandas as pd
import random
import copy
import time
import plotly.graph_objects as go
#from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import numpy as np
import glob

from blackjack_project import *

#Set page title and wide layout
st.set_page_config(page_title='Blackjack Strategy Simulator',layout='wide')

#Main page output
#Title
st.title('Blackjack Strategy Simulator')
st.write('v1.0, Sep 2021, Kevin Stone')

st.subheader('First, consider reviewing the fundamentals below.')

#Load in all of the optimal strategies from csv files in ./Strategies
list_of_strats = glob.glob('./Strategies/strategy_1*.csv')  
strats = {}
for file in list_of_strats:
    header_name = file.split('_1_')[1].split('.')[0]
    strats[header_name]=pd.read_csv(file)

#Load in all of the rules from txt files in ./Rules
list_of_rules = glob.glob('./Rules/*.txt')   
for file in sorted(list_of_rules):
    header_name = file.split('/')[2].split('.txt')[0]
    with st.expander(header_name):
        with open(file,'r') as f:
            st.markdown(f.read())
        if header_name == '3 - Optimal Strategy':
            replacements = {'DoubleH':'Double, else Hit', 'DoubleS':'Double, else Stand','Surrender':'Surrender, else Hit'}
            
            st.subheader('Hard Total Strategy')
            hard_unmelted = strats['hard'].pivot(index='Player', columns='Dealer').replace(replacements)
            st.write(hard_unmelted)
        
            st.subheader('Soft Total Strategy')
            soft_unmelted = strats['soft'].pivot(index='Card2', columns='Dealer').replace(replacements)
            st.write(soft_unmelted)
        
            st.subheader('Split Strategy')
            split_unmelted = strats['split'].pivot(index='Card', columns='Dealer').replace(replacements)
            st.write(split_unmelted)



st.write('')
st.subheader('Next, populate the sidebar (left) with options that you choose to evaluate in a simulation study.')

options = {}
st.sidebar.header('Simulation Options')    
options['hands'] = st.sidebar.number_input('Hands',
                                               min_value=0,max_value=1000000,value=1000,step=100,
                                               help='Enter the number of hands to simulate') 
seed = st.sidebar.text_input('Random Seed',value='6644',max_chars=10,help='(Optional) Random Seed')

st.sidebar.header('Game Options')  
options['blackjack'] = st.sidebar.number_input('BlackJack Value',
                                               min_value=0.0,max_value=None,value=1.5,
                                               help='Enter the value (multiplier of bet) that a natural BlackJack should return')      

options['decks_per_shoe'] = st.sidebar.number_input('Decks per Shoe',
                                               min_value=0,max_value=None,value=6,step=1,
                                               help='Enter the number of decks in play')
options['cut_in'] = st.sidebar.number_input('Decks to Cut In',
                                               min_value=0.0,max_value=float(options['decks_per_shoe']),value=options['decks_per_shoe']*(2/3), step=0.1,
                                               help='Enter the number of decks to play before reshuffling')

options['player_count'] = st.sidebar.number_input('Number of Players',
                                                  min_value=0,max_value=10,value=1,step=1,
                                                  help='Enter the number of players/strategies to simulate together')
options['player_strat'] = []
player_strats = st.sidebar.expander('Player Strategies')
with player_strats:
    for p_ in range(options['player_count']):
        st.subheader(f'Player {p_+1}')
        options['player_strat'].append({})
        choices = ['None/Dealer','Optimal']

        hard_strat = player_strats.selectbox('Hard-Total Strategy',choices,index=1,help='Select a strategy to test',key=str(p_)+'strat_hard')
        soft_strat = player_strats.selectbox('Soft-Total (Ace) Strategy',choices,index=1,help='Select a strategy to test',key=str(p_)+'strat_soft')
        split_strat = player_strats.selectbox('Split Strategy',choices,index=1,help='Select a strategy to test',key=str(p_)+'strat_split')               
        double_strat = player_strats.selectbox('Double-down Allowed?',[True,False],index=0,help='Select a strategy to test',key=str(p_)+'strat_double')               
        surr_strat = player_strats.selectbox('Surrender Allowed?',[True,False],index=1,help='Select a strategy to test',key=str(p_)+'strat_surr')               
    
        #Boolean algebra for 0 = None, 1 = Default, 2 = Custom
        options['player_strat'][p_]['Hard'] = 0**(hard_strat=='None/Dealer')+0**(hard_strat!='Custom')
        options['player_strat'][p_]['Soft'] = 0**(soft_strat=='None/Dealer')+0**(soft_strat!='Custom')
        options['player_strat'][p_]['Split'] = 0**(split_strat=='None/Dealer')+0**(split_strat!='Custom')
        options['player_strat'][p_]['Double'] = 0**(not double_strat)
        options['player_strat'][p_]['Surrender'] = 0**(not surr_strat)
        
@st.cache(allow_output_mutation=True)
def set_game(options):
    my_game = game(options)
    global cache_miss
    cache_miss = True
    return my_game

@st.cache(allow_output_mutation=True,suppress_st_warning=True)
def play_game(options,seed):
    my_game = game(options)
    random.seed(seed)
    my_game.play()
    return my_game

new_game = set_game(options)
if 'cache_miss' in vars():
    st.warning('Input settings have changed, simulation must be re-run')
else:
    my_game = play_game(options,seed)  

st.subheader('When you are ready, press the button below to begin the simulation.')
st.write('')
st.write('')
button_cols = st.columns(3)
n_hands = options['hands']
play_button = button_cols[1].button(f'Press here to simulate your Blackjack game for {n_hands} hands')
if play_button:
    my_game = play_game(options,seed)
    
if 'my_game' in vars():
    st.subheader('Now that the simulation is complete, examine the analytics below.')
    stats_info = st.expander('Player Statistics',expanded=False)
    with stats_info:
        stats, edges = my_game.score()
        st.write('House Edges Calculated for Each Player/Strategy')
        st.write(edges)
        statscols = st.columns(options['player_count'])
        for p_ in range(options['player_count']):
            statscols[p_].write(f'Summary Statistics for Player {p_+1}')
            statscols[p_].write(stats.loc[p_+1])
            
        fig_stats = go.Figure()
        for p_ in range(options['player_count']):
            player_stats = stats.loc[p_+1]
            player_stats['Double Label'] = np.where(player_stats['Double']==True,'Double','Standard')
            fig_stats.add_trace(go.Bar(x=player_stats['Result'],y=player_stats['Frequency'],name=f'Player {p_+1}',text = player_stats['Double Label']))
        fig_stats.update_xaxes(title_text='Result')
        fig_stats.update_yaxes(title_text='Frequency')
        fig_stats.update_layout(title_text='Comparison of Player Outcomes')
        st.plotly_chart(fig_stats, use_container_width=True)
        
    val_plot = st.expander('Player Value over Time',expanded=False)
    with val_plot:
        fig_val = val_over_time(my_game)
        st.plotly_chart(fig_val, use_container_width=True)
        
    prob_plot = st.expander('Batch-Means Analysis')
    with prob_plot:
        batch_hands = st.number_input('Number of Hands for Batch-Means Analysis',
                                               min_value=0,max_value=None,value=20,step=1,
                                               help='Enter the number of hands to batch out the simultaion')
        batch_means, batch_vars, fig_pmf, fig_ecdf  = batch_means(my_game,batch_hands)
        st.plotly_chart(fig_pmf, use_container_width=True) 
        st.plotly_chart(fig_ecdf, use_container_width=True)
    
    heatmap_plot = st.expander('Card Value Heatmap')
    with heatmap_plot:
        heatmap_cols = st.columns(2)
        fig_hard, fig_soft = card_heatmap(my_game)
        with heatmap_cols[0]:
            st.plotly_chart(fig_hard, use_container_width=True)
        with heatmap_cols[1]:
            st.plotly_chart(fig_soft, use_container_width=True)
            
    value_comparison = st.expander('Player Action Optimizer')
    with value_comparison:
        card_vals = list(range(2,11))
        card_vals.append([1,11])
        card_names = ['2','3','4','5','6','7','8','9','10 or Face','Ace']
        card_options = zip(card_names, card_vals)
        
        card1 = st.selectbox('Player Card 1', card_options)
        card2 = st.selectbox('Player Card 2', card_options)
        upcard = st.selectbox('Dealer Upcard', card_options)
        player_ID = st.selectbox('Player ID', list(range(1,1+my_game.player_count)))
        iterations = st.number_input('Iterations',
                                               min_value=0,max_value=10000,value=200,step=1,
                                               help='Enter the number of hands to test in the optimizer')
        
        values = my_game.value_actions(upcard,[card1,card2],player_ID,iterations)
