# %cd /home/mbodenator/Documents/hack_oregon
import pandas as pd
import requests
from lxml import html

headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Origin':'https://secure.sos.state.or.us',
            'Referer':'https://secure.sos.state.or.us/orestar/GotoSearchByName.do'}
election_activity_headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Origin':'https://secure.sos.state.or.us',
            'Referer':'https://secure.sos.state.or.us/orestar/CommitteeSearchFirstPage.do'}
committee_url = 'https://secure.sos.state.or.us/orestar/CommitteeSearchFirstPage.do'
election_history_url = 'https://secure.sos.state.or.us/orestar/electionActivityLog.do?actionId=PageLoad'

committee_ids = ['113','12510','17119','15082','14049']
all_rows = []
for cid in committee_ids:
    s = requests.Session()
    data = {'page':'100','committeeNameMultiboxText':'contains','committeeId':cid,'firstNameMultiboxText':'contains',
            'lastNameMultiboxText':'contains','submit':'Submit','discontinuedSOO':'false','approvedSOO':'true',
            'pendingApprovalSOO':'false','insufficientSOO':'false','resolvedSOO':'false','rejectedSOO':'false',
            'OWASP_CSRFTOKEN':'354D-CU2G-W596-3797-U511-ZEHT-BPLF-HUTG'}
    s.get(committee_url)
    # post to committee page first so the following get for election history
    r = s.post(committee_url,headers=headers,data=data)
    t = s.get(election_history_url,headers=election_activity_headers)#,data=data)
    body = html.fromstring(t.text)
    rows = [[subel.strip() for subel in el.xpath('td/text()')] for el in body.xpath('//*[@id="content"]/div/table[2]/tr')[1:]]
    for row in rows:
        row.append(cid)
    all_rows.extend(rows)
df = pd.DataFrame(all_rows,columns=['election','active_date','status','active_reason','committee_id'])
df.to_csv('election_activity_log.csv',index=False)
