#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Fri May  4 12:50:33 2018

@author: Shuai
"""

from pandas import DataFrame
from alpha_vantage.timeseries import TimeSeries
from math import sqrt
import pandas as pd
import time
import datetime
import os


api_key = 'FYWQFVRIHCJFJ893'
last_date = datetime.date(2018, 7, 20)


# =============================================================================
# Definitions of Functions
# =============================================================================
def get_data(ticker):
    ts = TimeSeries(key=api_key, output_format='pandas')
    data, meta_data = ts.get_daily(symbol=ticker, outputsize='compact')
    return data


def load_company_list():
    cwd = os.getcwd()
    return pd.read_csv(cwd + '\\company_list.txt', header=None, names=['company_name'])


def get_list_data(ticker_list):
    data = pd.DataFrame()
    repeat = 0
    error_list = []
    while len(ticker_list) > 0 and repeat <= 50:
        num_companies = len(ticker_list)
        for i in range(num_companies):
            ticker = ticker_list[i]
            try:
                temp = get_data(ticker)
                temp['ticker'] = ticker
                data = pd.concat([data, temp])
                # data['ticker'] = ticker
                print('{0} done! {1} done, {2} error, {3} left!'.format(ticker, i + 1 - len(error_list), len(error_list), num_companies - i - 1))
            except:
                error_list.append(ticker)
                print('{0} Error! {1} done, {2} error, {3} left!'.format(ticker, i + 1 - len(error_list), len(error_list), num_companies - i - 1))
                time.sleep(1)
        if len(ticker_list) == len(error_list):
            repeat += 1
        ticker_list = error_list
        error_list = []
        print('Restart!')
    print('Done')
    return data


# =============================================================================
# Main Function
# =============================================================================
if __name__ == '__main__':
    tickers = list(load_company_list()['company_name'])
    daily_data = get_list_data(tickers)
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    column_names = ['open', 'high', 'low', 'close', 'volume', 'ticker']
    daily_data.to_csv(os.getcwd() + '//daily_{0}.csv'.format(today), header=column_names)
    print('Done')
