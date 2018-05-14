'''
Useful functions for transaction analysis

'''


import psycopg2
import json
import os
import pandas as pd
import functools
from typing import Dict


ELECTION_DB_HOST = '54.202.102.40'
ELECTION_DB_NAME = 'local-elections-finance'


class Memoize():
    """ A wrapper for caching function results """
    def __init__(self, bound=None):
        self.__cache = dict()

    def __call__(self, fnc):
        @functools.wraps(fnc)
        def wrapper(*args, **kwargs):
            """ Helper function """
            key = (tuple(args), tuple(sorted(kwargs.items(), key=lambda x: x[0])))
            if key not in self.__cache:
                self.__cache[key] = fnc(*args, **kwargs)
            return self.__cache[key]

        return wrapper

@Memoize()
def get_db_login_info() -> Dict[str, str]:
    '''
    Get database login details.  Looks for elections_login.json in the path.
    :return:
    '''

    directories = os.path.abspath(__file__).split(os.sep)
    root_path = os.sep.join(directories[:directories.index('elections-2018')+1])

    login_file = None
    for path, dirs, files in os.walk(root_path):
        files = list(filter(lambda x: x == 'elections_login.json', files))
        if len(files) > 0:
            login_file = os.path.join(path, files[0])

    if login_file is None:
        raise Exception('Unable to find elections_login.json in path')

    with open(login_file, 'r') as f:
        login_info = json.load(f)
    return login_info

def query_db(table: str,
             select_stmt: str='*',
             where_stmt: str='',
             host: str=ELECTION_DB_HOST,
             dbname: str=ELECTION_DB_NAME,
             user: str = None,
             password: str = None) -> pd.DataFrame:
    '''
    query database

    :param host:
    :param dbname:
    :param user:
    :param password:
    :return:
    '''

    if user is None or password is None:
        login_info = get_db_login_info()
        user = login_info['username']
        password = login_info['password']

    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
    query = 'SELECT {0:s} FROM {1:s}'.format(select_stmt, table)
    if len(where_stmt) > 0:
        query += ' WHERE {1:s}'.format(where_stmt)

    data = pd.read_sql(query, conn)
    conn.close()

    return data


def fetch_statement_of_org() -> pd.DataFrame:
    '''
    Fetch Statement of Organization from database
    '''
    state_org = query_db(table='statement_of_org')

    state_org['committee_id'] = state_org['committee_id'].apply(str)
    state_org['committee_name'] = state_org['committee_name'].apply(str)
    return state_org


def fetch_transactions(statement_of_org: pd.DataFrame=None) -> pd.DataFrame:
    '''
    Fetch transactions from database.  Uses the statement_of_org to map all committee names to committee ids.
    '''
    trans = query_db(table='transactions')

    trans['committee_id'] = trans['committee_id'].apply(str)
    trans['contributor_payee'] = trans['contributor_payee'].apply(str)

    # Map all payees to committee ids
    statement_of_org = fetch_statement_of_org() if statement_of_org is None else statement_of_org
    committee_id_lookup = {id: name for name, id in
                           zip(statement_of_org['committee_name'].values, statement_of_org['committee_id'].values)}
    trans['contributor_payee'] = trans['contributor_payee'].apply(
        lambda x: committee_id_lookup[x] if x in committee_id_lookup else x)
    trans['committee_id'] = trans['committee_id'].apply(
        lambda x: committee_id_lookup[x] if x in committee_id_lookup else x)

    return trans
