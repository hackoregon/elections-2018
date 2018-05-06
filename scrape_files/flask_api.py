import psycopg2
import pandas as pd
from flask import Flask
import json

app = Flask(__name__)

@app.route('/committee/total_donors/<cid>',methods=['GET','POST'])
def donors(cid):
    conn = psycopg2.connect(host='host', user='user', password='pass',
                        dbname='db', connect_timeout=5)
    cursor = conn.cursor()
    cursor.execute('''select sum(1) from (select distinct contributor_payee
                        from transactions where committee_id = '{}') a'''.format(cid),conn)
    results = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()
    return str(results)

@app.route('/committee/total_donations/<cid>',methods=['GET','POST'])
def donations(cid):
    conn = psycopg2.connect(host='host', user='user', password='pass',
                            dbname='db', connect_timeout=5)
    cursor = conn.cursor()
    cursor.execute("""select sum(1) from transactions t
        left join transaction_details td using(transaction_id)
        where t.committee_id = '{}' and td.transaction_type = 'Contribution'""".format(cid),conn)
    results = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()
    return str(results)

@app.route('/committee/contributions/total/<cid>',methods=['GET','POST'])
def contributions(cid):
    conn = psycopg2.connect(host='host', user='user', password='pass',
                        dbname='db', connect_timeout=5)
    cursor = conn.cursor()
    cursor.execute("""select sum(t.amount) from transactions t
        left join transaction_details td using(transaction_id)
        where t.committee_id = '{}' and td.transaction_type = 'Contribution'
        group by t.committee_id""".format(cid),conn)
    results = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()
    return str(results)

@app.route('/committee/expenditures/total/<cid>',methods=['GET','POST'])
def expenditures(cid):
    conn = psycopg2.connect(host='host', user='user', password='pass',
                        dbname='db', connect_timeout=5)
    cursor = conn.cursor()
    cursor.execute("""select sum(t.amount) from transactions t
        left join transaction_details td using(transaction_id)
        where t.committee_id = '{}' and td.transaction_type = 'Expenditure'
        group by t.committee_id""".format(cid),conn)
    results = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()
    return str(results)

@app.route('/committee/expenditures/purpose/<cid>',methods=['GET','POST'])
def expenditures(cid):
    conn = psycopg2.connect(host='host', user='user', password='pass',
                        dbname='db', connect_timeout=5)
    cursor = conn.cursor()
    cursor.execute("""select sum(t.amount) from transactions t
        left join transaction_details td using(transaction_id)
        where t.committee_id = '{}' and td.transaction_type = 'Expenditure'
        group by t.committee_id""".format(cid),conn)
    results = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()
    return str(results)

@app.route('/committee/donors/<cid>',methods=['GET','POST'])
def transaction_details(tid):
    conn = psycopg2.connect(host='host', user='user', password='pass',
                        dbname='db', connect_timeout=5)
    cursor = conn.cursor()
    cursor.execute('''select sum(1) from (select distinct contributor_payee
                        from transactions where committee_id = '{}') a'''.format(cid),conn)
    results = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()
    return str(results)

# df.info()
if __name__ == "__main__":
    app.debug = True
    app.run()
