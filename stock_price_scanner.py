# Python practice
# This script pulls BABA, MOMO, and AMZN current stock prices.

import bs4 as bs
import urllib.request

source = urllib.request.urlopen('http://www.investopedia.com/markets/stocks/baba/').read()

soup = bs.BeautifulSoup(source, 'lxml')
baba = float(soup.td.string)
flux = list(soup.find('td', attrs={'class': 'value-change'}).string)
net_change = ""
i = 0

while flux[i] != ' ':
    net_change += flux[i]
    i += 1;

print("Current price of BABA:   ", baba)
print("Yeserday's price of BABA:", baba + float(net_change))
print("Change since yesterday:  ", soup.find('td', attrs={'class': 'value-change'}).string)


source2 = urllib.request.urlopen('http://www.investopedia.com/markets/stocks/momo/').read()

soup2 = bs.BeautifulSoup(source2, 'lxml')

print("Current price of MOMO:    " + soup2.td.string)

source3 = urllib.request.urlopen('http://www.investopedia.com/markets/stocks/AMZN/').read()

soup3 = bs.BeautifulSoup(source3, 'lxml')

print("Current price of AMZN:    " + soup3.td.string)
