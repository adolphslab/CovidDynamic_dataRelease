# imports
import pandas as pd
import numpy as np
import os


def check_items(text_file, clean_file):
    output_directory = os.path.split(clean_file)[0]
    name = os.path.split(clean_file)[1][:-4]

    # load original data
    text_items = pd.read_csv(text_file, encoding = "ISO-8859-1", dtype=str, keep_default_na=False, na_values='')
    text_items = text_items.iloc[1:] # delete first row
    text_items = text_items.applymap(str) # make all values strings
    text_columns = text_items.columns[1:] # get columns

    # load cleaned data
    cleaned = pd.read_csv(clean_file, encoding = "ISO-8859-1", dtype=str, keep_default_na=False, na_values='')
    cleaned = cleaned.iloc[1:] # delete first row
    cleaned = cleaned.applymap(str) # make all values strings
    cleaned_columns = cleaned.columns[1:] # get columns

    # init lists
    list_ones = []
    list_extra_nans = []
    list_no_idea = []

    # iterate over columns
    for col_num in range(len(text_columns)):

        # get column name for original and cleaned data
        tcol = text_columns[col_num]
        ccol = cleaned_columns[col_num]

        # get counts of values in the columns
        tvals = text_items[tcol].value_counts()
        cvals = cleaned[ccol].value_counts()

        # if the count lists are different
        if list(tvals) != list(cvals):

            # get list of unique values
            tlist = list(text_items[tcol].unique())
            clist = list(cleaned[ccol].unique())
            

            # get nan counts
            tnan = 0
            cnan = 0

            if 'nan' in tvals:
                tnan = tvals['nan']
            if 'nan' in cvals:
                cnan = cvals['nan']
                

            # check if columns are different becuase of 1.0 vs 1
            if (len(clist) == len(tlist) + 1) and '1.0' in clist and '1' in clist:
                list_ones.append(ccol)

            # check if one column has more nans than the other
            elif cnan > tnan:
                list_extra_nans.append(ccol)

            # other
            else:
                list_no_idea.append(ccol)

    # write lists of incorrect columns to textfile
    f = open(output_directory + "/errors_" + name + ".txt", "w")

    f.write("TWO WAYS TO WRITE ONE: 1 AND 1.0\n")
    for i in list_ones:
        f.write(str(i))
        f.write("\n")

    f.write("\nEXTRA NANS IN CLEANED\n")
    for i in list_extra_nans:
        f.write(str(i))
        f.write("\n")

    f.write("\nNO IDEA\n")
    for i in list_no_idea:
        f.write(str(i))
        f.write("\n")

    f.close()


def check_nums(text_file, clean_file):
    output_directory = os.path.split(clean_file)[0]
    name = os.path.split(clean_file)[1][:-4]

    # load original data
    text_items = pd.read_csv(text_file, encoding = "ISO-8859-1", dtype=str)
    text_items = text_items.iloc[1:] # delete first row
    text_items = text_items.applymap(str) # make all values strings
    text_columns = text_items.columns[1:] # get columns

    # load cleaned data
    cleaned = pd.read_csv(clean_file, encoding = "ISO-8859-1", dtype=str)
    cleaned = cleaned.iloc[1:] # delete first row
    cleaned = cleaned.applymap(str) # make all values strings
    cleaned_columns = cleaned.columns[1:] # get columns

    # init lists
    list_floats_vs_ints = []
    list_missing_one = []
    list_extra_nans = []
    list_no_idea = []

    # iterate over columns
    for col_num in range(len(text_columns)):

        # get column name for original and cleaned data
        tcol = text_columns[col_num]
        ccol = cleaned_columns[col_num]

        # get counts of values in the columns
        tvals = text_items[tcol].value_counts()
        cvals = cleaned[ccol].value_counts()

        # if the count lists are different
        if list(tvals) != list(cvals):

            # get list of unique values
            tlist = list(text_items[tcol].unique())
            clist = list(cleaned[ccol].unique())

            # get nan counts
            tnan = 0
            cnan = 0

            if 'nan' in tvals:
                tnan = tvals['nan']
            if 'nan' in cvals:
                cnan = cvals['nan']

            try:
                tlist_ints = set([int(float(i)) for i in tlist if i != 'nan'])
                clist_ints = set([int(float(i)) for i in clist if i != 'nan'])
            except ValueError:
                tlist_ints = set([int(float(i)) for i in tlist if i != 'nan'])
                clist_ints = set([i for i in clist if i != 'nan'])

            # check if missing one value:
            if len(tlist_ints) - len(clist_ints) == 1:
                list_missing_one.append(ccol)

            # check if one column has more nans than the other
            elif cnan > tnan:
                list_extra_nans.append(ccol)

            # ignore if columns are different becuase of float vs int
            elif tlist_ints == clist_ints:
                pass

            # ignore if just been reorded to be sequential
            elif len(tlist_ints) == len(clist_ints):
                pass

            # check if one-hot encoded
            elif sorted(clist) == sorted(['nan', str(float(ccol[-1]))]):
                pass

            # other
            else:
                list_no_idea.append(ccol)

    # write lists of incorrect columns to textfile
    f = open(output_directory + "/errors_nums_" + name + ".txt", "w")

    f.write("MISSING ONE VALUE IN CLEANED\n")
    for i in list_missing_one:
        f.write(str(i))
        f.write("\n")

    f.write("\nEXTRA NANS IN CLEANED\n")
    for i in list_extra_nans:
        f.write(str(i))
        f.write("\n")

    f.write("\nNO IDEA\n")
    for i in list_no_idea:
        f.write(str(i))
        f.write("\n")

    f.close()
