#Dealer upcard probabilities
dealer_probs = [1/13]*8
dealer_probs.append(4/13)
dealer_probs.append(1/13)
dealer_probs_dict = {}
for dealer_card,prob in zip(range(2,12),dealer_probs):
    dealer_probs_dict[dealer_card] = prob

#Player probabilities for hard sums
#Have to assume soft cards are in play, so no aces
#Have to assume splits are in play, so no doubles either
#Also treating each card as perfectly independent (infinite decks)
#Considering only 5 - 19 on the first 2 cards... hmm
#5 (2/3 or 3/2)
hard_probs = [((1/13)**2)*2]
#6 (2/4, 4/2)
hard_probs.append(((1/13)**2)*2)
#7 (2/5, 3/4, 4/3, 5/2)
hard_probs.append(((1/13)**2)*4)
#8 (2/6, 3/5, 5/3, 6/2)
hard_probs.append(((1/13)**2)*4)
#9 (2/7, 3/6, 4/5, 5/4, 6/3, 7/2)
hard_probs.append(((1/13)**2)*6)
#10 (2/8, 3/7, 4/6, 6/4, 7/3, 8/2)
hard_probs.append(((1/13)**2)*6)
#11 (2/9, 3/8, 4/7, 5/6, 6/5, 7/4, 8/3, 9/2)
hard_probs.append(((1/13)**2)*8)
#12 (2/10, 3/9, 4/8, 5/7, 7/5, 8/4, 9/3, 10/2)
hard_probs.append(((1/13)**2)*6+((4/13)*(1/13))*2)
#13 (3/10, 4/9, 5/8, 6/7, 7/6, 8/5, 9/4, 10/3)
hard_probs.append(((1/13)**2)*6+((4/13)*(1/13))*2)
#14 (4/10, 5/9, 6/8, 8/6, 9/5, 10/4)
hard_probs.append(((1/13)**2)*4+((4/13)*(1/13))*2)
#15 (5/10, 6/9, 7/8, 8/7, 9/6, 10/5)
hard_probs.append(((1/13)**2)*4+((4/13)*(1/13))*2)
#16 (6/10, 7/9, 9/7, 10/6)
hard_probs.append(((1/13)**2)*2+((4/13)*(1/13))*2)
#17 (7/10, 8/9, 9/8, 10/7)
hard_probs.append(((1/13)**2)*2+((4/13)*(1/13))*2)
#18 (8/10, 10/8)
hard_probs.append(((4/13)*(1/13))*2)
#19 (9/10, 10/9)
hard_probs.append(((4/13)*(1/13))*2)
hard_probs_dict = {}
for hardsum,prob in zip(range(5,20),hard_probs):
    hard_probs_dict[hardsum] = prob


#Player probabilities for soft sums
#First card is an ace, so everything starts with 1/13
#Only care about 2-9 for soft cards, 
soft_probs = [1/13*1/13]*8
soft_probs_dict = {}
for soft_card2,prob in zip(range(2,10),soft_probs):
    soft_probs_dict[soft_card2] = prob

#Player probabilities for splits
#Just will be individual probabilities, squared
split_probs = [prob**2 for prob in dealer_probs]
split_probs_dict = {}
for split_card,prob in zip(range(2,12),split_probs):
    split_probs_dict[split_card] = prob

master_prob = {}
master_prob['Dealer'] = dealer_probs_dict
master_prob['Hard'] = hard_probs_dict
master_prob['Soft'] = soft_probs_dict
master_prob['Split'] = split_probs_dict

master_prob = pd.DataFrame(master_prob)