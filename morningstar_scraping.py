# Created by Martin Qian
# Date: 06-27-2018
# Encoding: UTF-8

from selenium import webdriver
from lxml import html
import pandas as pd


def login_ticker(browser, ticker, sheet='is'):
    # A function to load the url of certain financial info of certain stock
    base_url = 'https://financials.morningstar.com/income-statement/{1}.html?t={0}&culture=en-US&platform=sal'.format(ticker, sheet)
    browser.get(base_url)
