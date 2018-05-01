# %cd /home/mbodenator/Documents/hack_oregon/elections-2018-master
import pandas as pd
import requests
from lxml import html
import logging
from datetime import datetime
import sys

logging.basicConfig(filename='logs/transaction_detail_scrape_{:%m%d%y%H%M%S}.log'.format(datetime.now()),level=logging.INFO)
file_num = sys.argv[-1]
# file_num = 4
# pull transactions ids from list of transactions
transactions = pd.read_csv('transactions_gaps{}.csv'.format(file_num))
transactions_list = list(transactions['Tran ID'])
# transactions_list[:10]
# transactions_list.index(2055319)
# transactions_list[123]
# 2055319 in transactions_list
s = requests.Session()
transaction_headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Origin':'https://secure.sos.state.or.us'}
rows = []
# transactions_list = [2345624]
for tid in transactions_list:
    logging.info('transaction_id: {}'.format(tid))
    transaction_url = 'https://secure.sos.state.or.us/orestar/gotoPublicTransactionDetail.do?tranRsn={}'.format(tid)
    t = s.get(transaction_url,headers=transaction_headers)
    logging.info('status_code: {}'.format(t.status_code))
    body = html.fromstring(t.text)
    # grabbing the info in the left column
    dict1 = {el.xpath('td[1]/text()')[0].strip():', '.join([subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ') for subel in el.xpath('td[3]/text()') if subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ')]) for el in body.xpath('//*[@id="content"]/div/form/fieldset/table/tr')[1:] if el.xpath('td[1]/text()')[0].strip()}
    # grabbing the info in the right column
    dict2 = {el.xpath('td[4]/text()')[0].strip():', '.join([subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ') for subel in el.xpath('td[6]/text()') if subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ')]) for el in body.xpath('//*[@id="content"]/div/form/fieldset/table/tr')[1:] if el.xpath('td[4]/text()') and el.xpath('td[4]/text()')[0].strip()}
    dict1.update(dict2)
    rows.append(dict1)
df = pd.DataFrame(rows)
# df.info()
df.fillna('',inplace=True)
df['Aggregate'] = df.Aggregate.apply(lambda a: a.replace('$','').replace(',','').replace(')','').replace('(','-') if a else 0).astype(float)
# [v for v in df['Aggregate'].values if type(v) == float]
# df.groupby('Aggregate').size().sort_values(ascending=False)
df['Amount'] = df.Amount.apply(lambda a: a.replace('$','').replace(',','').replace(')','').replace('(','-') if a else 0).astype(float)
# df.info()
# print(df.info())
df.to_csv('transaction_detail{}.csv'.format(file_num),index=False)
