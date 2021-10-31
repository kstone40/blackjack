# -*- coding: utf-8 -*-
"""
@author: Kevin Stone
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
import base64

from blackjack_project import *

#Set page title and wide layout
st.set_page_config(page_title='Blackjack Strategy Simulator',layout='wide')

#Main page output
#Title
st.title('Blackjack Strategy Simulator')
st.write('v1.0, Sep 2021, Kevin Stone')

st.subheader('First, consider reviewing the fundamentals below.')


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
options['H17'] = st.sidebar.checkbox('Dealer Hits on Soft 17?', value=1,
                                                 help ='Check if you want to simulate a dealer that hits on soft 17s')
options['decks_per_shoe'] = st.sidebar.number_input('Decks per Shoe',
                                               min_value=0,max_value=None,value=6,step=1,
                                               help='Enter the number of decks in play')
options['cut_in'] = st.sidebar.number_input('Decks to Cut In',
                                               min_value=0.0,max_value=float(options['decks_per_shoe']),value=options['decks_per_shoe']*(2/3), step=0.1,
                                               help='Enter the number of decks to play before reshuffling')
options['player_count'] = st.sidebar.number_input('Number of Players',
                                                  min_value=0,max_value=10,value=1,step=1,
                                                  help='Enter the number of players/strategies to simulate together')

#Load in the appropriate optimal strategy
if options['H17'] == 1:
    char = 'H'
else:
    char = 'S'

optimal_strat = optimal_strat = pd.ExcelFile(f'Strategies/strategy_optimal_{char}17.xlsx')
hard_strat = pd.read_excel(optimal_strat, 'hard').set_index('Player')
soft_strat = pd.read_excel(optimal_strat, 'soft').set_index('Player')
split_strat = pd.read_excel(optimal_strat, 'split').set_index('Player')

#Load in all of the rules from txt files in ./Rules
list_of_rules = glob.glob('./Rules/*.txt')   
for file in sorted(list_of_rules):
    header_name = file.split('/')[2].split('.txt')[0]
    with st.expander(header_name):
        with open(file,'r') as f:
            st.markdown(f.read())
        if header_name == '3 - Optimal Strategy':
            st.subheader(f'Optimal Strategy for {char}17 Game')
            st.subheader('Hard Total Strategy')
            st.write(hard_strat)
            st.subheader('Soft Total Strategy')
            st.write(soft_strat)
            st.subheader('Split Strategy')
            st.write(split_strat)

st.write('')
st.subheader('Next, populate the sidebar (left) with options that you choose to evaluate in a simulation study.')


options['player_strat'] = []
options['player_names'] = []

player_strats = st.sidebar.expander('Player Strategies')
with player_strats:
    for p_ in range(options['player_count']):
        st.subheader(f"{options['player_names'][p_]}")
        custom_strat = player_strats.checkbox('Custom?', value=0, key=str(p_)+'strat_custom',
                                          help ='Check if you want to upload a custom strategy')
        options['player_strat'].append({})
        options['player_names'].append(player_strats.text_input('Name', value=f"{options['player_names'][p_]}", key=str(p_)+'name'))
        if custom_strat:
            #Show example file
            data = open('Strategies/strategy_custom_example.xlsx', 'rb').read()
            b64 = base64.b64encode(data).decode('UTF-8')
            href = f'<a href="data:file/output_obj;base64,{b64}" download="Example_Strategy.xlsx" target="_blank"> Download Example Custom Strategy </a>'
            st.markdown(href, unsafe_allow_html=True)
            uploaded_file = player_strats.file_uploader('Choose a file', key=str(p_))
            if uploaded_file is not None:
                options['player_strat'][p_]['Special'] = 'Custom'
                options['player_strat'][p_]['Path'] = uploaded_file.name
            if uploaded_file is None:
                options['player_strat'][p_]['Special'] = 'Custom'
                options['player_strat'][p_]['Path'] = 'Strategies/strategy_custom_example.xlsx'
        else:        
            choices = ['None/Dealer','Optimal']
            hard_strat = player_strats.selectbox('Hard-Total Strategy',choices,index=1,help='Select a strategy to test',key=str(p_)+'strat_hard')
            soft_strat = player_strats.selectbox('Soft-Total (Ace) Strategy',choices,index=1,help='Select a strategy to test',key=str(p_)+'strat_soft')
            split_strat = player_strats.selectbox('Split Strategy',choices,index=1,help='Select a strategy to test',key=str(p_)+'strat_split')               
            #Boolean algebra for 0 = None, 1 = Default
            options['player_strat'][p_]['Hard'] = 0**(hard_strat=='None/Dealer')
            options['player_strat'][p_]['Soft'] = 0**(soft_strat=='None/Dealer')
            options['player_strat'][p_]['Split'] = 0**(split_strat=='None/Dealer')
        
        double_strat = player_strats.selectbox('Double-down Allowed?',[True,False],index=0,help='Select a strategy to test',key=str(p_)+'strat_double')               
        surr_strat = player_strats.selectbox('Surrender Allowed?',[True,False],index=1,help='Select a strategy to test',key=str(p_)+'strat_surr')               
        options['player_strat'][p_]['Double'] = 0**(not double_strat)
        options['player_strat'][p_]['Surrender'] = 0**(not surr_strat)
        
@st.cache(allow_output_mutation=True)
def set_game(options):
    my_game = Game(options)
    global cache_miss
    cache_miss = True
    return my_game

@st.cache(allow_output_mutation=True,suppress_st_warning=True)
def play_game(options,seed):
    my_game = Game(options)
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
            statscols[p_].write(f'Summary Statistics for {options['player_names'][p_]}')
            statscols[p_].write(stats.loc[p_+1])
            
        fig_stats = go.Figure()
        for p_ in range(options['player_count']):
            player_stats = stats.loc[p_+1]
            player_stats['Double Label'] = np.where(player_stats['Double']==True,'Double','Standard')
            fig_stats.add_trace(go.Bar(x=player_stats['Outcome'],y=player_stats['Frequency'],name=f"{options['player_names'][p_]}",text = player_stats['Double Label']))
        fig_stats.update_xaxes(title_text='Outcome')
        fig_stats.update_yaxes(title_text='Frequency')
        fig_stats.update_layout(title_text='Comparison of Player Outcomes')
        st.plotly_chart(fig_stats, use_container_width=True)
        
        for p_ in range(options['player_count']):
            st.write(f'Realized Card Values for Player {options['player_names'][p_]}')
            fig_hard, fig_soft = card_heatmap(my_game, p_+1)
            heatmap_cols = st.columns(2)
            with heatmap_cols[0]:
                st.plotly_chart(fig_hard, use_container_width=True)
            with heatmap_cols[1]:
                st.plotly_chart(fig_soft, use_container_width=True)
        
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
           
    value_comparison = st.expander('Player Action Analyzer')
    with value_comparison:
        card_options = list(range(2,12))
        
        card_entry_cols = st.columns(4)
        card1 =  card_entry_cols[0].selectbox('Player Card 1', card_options)
        card2 = card_entry_cols[1].selectbox('Player Card 2', card_options)
        upcard = card_entry_cols[2].selectbox('Dealer Upcard', card_options)
        player_ID = card_entry_cols[3].selectbox('Player ID', list(range(1,1+my_game.player_count)),
                                                 help="Select a player's strategy to use for sequential actions that follow the first, fixed action (i.e. continuous hits, or splits)")
        iterations = st.number_input('Iterations',
                                               min_value=0,max_value=10000,value=200,step=100,
                                               help='Enter the number of hands to test in the optimizer')
        optimize_action = st.button('Go!')
        if optimize_action:
            summary, values, results = my_game.value_actions(upcard,[card1, card2],player_ID,iterations)
            st.write(summary)
            
            fig_actions = go.Figure()
            for outcome in results['Outcome'].unique():
                action_results = results.query(f"`Outcome` == '{outcome}'")
                fig_actions.add_trace(go.Bar(x=action_results['First Action'],y=action_results['Frequency'],name = outcome))
            fig_actions.update_xaxes(title_text='First Action')
            fig_actions.update_yaxes(title_text='Frequency')
            fig_actions.update_layout(title_text='Comparison of Action Outcomes')
            st.plotly_chart(fig_actions, use_container_width=True)
            
