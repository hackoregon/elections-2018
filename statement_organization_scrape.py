import pandas as pd
import requests
from lxml import html

def dict_gen(body):
    """ scrape each portion of the provided lxml object and return dictionary of it all """
    # grabbing the left column of committee information
    dict1 = {'Committee '+el.xpath('td[1]/text()')[0].strip().split(':')[0]:', '.join([subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ') for subel in el.xpath('td[2]/text()')]) for el in body.xpath('//table[2]/tr')[1:]}
    # grabbing the right column of committee information
    dict2 = {'Committee '+el.xpath('td[3]/text()')[0].strip().split(':')[0]:', '.join([subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ') for subel in el.xpath('td[4]/text()')]) for el in body.xpath('//table[2]/tr')[1:]}
    # grabbing the left column of treasurer information
    dict3 = {'Treasurer '+el.xpath('td[1]/text()')[0].strip().split(':')[0]:', '.join([subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ') for subel in el.xpath('td[2]/text()')]) for el in body.xpath('//table[3]/tr')[1:]}
    dict1.update(dict2)
    dict1.update(dict3)

    # grabbing the right column of treasurer information since not every row has it like committee
    middle_last_headers = ['Treasurer '+el.strip().split(':')[0] for el in body.xpath('//table[3]/tr[3]/td[3]/text()')]
    middle_last_vals = [el.strip() for el in body.xpath('//table[3]/tr[3]/td[4]/text()')]
    middle_last = zip(middle_last_headers,middle_last_vals)
    middle_last_dict = {x:y for x,y in middle_last}
    dict1.update(middle_last_dict)

    # Grab candidate information if it is a candidate committee, otherwise grab supports/opposes info
    if body.xpath('//*[@id="content"]/div/form/table[4]/tr[1]/td/h5/text()')[0].strip() == 'Candidate Information':
        # grab left column
        dict5 = {el.xpath('td[1]/text()')[0].strip().split(':')[0]:', '.join([subel.strip().replace('\n','').replace('   ',' ').replace('  ',' ') for subel in el.xpath('td[2]/text()')]) for el in body.xpath('//table[4]/tr')[1:] if el.xpath('td[1]/text()')[0].strip()}
        last_first_headers = [el.strip().split(':')[0] for el in body.xpath('//table[4]/tr[3]/td[3]/text()')]
        last_first_vals = [el.strip() for el in body.xpath('//table[4]/tr[3]/td[4]/text()')]
        last_first = zip(last_first_headers,last_first_vals)
        last_first_dict = {x:y for x,y in last_first}

        # grab right column
        last_last_headers = [el.strip().split(':')[0] for el in body.xpath('//table[4]/tr[4]/td[3]/text()')]
        last_last_vals = [el.strip() for el in body.xpath('//table[4]/tr[4]/td[4]/text()')]
        last_last = zip(last_last_headers,last_last_vals)
        last_last_dict = {x:y for x,y in last_last}
        dict1.update(dict5)
        dict1.update(last_first_dict)
        dict1.update(last_last_dict)
    else:
        # may need to be updated once more examples of PACs are seen
        body.xpath('//*[@id="content"]/div/form/table[4]/tr[2]/td/text()')
    return dict1

committee_ids = ['113','12510','17119','15082','14049']
rows = []
# loop through list of committee_ids to scrape each profile
for cid in committee_ids:
    s = requests.Session()
    headers = {'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                'Origin':'https://secure.sos.state.or.us',
                'Referer':'https://secure.sos.state.or.us/orestar/GotoSearchByName.do'}
    data = {'page':'100','committeeNameMultiboxText':'contains','committeeId':cid,'firstNameMultiboxText':'contains',
            'lastNameMultiboxText':'contains','submit':'Submit','discontinuedSOO':'false','approvedSOO':'true',
            'pendingApprovalSOO':'false','insufficientSOO':'false','resolvedSOO':'false','rejectedSOO':'false',
            'OWASP_CSRFTOKEN':'354D-CU2G-W596-3797-U511-ZEHT-BPLF-HUTG'}
    committee_url = 'https://secure.sos.state.or.us/orestar/CommitteeSearchFirstPage.do'
    s.get(committee_url)
    r = s.post(committee_url,headers=headers,data=data)
    body = html.fromstring(r.text)
    rows.append(dict_gen(body))
df = pd.DataFrame(rows)
df.to_csv('statement_of_organization.csv',index=False)
