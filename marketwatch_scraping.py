# Version 1.0
# Created by Martin Qian
# Last Update Date: 06/06/18
#-*-coding:utf-8-*-


import requests
import pandas as pd
from lxml import html
from bs4 import BeautifulSoup as soup

ticker = 'AAPL'
my_url = 'https://www.marketwatch.com/investing/stock/{0}/financials'.format(ticker)
data = {}
data[ticker] = pd.DataFrame()

page = requests.get(my_url)
# tree = html.fromstring(page.text)
page_soup = soup(page.text, "lxml")

# years = [x.text for x in tree.cssselect('.financials > table > thead > tr > th[scope]')]
# years = tree.xpath('//*[@id="maincontent"]/div[1]/table[1]/thead/tr/th')
years = [x.text for x in page_soup.select('div.financials > table:nth-of-type(1) > thead > tr > th[scope]')][:5]

# indicators = tree.cssselect('.rowTitle')
indicators =  page_soup.select('.rowTitle')[1:]
for x in indicators:
    try:
        data[ticker][x.text.strip()] = [i.text.strip() for i in x.find_next_siblings('td',{'class':'valueCell'})]
    except:
        continue
        
data[ticker].insert(0,'year',years)
data[ticker].insert(0,'ticker',ticker)

print('Done')


