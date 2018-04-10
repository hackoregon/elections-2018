# %cd /home/mbodenator/Documents/hack_oregon/elections-2018-master
import pandas as pd
import requests
from lxml import html
import time
from math import ceil
# import logging
from datetime import datetime
import sys

# logging.basicConfig(filename='logs/transaction_scrape_{:%m%d%y%H%M%S}.log'.format(datetime.now()),level=logging.INFO)

def transaction_further_pages(committee_id,page,session):
    next_url = 'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearchResults.do?cneSearchButtonName=next&cneSearchFilerCommitteeId={0}&cneSearchContributorTxtSearchType=C&cneSearchFilerCommitteeTxtSearchType=C&cneSearchPageIdx={1}'.format(committee_id,page)
    headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                'Origin':'https://secure.sos.state.or.us',
                'Referer':'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearchResults.do'}
    time.sleep(5)
    t = session.get(next_url,headers=headers)
    body = html.fromstring(t.text)
    # grab header row from the top from the transaction table
    headers = [el.text_content().strip() for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr[1]/th')]
    rows = []
    for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr')[1:]:
        row = [subel.text_content().strip() for subel in el.xpath('td')]
        row.append(el.xpath('td[4]/a')[0].attrib['href'].split('=')[-1] if el.xpath('td[4]/a') else '')
        rows.append(row)
    headers.append('committee_id')
    if rows and rows[0] and rows[0][0][:7] != 'No data':
        next_df = pd.DataFrame(rows, columns=headers)
    else:
        next_df = []
    return next_df,session

def transactions_scrape(committee_id):
    """ scrape up to 10k transactions for the provided committee id """
    # logging.info('committee_id: {}'.format(committee_id))
    s = requests.Session()
    transaction_url = 'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearchResults.do'
    headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Origin':'https://secure.sos.state.or.us',
            'Referer':'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearch.do'}
    data = {'cneSearchButtonName':'search','cneSearchPageIdx':'0','cneSearchFilerCommitteeId':str(committee_id),'cneSearchFilerCommitteeTxtSearchType':'C','cneSearchContributorTxtSearchType':'C',
            'cneSearchTranStartDate':start,'cneSearchTranEndDate':end,'OWASP_CSRFTOKEN':'F251-AX8K-O7SW-7E36-3D0C-23S8-ILBF-OPOB'}
    time.sleep(5)
    r = s.post(transaction_url,headers=headers,data=data)
    # logging.info('initial status_code: {}'.format(r.status_code))
    # if orestar is blocking requests, exit the scraper
    if r.status_code == 403:
        return [],1
    body = html.fromstring(r.text)
    # grab header row from the top from the transaction table
    headers = [el.text_content().strip() for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr[1]/th')]
    # rows = [[subel.text_content().strip() for subel in el.xpath('td')] for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr')[1:]]
    rows = []
    # get each row of the table for the first 50 transactions
    for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr')[1:]:
        row = [subel.text_content().strip() for subel in el.xpath('td')]
        row.append(el.xpath('td[4]/a')[0].attrib['href'].split('=')[-1] if el.xpath('td[4]/a') else '')
        rows.append(row)
    headers.append('committee_id')
    # if data returned create the dataframe
    if rows and rows[0] and rows[0][0][:7] != 'No data':
        df = pd.DataFrame(rows, columns=headers)
        hits = int(body.xpath('//*[@id="content"]/div/form/table[3]/tr[3]/td[2]/text()')[0].strip().split()[0])
    else:
        df = []
        hits = 0
        logging.info('No data')
    # logging.info('hits: {}'.format(hits))
    # if more than 50 transactions, calculate the number of pages and scrape the rest
    if hits > 50:
        end_range = ceil(hits/50) if ceil(hits/50) < 102 else 101
        for page in range(1,end_range):
            next_df,s = transaction_further_pages(committee_id,page,s)
            if len(df) > 0 and len(next_df):
                df = pd.concat([df,next_df])
    return df,0
    # orestar maxes out at 5k transactions, if there's more, reverse date ordering
    # and grab 5k more, if more log it
    # if hits > 5000:
        # if hits > 10000:
        #     logging.info('More scraping needed for committee_id: {}'.format(committee_id))
        # headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
        #         'Origin':'https://secure.sos.state.or.us',
        #         'Referer':'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearch.do'}
        # time.sleep(30)
        # r = s.post(transaction_url,headers=headers,data=data)
        # if r.status_code == 403:
        #     return [],1
        # data2 = {'cneSearchButtonName':'sort','cneSearchPageIdx':'0','cneSearchFilerCommitteeId':str(committee_id),'cneSearchFilerCommitteeTxtSearchType':'C','cneSearchContributorTxtSearchType':'C',
        # 'OWASP_CSRFTOKEN':'F251-AX8K-O7SW-7E36-3D0C-23S8-ILBF-OPOB','sort':'asc','by':'TRAN_DATE'}
        # r = s.post(transaction_url,headers=headers,data=data2)
        # body = html.fromstring(r.text)
        # # grab header row from the top from the transaction table
        # headers = [el.text_content().strip() for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr[1]/th')]
        # # rows = [[subel.text_content().strip() for subel in el.xpath('td')] for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr')[1:]]
        # rows = []
        # # get each row of the table for the first 50 transactions for 2nd 5k
        # for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr')[1:]:
        #     row = [subel.text_content().strip() for subel in el.xpath('td')]
        #     row.append(el.xpath('td[4]/a')[0].attrib['href'].split('=')[-1] if el.xpath('td[4]/a') else '')
        #     rows.append(row)
        # headers.append('committee_id')
        # # if data returned create the dataframe
        # if rows and rows[0] and rows[0][0][:7] != 'No data':
        #     df_old = pd.DataFrame(rows, columns=headers)
        #     df = pd.concat([df,df_old])
        # for page in range(1,end_range):
        #     next_df,s = transaction_further_pages(committee_id,page,s)
        #         # next_df = pd.DataFrame(rows, columns=headers)
        #     if len(df) > 0 and len(next_df):
        #         df = pd.concat([df,next_df])
        # logging.info('length of results: {}'.format(len(df)))

# transactions_scrape(113)
# committees = pd.read_csv('committees_list.tsv',sep='\t')
# committees.info()
# committees_ids.extend(list(committees['ID']))
# committees_ids = list(committees['ID'])
# logging.info(df.info())
# start = int(sys.argv[-3])
cid = sys.argv[-4]
# cid = 113
# end = '9/26/2016'
start = sys.argv[-3]
end = sys.argv[-2]
# file_num = 1
file_num = sys.argv[-1]
# committees_ids[1524]
# df, point_break = transactions_scrape(17313)
# df.info()
# df, point_break = transactions_scrape(committees_ids[start])
df, point_break = transactions_scrape(cid)
# for cid in committees_ids[start+1:end]:
#     df_new, point_break = transactions_scrape(cid)
#     if point_break:
#         # orestar blocking requests, exiting
#         break
#     if len(df_new)>0:
#         # if len(df)>0:
#         if len(df)>0:
#             df = pd.concat([df,df_new])
#         else:
#             df = df_new
            # print('df_new:',df_new)
        # else:
        #     df = df_new.copy()
    # if len(df_new)>0:
            # df = pd.concat([df,df_new])
# committees_ids[]
# committees_ids.index(135)
# committees_ids[605:610]
# len(committees_ids)
# df.groupby('committee_id').size().sort_values(ascending=False)
# logging.info(df.info())
df['Amount'] = df.Amount.apply(lambda a: a.replace('$','').replace(',','').replace(')','').replace('(','-')).astype(float)
# df['Amount'] = df.Amount.apply(lambda a:
# df.loc[df.Amount<0,'Amount']
date_test = pd.Series(df['Tran Date'].unique())
errors = []
for number,value in date_test.iteritems():
    try:
        pd.to_datetime(value)
    except:
        errors.append([number,value])

# fix these date strings
erroneous_date_strings = [i[1] for i in errors]
erroneous_date_strings
df.head(50)
df.to_csv('transactions_gaps{0}_{1}.csv'.format(cid,file_num),index=False)
# 931 kate brown 5/18/17-2/18/18 4727, 8/18/16-5/18/17 4673, 8/11-18/16 4778, 1/18/14-8/18/16, 11/1/07-1/18/14, rest 652
# first set too long: 931,33,54
