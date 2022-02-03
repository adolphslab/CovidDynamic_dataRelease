#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 16:09:59 2020

@author: yantinghan
"""


# this script tries to extract 5/10 sub IDs 
# whose distance based on NEO is farthest among all people

import csv
import numpy as np
from scipy.spatial.distance import pdist
import pandas as pd
from sklearn import preprocessing
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import os

# the following part is to check whether the NEO scores for selected people make sense
# =============================================================================
# data = pd.read_csv('./Wave1-8_A-E.csv')
# sub_list = pd.read_csv('./furthest_10ids.csv') 
# subs = sub_list['PROLIFIC_PID']
# wave1 = data.groupby(['wave']).get_group(1) 
# wave1_core = wave1[wave1['PROLIFIC_PID'].isin(subs)]
# sub_vectors = np.array(wave1_core.loc[:,['NEO_O_z-score', 'NEO_C_z-score', 'NEO_E_z-score', 'NEO_A_z-score', 'NEO_N_z-score']])
# =============================================================================

data_path = os.path.join(os.path.expanduser('~'),'Box','COVID-19 Adolphs Lab', 'PreProcessed_Data')
data = pd.read_csv(os.path.join(data_path,'Wave1-16_A-M_release.csv'),low_memory=False)
data = data.loc[data.wave != '15b', :]
data.wave.unique()
list_path = os.path.join(os.path.expanduser('~'),'Box','COVID-19 Adolphs Lab', 'participant_lists')
# pids that completed all waves 
wave_count = data.PROLIFIC_PID.value_counts()

pids = wave_count.index[wave_count == 16]

wave1 = data.groupby(['wave']).get_group('1') 
wave1_core = wave1[wave1['PROLIFIC_PID'].isin(pids)] # get wave1 data only for the subjects that completed all waves
wave1_core = wave1_core.reset_index (drop = True) # reset index
sub_labels = wave1_core['PROLIFIC_PID']
sub_vectors = np.array(wave1_core.loc[:,['NEO_O_z-score', 'NEO_C_z-score', 'NEO_E_z-score', 'NEO_A_z-score', 'NEO_N_z-score']])
#sub_vectors[np.isnan(sub_vectors)] = 0
sub_vectors_scaled = preprocessing.scale(sub_vectors) # z score is with respect to published stats, not this sample


###########################################################################################################################
# Farthest point sampling
def calc_distances(p0, points):
    return np.sqrt(((p0 - points)**2.).sum(axis=1))

def farthest_points(pts, pt_labels, K,ii):
    ndims = pts.shape[1] #5 dims
    farthest_pts = np.zeros((K, ndims)) # specify format for wanted points, 5/10 people*5 dim
    farthest_pts[0] = pts[ii]  
    farthest_pts_labs = []
    farthest_pts_labs.append(pt_labels[ii]) # append label 
    distances = calc_distances(farthest_pts[0], pts) # calculate dist for this subject with all other ones

    for ij in range(1, K):
        farthest_pts[ij] = pts[np.argmax(distances)] #returns the index of the subject with the furthest dist
        farthest_pts_labs.append(pt_labels[np.argmax(distances)])
        distances = np.minimum(distances, calc_distances(farthest_pts[ij], pts))
        # for the rest of the points, update the distance to be the min to the already chosen ones
    return farthest_pts, farthest_pts_labs
###########################################################################################################################
    

# you can run Farthest point sampling 10000 times to find the optimal solution
# if the starting point is chosen randomly, but since i only have 1418 points
# just iterating all of them is easier

# K is the desired sample size. 
K= 5
all_sols_dists = []
all_sols_feats = []
all_sols_names = []
for iter_ii in range(len(sub_vectors)):
    solution_set, solution_labels = farthest_points(sub_vectors_scaled,sub_labels,K, iter_ii)
    all_sols_feats.append(solution_set)
    all_sols_names.append(solution_labels)
    all_sols_dists.append(np.sum(pdist(solution_set, metric='euclidean')))

best_sols_feats = all_sols_feats[np.argmax(all_sols_dists)]
best_sols_labels = all_sols_names[np.argmax(all_sols_dists)]

#print (sorted(best_sols_labels))
print (best_sols_labels)

# =============================================================================
# X_embedded = TSNE(n_components=2, perplexity=30, n_iter=10000).fit_transform(sub_vectors_scaled)
# 
# id_index = []
# id_loc = []
# for i in best_sols_labels:
#     pos = sub_labels.index[sub_labels == i].tolist()[0]
#     id_index.append(pos)
#     id_loc.append(X_embedded[pos].tolist())
# plt.scatter(X_embedded[:,0],X_embedded[:,1],facecolors='black',alpha=.55, )
# plt.scatter(id_loc[0][0], id_loc[0][1], color="yellow", s=100)   
# plt.scatter(id_loc[1][0], id_loc[1][1], color="red", s=100)  
# plt.scatter(id_loc[2][0], id_loc[2][1], color="blue", s=100)  
# plt.scatter(id_loc[3][0], id_loc[3][1], color="green", s=100)  
# plt.scatter(id_loc[4][0], id_loc[4][1], color="purple", s=100)  
# =============================================================================


df = pd.DataFrame(data={"PROLIFIC_PID": best_sols_labels})
df.to_csv("./furthest_5ids_w1to16.csv", sep=',',index=False)









