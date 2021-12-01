import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns
import matplotlib.ticker as ticker


# Plot summary statistics for the

def plot_single_item(col, data, save=None):
    fig = plt.figure(figsize=(12,10))
    ax = sns.countplot(x=col, data=data)
    total = len(data[col])
    for p in ax.patches:
            percentage = '{:.1f}% ({})'.format(100 * p.get_height()/total, p.get_height())
            x = p.get_x() + p.get_width() / 3
            y = p.get_y() + p.get_height() + 20
            ax.annotate(percentage, (x, y))
    ax.set_title(col + ' Value Counts')
    if save:
        fig = ax.get_figure()
        fig.savefig(save)
        fig.clf()
    plt.close(fig)
    
    
def plot_survey_responses(col, data, save=None):
    fig = plt.figure(figsize=(12,10))
    #No NA plot
    data_no_na = data.loc[data[col]!='Missing', :]
    if len(data_no_na) == 0:
        fig = plt.figure()
        plt.text(0.35, 0.5, 'Empty Column!')
        
    else:
        ax = sns.countplot(x=col, data=data_no_na)
        total = len(data_no_na[col])
        
        ylim = ax.get_ylim()
        
        for p in ax.patches:
                percentage = '{:.1f}% ({})'.format(100 * p.get_height()/total, p.get_height())
                x = p.get_x() + p.get_width() / 3
                y = p.get_y() + p.get_height() + ylim[1]*0.01
                ax.annotate(percentage, (x, y))
        ax.set_title(col + ' Value Counts')

        # Calculate different values
        #print(data_no_na[col])
        vals = data_no_na[col].astype(float)
        mu = np.mean(vals)
        var = np.var(vals)
        n_nas = len(data) - total
        percent_nas = round(n_nas/len(data) * 100, 2) 
        median = np.median(vals)

        textstr = '\n'.join((
        r'$\mu=%.2f$' % (mu, ),
        r'$\mathrm{median}=%.2f$' % (median, ),
        r'$\sigma^2=%.2f$' % (var, ),
        r'n_NAs={}%({})'.format(str(percent_nas), str(n_nas))))

        # these are matplotlib.patch.Patch properties
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        # place a text box in middle right in axes coords
        ax.text(1.05, 0.50, textstr, transform=ax.transAxes, fontsize=14,
                bbox=props)

        plt.subplots_adjust(right=0.75)
        fig = ax.get_figure()
    
    if save:
        fig.savefig(save)
        fig.clf()
        
    plt.close(fig)

    
def summary_stats(data, week, aligned, save_path):
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Column types to ignore:
    ig_cols = ['unchanged', 'text', 'numeric']

    # Clean up the column names, some of them contains unicode characters
    data_cols = list(data.columns)
    iteration = aligned.iterrows()
    data=data.loc[1:,:].fillna('Missing')

    # Skip the first row from the align table
    next(iteration)
    for row in iteration:
        # Get column names and lookup id from the aligned/items table
        column = row[1][week]
        lookup_id = row[1]['Question_type']
        new_col_name = row[1]['unified_variable_names']

        # Only run for columns that exist in the dataset
        if (column is not np.nan):
            str_col = str(new_col_name)
            if str_col in data_cols:
                
                # Plot single item
                path = save_path + str_col + '.png'
                if lookup_id == 'single_item':
                    plot_single_item(str_col, data, save=path)

                # Plot other number items
                elif lookup_id not in ig_cols:
                    plot_survey_responses(str_col, data, save=path)

            # A warning for situation that a column is found in the aligned table but not in the input data
            else:
                print("Warning: column '{}'/'{}' in aligned file is not a column of the data file.".format(column, str_col))


# Code for generating heatmaps, variance plots and stack distribution plots for the score items:

def concat_scores(score_files):
    # concat pilot and week 1
    pilot = pd.read_csv(score_files[0], encoding = "ISO-8859-1")
    pilot = pilot.rename(columns={pilot.columns[0]: 'PROLIFIC_PID'})
    week1 = pd.read_csv(scorefiles[1], encoding = "ISO-8859-1")
    week1 = week1.rename(columns={week1.columns[0]: 'PROLIFIC_PID'})

    
    # initialise dataframe with all weeks' data 
    score_data = pd.concat([pilot, week1], axis=0, sort=False)
    score_data.loc[:,'Week'] = 'Week1'

    # add other weeks to this dataframe
    for i in range(2,len(score_files)):

        # read data
        week_data = pd.read_csv(score_files[i], encoding = "ISO-8859-1")
        week_data = week_data.rename(columns={week_data.columns[0]: 'PROLIFIC_PID'})

        # remove repeated row (?) fom week 4
        if i == 4:
            week_data = week_data.drop(week_data.index[0])

        # add week column
        week_data.loc[:, 'Week'] = 'Week' + str(i)

        # add the week data to dataframe of all weeks' data
        score_data = pd.concat([score_data, week_data], axis=0, sort=False)


def df_of_question(question, score_data):
    num_weeks = len(set(score_data['Week']))
    week_keys = ['Week' + str(i) for i in range(1, num_weeks + 1)]
    question_data = score_data.loc[:,['PROLIFIC_PID', 'Week', question]]
    
    # initilise data frame containing weekly data for question
    df_weeks = question_data.loc[question_data['Week']=='Week1',:].drop('Week', axis=1)
    
    # fill data frame
    for i in range(1, num_weeks): 
        week = question_data.loc[question_data['Week']==week_keys[i],:].drop('Week', axis=1)
        df_weeks = pd.merge(df_weeks, week, how='left', on='PROLIFIC_PID')
    
    # rename columns
    week_keys.insert(0, 'ID')
    df_weeks.columns = week_keys
        
    return df_weeks
    

def plot_heatmap(values, question_name, save_path, cmap='bwr', na_color='black'):
    # plot heatmap
    plt.figure(figsize=(12, 12))
    g = sns.heatmap(values, cmap=cmap, mask=values.isnull())
    g.set_facecolor(na_color)
    g.get_yaxis().set_ticks([])
    plt.title('Heatmap of ' + str(question_name), size=30)
    plt.ylabel('Participants', size=20)
    
    # save heatmap
    path = save_path + '/heatmaps'
    if not os.path.exists(path):
        os.makedirs(path)
    plt.savefig(path + '/heatmap_' + str(question_name) + '.png', format="png")
    plt.close()
    
    
def plot_histogram(values, question_name, save_path, n_bins):
    # calculate variance for each participant, ignoring nans
    hist = []
    for index, rows in values.iterrows(): 
        my_list = [rows.Week1, rows.Week2, rows.Week3, rows.Week4] 
        hist.append(np.nanvar(my_list))
    
    # plot histogram --> bin size calculated from n bins
    bin_size = float((np.nanmax(hist) - np.nanmin(hist))/n_bins)
    plt.figure(figsize=(10, 10))
    plt.hist(hist, bins=np.arange(np.nanmin(hist), np.nanmax(hist) + bin_size, bin_size))
    plt.xlabel('Variance', size=20)
    plt.ylabel('Count', size=20)
    plt.title('Histogram of Variance for ' + str(question_name), size=30)
    
    # save histogram
    path = save_path + '/histograms/' + str(n_bins) + '_bins'
    if not os.path.exists(path):
        os.makedirs(path)
    plt.savefig(path + '/histogram_' + str(question_name) + '.png', format="png")
    plt.close()
    
    
def plot_stacked_bar_dist(values, question_name, save_path, n_segments):
    # generate bins
    sig_width = (values.max().max() - values.min().min())/n_segments
    bins = np.arange(values.min().min(), values.max().max() + sig_width, sig_width)
    labels = [i for i in range(len(bins)-1)]
    
    # bin values
    for i in range(len(values.columns)):
        values[values.columns[i]] = pd.cut(values[values.columns[i]], bins=bins, labels=labels, include_lowest=True)
        
    # count values for each week and concatentate
    weekly = [values[values.columns[i]].value_counts().sort_index() for i in range(len(values.columns))]
    stacked_bar = weekly[0]
    for i in range(1, len(values.columns)): 
        stacked_bar = pd.concat([stacked_bar, weekly[i]], axis=1)
        
    # generate legend labels and colours
    legend = [str(round(bins[i], 3)) + ' to ' + str(round(bins[i+1], 3)) for i in range(len(bins)-1)]
    
    # plot bar graph
    fig, ax = plt.subplots()
    stacked_bar.T.plot(kind='bar', stacked=True, ax=ax, colormap='summer')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], legend[::-1], loc='center left', bbox_to_anchor=(1, 0.5))
    plt.ylabel('Count', size=10)
    plt.title('Stacked Score Distribution for ' + str(question_name))
    
    # save bar graph
    path = save_path + '/stacked_distributions/' + str(n_segments) + '_segments'
    if not os.path.exists(path):
        os.makedirs(path)
    plt.savefig(path + '/stacked_dist_' + str(question_name) + '.png', format="png", bbox_inches='tight')
    plt.close()
    

def generate_graphs(score_data, question_name, save_path, n_bins, n_segments, heat, hist, bar):
    # get dataframe of weekly data for question
    df = df_of_question(question_name, score_data)
    
    # remove IDs, convert all values to floats
    values = df.drop('ID', axis=1)
    values = values.astype(float)
    
    # delete rows that have no values
    # values = values.dropna(axis=0, how='all')
    
    # generate a list with one value for each week: True if all values are nan
    # ignore data with only one week of data
    nulls = [values[values.columns[i]].isnull().all() for i in range(len(values.columns))]
    if nulls.count(False) < 2:
        return
    
    # sort by magnitude of first week of data
    first_week = nulls.index(False)
    values = values.sort_values(['Week' + str(first_week + 1)])
    
    # plot heatmap
    if heat:
        plot_heatmap(values, question_name, save_path)
    
    # plot histogram
    if hist:
        plot_histogram(values, question_name, save_path, n_bins)
    
    # plot stacked bar
    if bar:
        plot_stacked_bar_dist(values, question_name, save_path, n_segments)
    