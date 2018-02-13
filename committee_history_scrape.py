# %cd /home/mbodenator/Documents/hack_oregon
import pandas as pd
import requests
from lxml import html

def history_scrape(committee_id):
    history_url = 'https://secure.sos.state.or.us/orestar/committeeSearchSOOHistory.do?committeeId={}'.format(committee_id)
    s.get(history_url)
    t = s.get(history_url,headers=election_activity_headers)
    body = html.fromstring(t.text)
    rows = [[subel.text_content().strip() for subel in el.xpath('td')] for el in body.xpath('//*[@id="content"]/div/table[4]/tr')[1:]]
    for row in rows:
        row.append(committee_id)
    df = pd.DataFrame(rows,columns=['committee_name','committee_description','effective','expiration','filing_type','committee_id'])
    return df

s = requests.Session()
election_activity_headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Origin':'https://secure.sos.state.or.us',
            'Referer':'https://secure.sos.state.or.us/orestar/CommitteeSearchFirstPage.do'}
committee_ids = ['113','12510','4797']
df = history_scrape(committee_ids[0])
for cid in committee_ids[1:]:
    new_df = history_scrape(cid)
    df = pd.concat([df,new_df])
df.to_csv('committee_history_log.csv',index=False)
