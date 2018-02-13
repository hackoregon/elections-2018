%cd /home/mbodenator/Documents/hack_oregon
import pandas as pd
import requests
from lxml import html

s = requests.Session()
committee_id = '113'
headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Origin':'https://secure.sos.state.or.us',
            'Referer':'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearch.do'}

data = {'cneSearchButtonName':'search','cneSearchPageIdx':'0','cneSearchFilerCommitteeId':committee_id,'cneSearchFilerCommitteeTxtSearchType':'C','cneSearchContributorTxtSearchType':'C',
        'OWASP_CSRFTOKEN':'F251-AX8K-O7SW-7E36-3D0C-23S8-ILBF-OPOB'}
transaction_url = 'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearchResults.do'
r = s.post(transaction_url,headers=headers,data=data)
body = html.fromstring(r.text)
headers = [el.text_content().strip() for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr[1]/th')]
rows = [[subel.text_content().strip() for subel in el.xpath('td')] for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr')[1:]]
df = pd.DataFrame(rows, columns=headers)

for page in range(1,3):
    next_url = 'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearchResults.do?cneSearchButtonName=next&cneSearchFilerCommitteeId={0}&cneSearchContributorTxtSearchType=C&cneSearchFilerCommitteeTxtSearchType=C&cneSearchPageIdx={1}'.format(committee_id,page)
    headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                'Origin':'https://secure.sos.state.or.us',
                'Referer':'https://secure.sos.state.or.us/orestar/gotoPublicTransactionSearchResults.do'}
    t = s.get(next_url,headers=headers)
    body = html.fromstring(t.text)
    headers = [el.text_content().strip() for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr[1]/th')]
    rows = [[subel.text_content().strip() for subel in el.xpath('td')] for el in body.xpath('//*[@id="content"]/div/form/table[4]/tr')[1:]]
    next_df = pd.DataFrame(rows, columns=headers)
    df = pd.concat([df,next_df])
df.to_csv('transaction_sample.csv',index=False)
