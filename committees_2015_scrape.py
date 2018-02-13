# %cd /home/mbodenator/Documents/hack_oregon
from lxml import html
import pandas as pd

html_files = ['committees_2015.html','committees_2016.html']

def html_scrape(input_file):
    with open(input_file,'r') as html_file:
        html_body = html_file.read()
    body = html.fromstring(html_body)
    committee_rows = body.xpath('//tbody/tr')

    committee_select = [('|'.join(row.xpath('td[1]/a/text()')).strip(),'|'.join(row.xpath('td[2]/text()')).strip(),'|'.join(row.xpath('td[3]/text()')).strip()) for row in committee_rows if row]
    df = pd.DataFrame(committee_select,columns=['filer_name','ID','filer_description'])
    df_clean = df.loc[df.ID != '',:]
    df_clean['ID'] = df_clean.ID.apply(int)
    print(df_clean.info())
    return df_clean

df = html_scrape(html_files[0])
df = pd.concat([df,html_scrape(html_files[1])])
print(df.info())
df.groupby('ID').size().sort_values(ascending=False)
df.drop_duplicates(subset='ID',inplace=True)
df.to_csv('committees_list.tsv',sep='\t',index=False)
