import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re


def construct_vars(prefix, n, postfix=None, skip=[]):
    ls = []
    for i in range(n):
        if (i+1) not in skip:
            out = prefix + str(i+1)
            if postfix:
                out = out + postfix
            ls.append(out)
    return ls


def extract_values(row):
    out = np.nan
    for i in range(len(row)):
        if row[i] is not np.nan:
            out = str(i+1)
    return out


def map_w1_to_other(col_name, dat, wave):
    if wave.isnumeric():
        dictionary = dat.loc[dat['wave']=='1', ['PROLIFIC_PID', col_name]].set_index('PROLIFIC_PID').to_dict()
    else:
        dictionary = dat.loc[dat['wave']=='A', ['PROLIFIC_PID', col_name]].set_index('PROLIFIC_PID').to_dict()

    dat.loc[dat[col_name].isna(), col_name] = dat.loc[dat[col_name].isna(), 'PROLIFIC_PID'].map(dictionary[col_name])
    return dat


def clean_column_names(col_names):
    # Clean up the column names by removing the unicode values
    new_cols = []
    for col in col_names:
        replaced = re.sub(r'[^\x00-\x7F]', '', col)
        new_cols.append(replaced)
    return new_cols


def reformat_conte_CCID(data):
    tmp = []
    for CCID in data:
        if len(CCID) == 1:
            tmp.append('CC000' + CCID)
        elif len(CCID) == 2:
            tmp.append('CC00' + CCID)
        elif len(CCID) == 3:
            tmp.append('CC0' + CCID)
        elif len(CCID) == 4:
            tmp.append('CC' + CCID)
        else:
            tmp.append(CCID)
    return tmp


def detect_new_columns(data, aligned, week):
    cols = []
    for col in list(data.columns):
        if col not in list(aligned[week]):
            cols.append(col)
    return cols


def ext_txt(data, week, aligned, lookup, debug=False, debug_col=None, verbose=False):

    # Column types to ignore:
    ig_cols = ['unchanged', 'text', 'numeric']

    # Preprocessing for the lookup table
    # Get rid of all unicode characters and punctuation characters using regular expression
    # Change all response values in the lookup table to lowercase letters
    lookup.loc[:, 'Responses'] = lookup['Responses'].astype(str).str.lower()\
                                 .str.replace(r"[^\x00-\x7F]", '')\
                                 .str.replace(r"[ .,!\"']", '')

    # Start value substitution
    data_cols = list(data.columns)

    # Clean column names
    data_cols = clean_column_names(data_cols)
    #print(data_cols)
    data.columns = data_cols

    iteration = aligned.iterrows()

    # Skip the first row from the align table
    next(iteration)

    # Define a rename dictionary
    tmp_dict = {}

    for row in iteration:
        # Get column names and lookup id from the aligned/items table
        column = row[1][week]
        lookup_id = row[1]['Question_type']
        new_col_name = row[1]['unified_variable_names']

        # Only run for columns that exist in the dataset
        if (column is not np.nan):
            str_col = str(column)
            if verbose==True:
                print(str_col)
            if str_col in data_cols:
                # If this variable only has a single value, convert it to 1
                if lookup_id == 'single_item':
                    #print('single_item: '+ str_col)
#                     if (str_col=='Mask1_1'):
#                         print(str_col)
#                         print(data[str_col])
#                         print(new_col_name)
                    idx = data[str_col].notna()
                    idx[0] = False
                    data.loc[idx, str_col] = 1.0



                # If other response type, create a substitution dictionary
                elif lookup_id not in ig_cols:
                    # Generate the dictionary for replacement
                    print(str_col)
                    replace_dict = lookup.loc[lookup['Type']==lookup_id, ['Responses', 'Numeric']]\
                                   .set_index('Responses').to_dict()
                    # if str_col == 'NIHE1_9':
                    #     print(replace_dict)
                    #     print(data.loc[1:,str_col])

                    data.loc[1:,str_col] = data.loc[1:,str_col].str.lower().\
                                           str.replace(r"[^\x00-\x7F]", '').\
                                           str.replace(r"[ .,!\"']", '').\
                                           replace(replace_dict['Numeric']).astype(float)

                tmp_dict[str_col] = new_col_name

            # A warning for situation that a column is found in the aligned table but not in the input data
            else:
                print("Warning: column '{}' in aligned file is not a column of the data file.".format(str_col))

    data = data.rename(columns=tmp_dict)

    return data

def handle_RW27(num, data, week='RW27'):
    data.columns = clean_column_names(list(data.columns))
    num.columns = clean_column_names(list(num.columns))

    if (week == 'Pilot30') | (week == 'Week1'):
        col = 'Q60'
    else:
        col = 'RW27'

    iteration = data.iterrows()
    next(iteration)
    for index, row in iteration:
        rid = row['V1']
        val = num.loc[num['V1']==rid, col]
        if (~val.isna().values):
            data.loc[data['V1']==rid, col] = int(num.loc[num['V1']==rid, col])

    return data

def comb_score(score_file, processed_data, week):
    score = pd.read_csv(score_file, encoding = "ISO-8859-1", dtype=str)
    score_cols = list(score.columns)
    # Clean column names
    score_cols = clean_column_names(score_cols)
    score.columns = score_cols

    if week.endswith('C'):
        # handle conte data
        score['CCID'] = reformat_conte_CCID(score['CCID'])
        processed_data = processed_data.merge(score, how='left', on='CCID')
    else:
        processed_data = processed_data.merge(score, how='left', on='PROLIFIC_PID')
    return processed_data


def extract(source, num, score, week_col, aligned, lookup, save_path=None):
    # Somehow the new files we work with requires a different encoding.
    data = pd.read_csv(source, encoding = "ISO-8859-1", dtype=str, keep_default_na=False, na_values=['', 'nan'])
    num_data = pd.read_csv(num, encoding = "ISO-8859-1", dtype=str, keep_default_na=False, na_values=['', 'nan'])
    # First handle the RW27 and Q60 column

    data = handle_RW27(num_data, data, week=week_col)
    processed_data = ext_txt(data, week_col, aligned, lookup)
    processed_data = comb_score(score, processed_data, week_col)

    if save_path:
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        path = save_path + week_col + '.csv'
        processed_data.to_csv(path, index=False, encoding='utf-8')

    return processed_data


def unify_randomizer_names(data, week, aligned, lookup, debug=False, debug_col=None):
    # Column types to ignore:
    ig_cols = ['unchanged', 'text', 'numeric']

    # Preprocessing for the lookup table
    # Get rid of all unicode characters and punctuation characters using regular expression
    # Change all response values in the lookup table to lowercase letters
    lookup.loc[:, 'Responses'] = lookup['Responses'].astype(str).str.lower()\
                                 .str.replace(r"[^\x00-\x7F]", '')\
                                 .str.replace(r"[ .,!\"']", '')

    # Start value substitution
    data_cols = list(data.columns)

    # Clean column names
    data_cols = clean_column_names(data_cols)
    #print(data_cols)
    data.columns = data_cols

    iteration = aligned.iterrows()

    # Skip the first row from the align table
    next(iteration)

    # Define a rename dictionary
    tmp_dict = {}

    for row in iteration:
        # Get column names and lookup id from the aligned/items table
        column = row[1][week]
        lookup_id = row[1]['Question_type']
        new_col_name = row[1]['unified_variable_names']

        # Only run for columns that exist in the dataset
        if (column is not np.nan):
            str_col = str(column)
            if str_col in data_cols:
                tmp_dict[str_col] = new_col_name
#                 if str_col == 'Mask1_1':
#                     print(new_col_name)
#                     print(data['Mask1_1'])

            # A warning for situation that a column is found in the aligned table but not in the input data
            else:
                print("Warning: column '{}' in aligned file is not a column of the data file.".format(str_col))

    data = data.rename(columns=tmp_dict)

    return data


def processed_v2(data_path, aligned, lookup, week, num_path=None, verbose=False, score_file=None, randomizer=None):
    data = pd.read_csv(data_path, encoding = "ISO-8859-1", dtype=str, keep_default_na=False, na_values='')
    if num_path:
        num = pd.read_csv(num_path, encoding = "ISO-8859-1", dtype=str, keep_default_na=False, na_values='')
        print('processing RW27..')
        data = handle_RW27(num, data, week)
    print('processing text exchange')
    processed = ext_txt(data, week, aligned, lookup, verbose=verbose)

    if score_file:
        score = pd.read_csv(score_file, encoding = "ISO-8859-1", dtype=str, keep_default_na=False, na_values='')
        #print(score['SNI_Ex_Network_Diversity_allComm_2019'].values)
        processed = processed.merge(score, how='left', on='PROLIFIC_PID')

    if randomizer:
        randomizer_dat = pd.read_csv(randomizer, encoding = "ISO-8859-1", dtype=str, keep_default_na=False, na_values='')
        randomizer_dat.columns = clean_column_names(randomizer_dat.columns)
        randomizer_dat = unify_randomizer_names(randomizer_dat, week, aligned, lookup)

        Vs = [x for x in randomizer_dat.columns.tolist() if x.startswith('V')]
        Vs.remove('V1')
        Vs.append('PROLIFIC_PID')
        randomizer_dat.drop(Vs, inplace=True, axis=1)
        processed = processed.merge(randomizer_dat, how='left', on='V1')


    #print(processed['SNI_Ex_Network_Diversity_allComm_2019'].values)

    return processed


def clean_text_columns(data, aligned):
    cols = data.columns
    iteration = aligned.iterrows()
    # Skip the first row from the align table
    next(iteration)
    for row in iteration:
        # qt = row[1]['Question_type']
        # if (qt=='text'):
        var_name = row[1]['unified_variable_names']
        if var_name in cols:
            print(var_name)
            data.loc[:, var_name] = data.loc[:, var_name].astype('str').str.replace(r"[^\x00-\x7F]", '')
    return data
