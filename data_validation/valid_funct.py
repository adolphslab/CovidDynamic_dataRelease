import numpy as np
import pandas as pd
from natsort import natsorted
from glob import glob
import nltk
import os
import warnings

def check_for_errors(data, valid_data, keyword):
    if((len(valid_data) != len(data)) |
   (len(set(valid_data['PROLIFIC_PID']+valid_data['wave']) - set(data['PROLIFIC_PID']+data['wave'])) !=0) |
   (len(set(data['PROLIFIC_PID']+data['wave'])- set(valid_data['PROLIFIC_PID']+valid_data['wave']))  !=0)):
        warnings.warn("Warning: Check " + keyword + "!");


def attent_check(dat, w):
    """
    Count numper of failed attention questions.
    INPUT
        dat (pd.DataFrame) - all data
        w (str) - wave of interest
    OUTPUT
        out (pd.DataFrame) - 7 columns: 
                                * wave
                                * PROLIFIC_PID
                                * 5 possible pailed attention questions (TRUE if failed, FALSE if passed, NaN if not included)
    """

    # select wave
    dat = dat.loc[dat.wave == w, :]
    # drop empty columns
    dat = dat.dropna(axis = 1, how = 'all')


    # attention check column names and correct values in export data    
    attent_chk_dict = {'NIHE1_9': '4.0',
                      'DemC25': '3.0',
                      'DISG1.2_23': '4.0',
                      'DISG1.1_23': '2.0',
                      'DISG2.2_23': '4.0',
                      'ReSe1_23': '4.0',
                      'Fed_13': '7.0', 
                      'RW23': '2.0',
                      'GFPS2_11': '1.0',
                      'EES1_32': '5.0',}
    
    # attention check column names
    attent_vars = list(attent_chk_dict.keys())

    # attention questions included in wave
    att_q = list(set(dat.columns).intersection(set(attent_vars)))
    
    # count if 1 to 5 possible failed attention questions (N attention questions varies across waves)
    out = pd.DataFrame(index=np.arange(len(dat)), \
                       columns= ['failed_att_qns_1', 'failed_att_qns_2', 'failed_att_qns_3',
                                 'failed_att_qns_4','failed_att_qns_5'])
    out['PROLIFIC_PID'] = dat.PROLIFIC_PID.values
    out['wave'] = dat.wave.values

    # compare attention question-responses to correct response
    for idx, att_check in enumerate(att_q):
        tmp = dat[att_check] != attent_chk_dict[att_check]
        out[out.columns[idx]] = tmp.values
        del tmp
    out.replace(True, 1, inplace = True)
    out.replace(False, 0, inplace = True)
    out['more_than_1_attQ_failed'] = out.loc[:,'failed_att_qns_1':'failed_att_qns_5'].sum(axis=1)>0
    
    return out[['PROLIFIC_PID', 'wave', 'more_than_1_attQ_failed']]

def w_completed(data):
    w_completed = pd.DataFrame(data[['PROLIFIC_PID', 'wave', 'V5']])
    w_completed = w_completed.rename(columns ={'V5': 'completed'})
    w_completed['completed'].replace('TRUE', '1', inplace=True)
    w_completed['completed'].replace('FALSE', '0',inplace=True)
    return w_completed

def nounVerb_count(data):
    text_cols = ['DemW21_1_TEXT','DemW21_2_TEXT', 'DemW21_3_TEXT', 'RW7_1_TEXT', 'RW7_2_TEXT', 'RW7_3_TEXT']
    verbNoun_df = data[['PROLIFIC_PID', 'wave']]

    for text_col in text_cols:
        df  = data[['PROLIFIC_PID', 'wave', text_col]].dropna().reset_index(drop = True)
        for row_idx in df.index:
            tokenized =  nltk.pos_tag(nltk.word_tokenize(df.loc[row_idx,text_col]))
            tmp = np.array(tokenized)
            val,count =  np.unique(tmp[:,1], return_counts=True)
            pos_counts = pd.DataFrame(index = val)
            pos_counts['count'] = count
            N_nouns = pos_counts.loc[pos_counts.index.str.startswith('NN'), 'count'].sum()
            N_verbs = pos_counts.loc[pos_counts.index.str.startswith('VB'), 'count'].sum()
            nounVerb_count =  N_nouns + N_verbs
            df.loc[row_idx, 'nounVerb_count_'+text_col] = nounVerb_count
        verbNoun_df = verbNoun_df.merge(df, on = ['PROLIFIC_PID', 'wave'], how = 'left')
        
    stress_df = pd.DataFrame()
    stress_df['free_text_resp_valid_stress'] = (verbNoun_df[['nounVerb_count_DemW21_1_TEXT',
                                                                 'nounVerb_count_DemW21_2_TEXT',
                                                                 'nounVerb_count_DemW21_3_TEXT']].dropna(axis=0,
                                                                                                         how='all')>0).sum(axis = 1)<3
    verbNoun_df = verbNoun_df.merge(stress_df, left_index=True, right_index=True, how= 'left')
    news_df = pd.DataFrame()
    news_df['free_text_resp_valid_news'] = (verbNoun_df[['nounVerb_count_RW7_1_TEXT',
                                                             'nounVerb_count_RW7_2_TEXT',
                                                             'nounVerb_count_RW7_3_TEXT']].dropna(axis=0,
                                                                                                  how='all')>0).sum(axis = 1)<3
    verbNoun_df = verbNoun_df.merge(news_df, left_index=True, right_index=True, how= 'left')
        
    return verbNoun_df[['PROLIFIC_PID', 'wave','free_text_resp_valid_stress', 'free_text_resp_valid_news']]

####################################### RESP STRING LENGTH #############################
def extract_long_string(long_string_df, data, name, input_vars):
    tmp_df = run_analysis(data, name, input_vars)
    long_string_df = long_string_df.merge(tmp_df, on = ['PROLIFIC_PID', 'wave'], how = 'left')
    return long_string_df

def long_string(row):
    # Return a list of response string length
    # The calculation of MaxLongString, meanLongString and countLongString can be calculated from this list
    count_ls = []
    string_len = 1
    for i in range(1, len(row)):
        if np.isnan(float(row[i])):
            # If the row contains all nas, then will append an empty list
            continue
        elif row[i] == row[i-1]:
            string_len += 1
        elif row[i-1] is not np.nan:
            count_ls.append(string_len)
            string_len = 1
    
    if ~np.all(np.isnan([float(x) for x in row])):
        count_ls.append(string_len)
    return np.array(count_ls)


def get_max(ls):
    if ls.size == 0:
        return np.nan
    else:
        return ls[np.argmax(ls)]
    
    
def get_mean(ls):
    if ls.size == 0:
        return np.nan
    else:
        return np.mean(ls)

    
def process_na(dat, var_names):
    for w in np.unique(dat['wave']):
        for var in var_names:
            if np.sum(~dat.loc[dat['wave']==w, var].isna())>0:
                dat.loc[dat['wave']==w,var] = dat.loc[dat['wave']==w, var].fillna(0)   
    return dat

def run_analysis(data, name, input_vars):
    data = process_na(data, input_vars)
    input_dat = data.loc[:, input_vars]
    input_indices = data[['PROLIFIC_PID', 'wave']]
    out_df = response_string(input_indices, input_dat, name)
    return out_df

def response_string(input_indices, data, name):
    s_long_string = data.apply(long_string, axis=1)
    out_df = pd.DataFrame(index =data.index)
    out_df['maxLongString_'+name] = s_long_string.apply(get_max)
    out_df['meanLongString_'+name] = s_long_string.apply(get_mean)
    out_df = input_indices.merge(out_df,left_index=True, right_index=True)
    return out_df


def construct_vars(prefix, n, postfix=None, skip=[]):
    ls = []
    for i in range(n):
        if (i+1) not in skip:
            out = prefix + str(i+1)
            if postfix:
                out = out + postfix
            ls.append(out)
    return ls
    
    
    
####################################### interquartile range #############################

    
def interq_range(s, n):
    # calculate the intequartile range given a pandas series - a list of responses
    s_cleaned = s[~s.isna()]
    if len(s_cleaned) == 0:
        return [np.nan, np.nan]
    else:
        q1 = np.quantile(s_cleaned.astype(float), 0.25)
        q3 = np.quantile(s_cleaned.astype(float), 0.75)
        return [q1-n*(q3-q1), q3+n*(q3-q1)]


def interq_analysis(dat, n_q):
    
    dat_idx = dat[['PROLIFIC_PID','wave']]
    dat_val = dat.iloc[:,2:]
    n_w = dat_idx.wave.unique()
    dat_tmp = dat.copy()
    dat_tmp.iloc[:,2:] = np.nan
    for w in n_w:
        interq_r = dat_val.loc[dat_idx['wave'] == w].apply(lambda x: interq_range(x, 1), axis=0)
        for col in list(interq_r.columns):
            dat_no_na = dat_val.loc[(dat_idx['wave'] == w) & (~dat_val[col].isna())]
            idx = (dat_no_na[col]<=interq_r[col][1]) & (dat_no_na[col]>=interq_r[col][0])
            idx = idx.index[idx == True]
            dat_tmp.loc[idx, col] = 0

    for q in range(n_q):
        for w in n_w:
            interq_r = dat_val.loc[dat_idx['wave'] == w].apply(lambda x: interq_range(x, q+1), axis=0)
            for col in list(interq_r.columns):
                dat_no_na = dat_val.loc[(dat_idx['wave'] == w) & (~dat_val[col].isna())]
                idx =((dat_no_na[col]<interq_r[col][0]) | (dat_no_na[col]>interq_r[col][1]))
                idx = idx.index[idx == True]
                dat_tmp.loc[idx, col] = q+1
    return dat_tmp