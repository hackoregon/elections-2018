'''
Useful functions for transaction analysis

'''

import datetime
import psycopg2
import json
import os
import sys
import pandas as pd
import functools
from typing import Dict, Iterable
import numpy as np
import itertools

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

class CachedProperty(object):
    '''
    Decorator for a cached property.  Similar to a property, but is only computed once.  Helpful for expensive to
    compute properties.  The property is computed and replaced with an attribute at initialization.

    :Example:

        >>> class foo(object):
        ...     def __init__(self,value):
        ...         self.x = value
        ...
        ...     @CachedProperty()
        ...     def compute_intense_property(self):     # Will only be computed once
        ...         return x
    '''

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value



def calc_icdf(x: Iterable[float], counts: Iterable[int], values: Iterable[float]) -> np.ndarray:
    '''
    Caculates the inverse CDF given counts and valudes
    :param x: Values to calculate inverse CDF
    :param counts: Bin counts
    :param values: Bin values
    :return:
    '''
    values = np.array(values)
    counts = np.array(counts)

    index = np.argsort(values)

    values = values[index]
    norm_counts = counts / np.sum(counts)
    norm_counts = norm_counts[index]

    return np.interp(x=x,
                     xp=np.cumsum(norm_counts),
                     fp=values)

@Memoize()
def get_db_login_info() -> Dict[str, str]:
    '''
    Get database login details.  Looks for elections_login.json in the path.

    File schema:

        {
        "ip": "xxx",
        "db": "xxx",
        "username": "xxx",
        "password": "xxx"
        }

    :return:
    '''

    login_file = None
    for path, dirs, files in itertools.chain(*(os.walk(path) for path in sys.path[::-1])):
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
        query += ' WHERE {0:s}'.format(where_stmt)

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


def fetch_transactions(statement_of_org: pd.DataFrame=None,
                       start_date: datetime.date=None,
                       end_date: datetime.date=None) -> pd.DataFrame:
    '''
    Fetch transactions from database.  Uses the statement_of_org to map all committee names to committee ids.
    '''
    where_stmt = ''
    if start_date is not None:
        where_stmt += " transaction_date > '{:s}'".format(start_date.strftime('%Y/%m/%d'))

    if end_date is not None:
        where_stmt += '' if len(where_stmt) == 0 else ' and'
        where_stmt += " transaction_date < '{:s}'".format(end_date.strftime('%Y/%m/%d'))


    trans = query_db(table='transactions', where_stmt=where_stmt)

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
