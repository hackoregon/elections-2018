%cd /home/mbodenator/Documents/hack_oregon/elections-2018-master
import pandas as pd
import requests
from lxml import html
import time
import logging
from datetime import datetime

logging.basicConfig(filename='logs/transactions_totals_scrape_{:%m%d%y%H%M%S}.log'.format(datetime.now()),level=logging.INFO)

def transactions_scrape(committee_id):
    """ scrape up to 10k transactions for the provided committee id """
    logging.info('committee_id: {}'.format(committee_id))
    s = requests.Session()
    transaction_url = 'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearchResults.do'
    headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Origin':'https://secure.sos.state.or.us',
            'Referer':'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearch.do'}
    data = {'cneSearchButtonName':'search','cneSearchPageIdx':'0','cneSearchFilerCommitteeId':str(committee_id),'cneSearchFilerCommitteeTxtSearchType':'C','cneSearchContributorTxtSearchType':'C',
            'OWASP_CSRFTOKEN':'F251-AX8K-O7SW-7E36-3D0C-23S8-ILBF-OPOB'}
    time.sleep(15)
    r = s.post(transaction_url,headers=headers,data=data)
    logging.info('initial status_code: {}'.format(r.status_code))
    # if orestar is blocking requests, exit the scraper
    body = html.fromstring(r.text)
    if r.status_code == 403:
        return ''
    else:
        results = body.xpath('//*[@id="content"]/div/form/table[3]/tr[3]/td[2]/text()')[0].strip().split()[0]
        return results
    # grab header row from the top from the transaction table
    # headers = [el.text_content().strip() for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr[1]/th')]
    # rows = [[subel.text_content().strip() for subel in el.xpath('td')] for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr')[1:]]
committees = pd.read_csv('committees_list.tsv',sep='\t')
committees_ids = list(committees['ID'])
totals_rows = []
committees_ids.index(5789)
for cid in committees_ids[1150:1200]:
    totals_rows.append((cid,transactions_scrape(cid)))
totals_rows
df = pd.DataFrame(totals_rows,columns=['committee_id','total_transactions'])
df_clean = df.loc[df.total_transactions != '',:]
df_clean.info()
df_clean.to_csv('transcation_totals24.csv',index=False)
