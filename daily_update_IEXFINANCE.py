#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Fri May  4 12:50:33 2018

@author: Shuai
"""

from pandas import DataFrame
from iexfinance import get_historical_data
from math import sqrt
import pandas as pd
import time
import datetime
import os
from sqlalchemy import create_engine


last_date = datetime.datetime.today()
start_date = last_date + datetime.timedelta(days=-7)


# =============================================================================
# Definitions of Functions
# =============================================================================
def load_company_list():
    cwd = os.getcwd()
    return pd.read_csv(cwd + '\\company_list.txt', header=None, names=['company_name'])


def get_list_data(ticker_list):
    data = pd.DataFrame()
    repeat = 0
    error_list = []
    while len(ticker_list) > 0 and repeat <= 5:
        num_companies = len(ticker_list)
        for i in range(num_companies):
            ticker = ticker_list[i]
            try:
                temp = get_historical_data(ticker, start=start_date, end=last_date, output_format='pandas')
                temp['ticker'] = ticker
                data = pd.concat([data, temp])
                # data['ticker'] = ticker
                print('{0} done! {1} done, {2} error, {3} left!'.format(ticker, i + 1 - len(error_list), len(error_list), num_companies - i - 1))
            except:
                error_list.append(ticker)
                print('{0} Error! {1} done, {2} error, {3} left!'.format(ticker, i + 1 - len(error_list), len(error_list), num_companies - i - 1))
                # time.sleep(1)
        if len(ticker_list) == len(error_list):
            repeat += 1
        ticker_list = error_list
        error_list = []
        print('Restart!')
    print('Done')
    return data


def run_sql(data_input, table, columns):
    """
    connection = mysql.connector.connect(host='localhost',
                                 port=3306,
                                 user='martin',
                                 password='DWL,iloveyou',
                                 database='company_data')
    """
    # Connect to the database
    engine = create_engine('mysql+mysqlconnector://martin:DWL,iloveyou@localhost/company_data')
    data_input.columns = columns
    data_input.to_sql(name=table, con=engine, index=True, index_label='date', if_exists='append')


# =============================================================================
# Main Function
# =============================================================================
if __name__ == '__main__':
    tickers = list(load_company_list()['company_name'])
    daily_data = get_list_data(tickers)
    column_names = ['open', 'high', 'low', 'close', 'volume', 'ticker']
    engine = create_engine('mysql+mysqlconnector://martin:DWL,iloveyou@localhost/company_data')
    daily_data.to_sql(name='ts_daily', con=engine, index=True, index_label='date', if_exists='append')
    print('Done')
