#!/usr/bin/env python3
import json
import os
import datetime
from urllib import request
from prettytable import PrettyTable

eth_json = os.path.expanduser('~') + '/.eth.json'
if not os.path.isfile(eth_json):
    print('Error: Config file %s missing. Copy eth_aud.json to %s and configure as required.' % (eth_json, eth_json))
    exit(1)
else:
    with open(eth_json) as eth_file:
        eth_trans = json.load(eth_file)

current = PrettyTable(['ETH/AUD', 'ETH/USD', 'ETH/mBTC', '% 1h', '% 24h', '% 7d', 'Mkt Cap AUD'])
with request.urlopen('https://api.coinmarketcap.com/v1/ticker/ethereum/?convert=AUD') as url:
    data = json.loads(url.read().decode())
    update = datetime.datetime.fromtimestamp(
        int(data[0]['last_updated'])
        ).strftime('%Y-%m-%d %H:%M:%S')
    eth_aud = float(data[0]['price_aud'])
    eth_usd = float(data[0]['price_usd'])
    eth_btc = float(data[0]['price_btc']) * 1000
    pct_1h = data[0]['percent_change_1h'] + '%'
    pct_1d = data[0]['percent_change_24h'] + '%'
    pct_7d = data[0]['percent_change_7d'] + '%'
    mkt_aud = '$' + '{:,.0f}'.format(float(data[0]['market_cap_aud']))
    current.add_row(['$%.2f' % eth_aud, '$%.2f' % eth_usd, '%.2f' % eth_btc, pct_1h, pct_1d, pct_7d, mkt_aud])

print('Data updated at %s:' % update)
print(current)

table = PrettyTable(['Date', 'Ethereum', 'AUD buy', 'AUD now', 'Profit'])

for trans in eth_trans:
    eth_purchase = float(trans['aud']) / float(trans['eth'])
    aud_now = float(trans['eth']) * eth_aud
    profit_aud = aud_now - float(trans['aud'])
    table.add_row([trans['date'], trans['eth'], '$%s' % trans['aud'], '$%.2f' % aud_now, '$%.2f' % profit_aud])

print('Portfolio:')
print(table)
