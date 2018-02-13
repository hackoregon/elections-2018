# %cd /home/mbodenator/Documents/hack_oregon
import pandas as pd
import requests
from lxml import html

s = requests.Session()
transaction_headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Origin':'https://secure.sos.state.or.us'}
transaction_ids = ['2540704','2540705','2540706','2540707','2540708']
rows = []
for tid in transaction_ids:
    transaction_url = 'https://secure.sos.state.or.us/orestar/gotoPublicTransactionDetail.do?tranRsn={}'.format(tid)
    t = s.get(transaction_url,headers=transaction_headers)
    body = html.fromstring(t.text)
    body.xpath('//*[@id="content"]/div/form/fieldset/table/tr[15]/td[3]/text()')
    # grabbing the info in the left column
    dict1 = {el.xpath('td[1]/text()')[0].strip():', '.join([subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ') for subel in el.xpath('td[3]/text()')]) for el in body.xpath('//*[@id="content"]/div/form/fieldset/table/tr')[1:] if el.xpath('td[1]/text()')[0].strip()}
    # grabbing the info in the right column
    dict2 = {el.xpath('td[4]/text()')[0].strip():', '.join([subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ') for subel in el.xpath('td[6]/text()')]) for el in body.xpath('//*[@id="content"]/div/form/fieldset/table/tr')[1:] if el.xpath('td[4]/text()') and el.xpath('td[4]/text()')[0].strip()}
    dict1.update(dict2)
    rows.append(dict1)
df = pd.DataFrame(rows)
df.to_csv('transaction_detail_sample.csv',index=False)
