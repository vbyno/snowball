# import sys
import fire
import configparser
import time
import re
import os
import psutil
import jsonlines
from nltk.stem.porter import *
from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np


def do_clear_terms(config=None,
                 dir_in_terms=None,  #
                 dir_out_terms=None,
                 trace=0
                 ):
    """

    :param config:
    :param in_terms: input TXT file
    :param out_terms: output CSV file containing terms
    :param stopwords: text file containing stopwords, one word per row
    :param trace: show detailed information about execution
    :return:
    """

    conf = configparser.ConfigParser()
    conf.read_file(open(config))

    data_dir = conf.get('main', 'data_dir')
    trace = (int(trace) == 1)

    # =====================================================
    # place to read partial term lists
    if dir_in_terms is None:
        dir_in_terms = f'{data_dir}/terms_partial'
    print(('dir_in_terms', dir_in_terms))
    # =====================================================

    # =====================================================
    # place to write merged term lists
    if dir_out_terms is None:
        dir_out_terms = f'{data_dir}/terms'
    print(('dir_out_terms', dir_out_terms))
    # =====================================================

    partial_term_files = sorted([join(dir_in_terms, f) for f in listdir(dir_in_terms) if isfile(join(dir_in_terms, f)) and f.lower().endswith(".txt")])

    cumulative_terms = []
    file_counter = 0
    for partial_term_file in partial_term_files:
        # append partial terms to cumulative_terms
        with jsonlines.open(partial_term_file) as reader:
            cumulative_terms.extend([row for row in reader])

        # do aggregation
        df_raw = pd.DataFrame(data=cumulative_terms, columns=['term', 'cvalue'])
        df_cumulative = df_raw.groupby(['term'])['cvalue'].agg([np.sum])
        df_cumulative.columns = ['cvalue']
        df_cumulative.sort_values(by='cvalue', ascending=False, inplace=True)
        print(('partial_term_file', partial_term_file))
        print(df_cumulative.head())

        # write next term list to file
        file_counter += 1
        terms_file_path = join(dir_out_terms, 'T' + (('00000000000000000' + str(file_counter))[-10:]) + '.txt')

        with jsonlines.open(terms_file_path, mode='w') as writer:
            for term in df_cumulative.index:
                writer.write([term, df_cumulative.loc[term]['cvalue']])


if __name__ == "__main__":
    t0 = time.time()
    fire.Fire(do_clear_terms)
    t1 = time.time()
    print("finished")
    print(("time", t1 - t0,))
    process = psutil.Process(os.getpid())
    print('used RAM(bytes)=', process.memory_info().rss)  # in bytes

