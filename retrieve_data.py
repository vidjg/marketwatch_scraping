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


api_key = 'JSPV785VY6KZQTOQ'


# =============================================================================
# Portfolio Management
# =============================================================================
def get_data(ticker):
    ts = TimeSeries(key=api_key, output_format='pandas')
    data, meta_data = ts.get_daily(symbol=ticker, outputsize='full')
    return data


def get_close(ticker, size='compact', length=252):
    # Get closes of stock in certain period of time
    ts = TimeSeries(key=api_key, output_format='pandas')
    data, meta_data = ts.get_daily(symbol=ticker, outputsize=size)
    return data.iloc[-length:, 3]


def get_pool(tickers, size='compact', length=252):
    # Get data of closes and store them in a DataFrame
    pool = DataFrame()

    for i in tickers:
        stock_close = get_close(i, size, length)
        pool[i] = stock_close.tolist()
        if i == tickers[0]:
            pool.index = stock_close.index

    return pool


def cal_sharpe_ratio(pool, dist):
    # Calculate Sharpe Ratio from the stock inputs

    # Get Cumulative Return and Returns of the portfolio
    port_cum = (pool * dist).sum(axis=1)
    port_rets = port_cum / port_cum.shift() - 1
    port_rets = port_rets[1:]

    # Calculate Sharpe Ratio
    avg_ret = port_rets.mean()
    std = port_rets.std()
    sharpe_ratio = avg_ret / std * sqrt(len(port_rets))

    return round(sharpe_ratio, 2)


def optimize(pool, unit):
    # Optimize the portfolio of certain stocks
    dist = [1.00] + [0.00] * (len(pool.columns) - 1)
    dist_best = dist
    sharpe_best = -1
    num = len(pool.columns)
    dists = num_dist(num, unit)

    for x in dists:
        sharpe_curr = cal_sharpe_ratio(pool, [round(i * 0.01, 2) for i in x])
        if sharpe_curr > sharpe_best:
            dist_best = [round(i * 0.01, 2) for i in x]
            sharpe_best = sharpe_curr

    return [round(sharpe_best, 2), dist_best]


def pool_data(pool):
    # Gather data of stocks from stock pool

    stocks = DataFrame()

    tickers = []
    rets = []
    s_ratios = []

    for x in pool:
        tickers.append(x)
        stock_close = pool[x]
        stock_rets = (stock_close / stock_close.shift(1) - 1)[1:]
        stock_avg_ret = stock_rets.mean()
        stock_sharpe = stock_avg_ret / stock_rets.std() * sqrt(len(stock_rets))
        rets.append(round(stock_avg_ret, 4))
        s_ratios.append(round(stock_sharpe, 2))

    stocks['ticker'] = tickers
    stocks['avg_ret'] = rets
    stocks['sharpe'] = s_ratios

    return stocks


def num_dist(num, unit):
    # Distribute Numbers among list
    result = []
    # unit = 10
    r = [0] * num

    def ff(n, m, r):
        if m == 1:
            result.append([n] + r[1:])
        else:
            for i in range(int(n / unit) + 1):
                r[m - 1] = unit * i
                ff(n - i * unit, m - 1, r)

    ff(100, num, r)
    return result


# =============================================================================
# Backtest Module
# =============================================================================

def get_intraday(ticker, length=1, size='full'):
    # Get closes of stock in certain period of time
    ts = TimeSeries(key=api_key, output_format='pandas')
    data, meta_data = ts.get_intraday(symbol=ticker, interval='1min', outputsize=size)
    return data.iloc[-length * 391:, 3]


def backtest(pool, strategy, dist=1):
    # Backtest the trading strategy on the stocks in the pool in certain period
    trade_start_lag = 30

    # Create a DataFrame to record signals for each stock
    pool = DataFrame(pool)
    trade_records = pool.copy()
    positions = pool.copy()
    trade_records.iloc[:] = 0
    positions.iloc[:] = 0

    pool_rets = (pool / pool.shift() - 1)

    port_capital = trade_records.copy()
    port_capital.iloc[trade_start_lag - 1] = pool.iloc[trade_start_lag - 1] * dist

    for x in pool:
        for i in range(trade_start_lag, len(pool)):
            trade_records[x][i] = strategy(pool[x][:i])

            # Change the position based on signals
            if trade_records[x][i] == 1 and positions[x][i] <= 0:
                positions[x][i] = 1
            elif trade_records[x][i] == -1 and positions[x][i] >= 0:
                positions[x][i] = -1
            elif trade_records[x][i] == 2 and positions[x][i] != 0:
                positions[x][i] = 0
            else:
                positions[x][i] = positions[x][i - 1]

            # Change the capital based on the positions
            if positions[x][i - 1] == 1:
                port_capital[x][i] = port_capital[x][i - 1] * (1 + pool_rets[x][i])
            elif positions[x][i - 1] == -1:
                port_capital[x][i] = port_capital[x][i - 1] * (1 - pool_rets[x][i])
            else:
                port_capital[x][i] = port_capital[x][i - 1]

    trade_records = trade_records[trade_start_lag:]
    positions = positions[trade_start_lag:]
    port_capital = port_capital[trade_start_lag:]

    port_ret = sum(port_capital.iloc[-1]) / sum(port_capital.iloc[0]) - 1

    return [port_capital, positions, port_ret]


# =============================================================================
# Trading Strategies
# =============================================================================

def s_moving_average(fast=5, slow=30):
    # Long if fast MA cross upwards; Short if fast MA cross downwards
    def signal(closes):
        if fast < slow and len(closes) > (slow + 1):
            ma_f = [closes[-fast - 1:-1].mean(), closes[-fast:].mean()]
            ma_s = [closes[-slow - 1:-1].mean(), closes[-slow:].mean()]
            #            print([ma_f, ma_s])
            if ma_f[0] < ma_s[0] and ma_f[1] > ma_s[1]:
                return 1
            elif ma_f[0] > ma_s[0] and ma_f[1] < ma_s[1]:
                return -1
            else:
                return 0
        else:
            return 0

    return signal

# =============================================================================
# Debugging and Testing
# =============================================================================
# pool = get_pool(['AAPL','MSFT'])
# ans = backtest(pool, s_moving_average(5,15), [0.5,0.5])


# =============================================================================
# Main Function
# =============================================================================
if __name__ == '__main__':
    ticker_list = ['ABT', 'ABBV', 'ACN', 'ACE', 'ADBE', 'ADT', 'AAP', 'AES', 'AET', 'AFL', 'AMG', 'A', 'GAS', 'APD',
                   'ARG', 'AKAM', 'AA', 'AGN', 'ALXN', 'ALLE', 'ADS', 'ALL', 'ALTR', 'MO', 'AMZN', 'AEE', 'AAL', 'AEP',
                   'AXP', 'AIG', 'AMT', 'AMP', 'ABC', 'AME', 'AMGN', 'APH', 'APC', 'ADI', 'AON', 'APA', 'AIV', 'AMAT',
                   'ADM', 'AIZ', 'T', 'ADSK', 'ADP', 'AN', 'AZO', 'AVGO', 'AVB', 'AVY', 'BHI', 'BLL', 'BAC', 'BK',
                   'BCR', 'BXLT', 'BAX', 'BBT', 'BDX', 'BBBY', 'BRK-B', 'BBY', 'BLX', 'HRB', 'BA', 'BWA', 'BXP', 'BSK',
                   'BMY', 'BRCM', 'BF-B', 'CHRW', 'CA', 'CVC', 'COG', 'CAM', 'CPB', 'COF', 'CAH', 'HSIC', 'KMX', 'CCL',
                   'CAT', 'CBG', 'CBS', 'CELG', 'CNP', 'CTL', 'CERN', 'CF', 'SCHW', 'CHK', 'CVX', 'CMG', 'CB', 'CI',
                   'XEC', 'CINF', 'CTAS', 'CSCO', 'C', 'CTXS', 'CLX', 'CME', 'CMS', 'COH', 'KO', 'CCE', 'CTSH', 'CL',
                   'CMCSA', 'CMA', 'CSC', 'CAG', 'COP', 'CNX', 'ED', 'STZ', 'GLW', 'COST', 'CCI', 'CSX', 'CMI', 'CVS',
                   'DHI', 'DHR', 'DRI', 'DVA', 'DE', 'DLPH', 'DAL', 'XRAY', 'DVN', 'DO', 'DTV', 'DFS', 'DISCA', 'DISCK',
                   'DG', 'DLTR', 'D', 'DOV', 'DOW', 'DPS', 'DTE', 'DD', 'DUK', 'DNB', 'ETFC', 'EMN', 'ETN', 'EBAY',
                   'ECL', 'EIX', 'EW', 'EA', 'EMC', 'EMR', 'ENDP', 'ESV', 'ETR', 'EOG', 'EQT', 'EFX', 'EQIX', 'EQR',
                   'ESS', 'EL', 'ES', 'EXC', 'EXPE', 'EXPD', 'ESRX', 'XOM', 'FFIV', 'FB', 'FAST', 'FDX', 'FIS', 'FITB',
                   'FSLR', 'FE', 'FSIV', 'FLIR', 'FLS', 'FLR', 'FMC', 'FTI', 'F', 'FOSL', 'BEN', 'FCX', 'FTR', 'GME',
                   'GPS', 'GRMN', 'GD', 'GE', 'GGP', 'GIS', 'GM', 'GPC', 'GNW', 'GILD', 'GS', 'GT', 'GOOGL', 'GOOG',
                   'GWW', 'HAL', 'HBI', 'HOG', 'HAR', 'HRS', 'HIG', 'HAS', 'HCA', 'HCP', 'HCN', 'HP', 'HES', 'HPQ',
                   'HD', 'HON', 'HRL', 'HSP', 'HST', 'HCBK', 'HUM', 'HBAN', 'ITW', 'IR', 'INTC', 'ICE', 'IBM', 'IP',
                   'IPG', 'IFF', 'INTU', 'ISRG', 'IVZ', 'IRM', 'JEC', 'JBHT', 'JNJ', 'JCI', 'JOY', 'JPM', 'JNPR', 'KSU',
                   'K', 'KEY', 'GMCR', 'KMB', 'KIM', 'KMI', 'KLAC', 'KSS', 'KRFT', 'KR', 'LB', 'LLL', 'LH', 'LRCX',
                   'LM', 'LEG', 'LEN', 'LVLT', 'LUK', 'LLY', 'LNC', 'LLTC', 'LMT', 'L', 'LOW', 'LYB', 'MTB', 'MAC', 'M',
                   'MNK', 'MRO', 'MPC', 'MAR', 'MMC', 'MLM', 'MAS', 'MA', 'MAT', 'MKC', 'MCD', 'MHFI', 'MCK', 'MJN',
                   'MMV', 'MDT', 'MRK', 'MET', 'KORS', 'MCHP', 'MU', 'MSFT', 'MHK', 'TAP', 'MDLZ', 'MON', 'MNST', 'MCO',
                   'MS', 'MOS', 'MSI', 'MUR', 'MYL', 'NDAQ', 'NOV', 'NAVI', 'NTAP', 'NFLX', 'NWL', 'NFX', 'NEM', 'NWSA',
                   'NEE', 'NLSN', 'NKE', 'NI', 'NE', 'NBL', 'JWN', 'NSC', 'NTRS', 'NOC', 'NRG', 'NUE', 'NVDA', 'ORLY',
                   'OXY', 'OMC', 'OKE', 'ORCL', 'OI', 'PCAR', 'PLL', 'PH', 'PDCO', 'PAYX', 'PNR', 'PBCT', 'POM', 'PEP',
                   'PKI', 'PRGO', 'PFE', 'PCG', 'PM', 'PSX', 'PNW', 'PXD', 'PBI', 'PCL', 'PNC', 'RL', 'PPG', 'PPL',
                   'PX', 'PCP', 'PCLN', 'PFG', 'PG', 'PGR', 'PLD', 'PRU', 'PEG', 'PSA', 'PHM', 'PVH', 'QRVO', 'PWR',
                   'QCOM', 'DGX', 'RRC', 'RTN', 'O', 'RHT', 'REGN', 'RF', 'RSG', 'RAI', 'RHI', 'ROK', 'COL', 'ROP',
                   'ROST', 'RLC', 'R', 'CRM', 'SNDK', 'SCG', 'SLB', 'SNI', 'STX', 'SEE', 'SRE', 'SHW', 'SIAL', 'SPG',
                   'SWKS', 'SLG', 'SJM', 'SNA', 'SO', 'LUV', 'SWN', 'SE', 'STJ', 'SWK', 'SPLS', 'SBUX', 'HOT', 'STT',
                   'SRCL', 'SYK', 'STI', 'SYMC', 'SYY', 'TROW', 'TGT', 'TEL', 'TE', 'TGNA', 'THC', 'TDC', 'TSO', 'TXN',
                   'TXT', 'HSY', 'TRV', 'TMO', 'TIF', 'TWX', 'TWC', 'TJK', 'TMK', 'TSS', 'TSCO', 'RIG', 'TRIP', 'FOXA',
                   'TSN', 'TYC', 'UA', 'UNP', 'UNH', 'UPS', 'URI', 'UTX', 'UHS', 'UNM', 'URBN', 'VFC', 'VLO', 'VAR',
                   'VTR', 'VRSN', 'VZ', 'VRTX', 'VIAB', 'V', 'VNO', 'VMC', 'WMT', 'WBA', 'DIS', 'WM', 'WAT', 'ANTM',
                   'WFC', 'WDC', 'WU', 'WY', 'WHR', 'WFM', 'WMB', 'WEC', 'WYN', 'WYNN', 'XEL', 'XRX', 'XLNX', 'XL',
                   'XYL', 'YHOO', 'YUM', 'ZBH', 'ZION', 'ZTS']
    data = pd.DataFrame()
    i = 0
    error_list = []
    while 1:
        while i < len(ticker_list):
            ticker = ticker_list[i]
            try:
                temp = get_data(ticker)
                temp['ticker'] = ticker
                temp.to_csv('stock_data.csv', header=False, mode='a', encoding='utf-8')
                i += 1
                print('{0} finished! {1:.2f}%'.format(ticker, 100 * i/len(ticker_list)))
            except ValueError:
                print('{0} Error!'.format(ticker))
                error_list.append(ticker)
                time.sleep(5)
                i += 1
                continue
        if len(error_list) == 0:
            break
        else:
            ticker_list = error_list
            error_list = []
            i = 0
            print('Restart!')
            time.sleep(5)