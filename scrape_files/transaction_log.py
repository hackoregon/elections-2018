%cd /home/mbodenator/Documents/hack_oregon/elections-2018-master
import pandas as pd
import os

for root, dir, files in os.walk('./logs'):
    log_files = files
scrape_log_files = [log for log in log_files if 'transaction_scrape' in log]
no_data_rows = []
more_scraping = []
for log in scrape_log_files:
    with open('logs/'+log) as f:
        data = f.readlines()
    data
    prev_row = ''
    uber_prev_row = ''
    for row in data:
        if 'No data' in row:
            # print(uber_prev_row)
            # print(prev_row)
            # print(row)
            if 'No data' not in uber_prev_row:
                no_data_rows.append(uber_prev_row.split(':')[-1].strip())
        if 'More scraping' in row:
            more_scraping.append(row.split(':')[-1].strip())
        uber_prev_row = prev_row
        prev_row = row
len(no_data_rows)
set(no_data_rows)
missing_list = ['4572','3396','191','39','2690','15192','348','33','54','931','1524','135','275','682']
len(set(more_scraping))
set(more_scraping).difference(missing_list)
