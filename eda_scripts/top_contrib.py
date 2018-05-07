import psycopg2
import numpy as np
import pandas as pd
import datetime
import json
import os
import sys
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class TopContrib(object):
    """
    For getting top contributors for a canidate for a specific year.

    Parameters:
    -----------
    login_file : (str) Name of a json type file that is within 5 steps along the tree dir that holds postgres login info.
            format : {"ip" : $IP_ADDRESS$,
                      "username" : $DB_USERNAME$,
                      "password" : $DB_PASSWORD$,
                      "db" : $DB_NAME$
                      }
    Use:
    ----
    TC = TopContrib(login_file='foo.json')
    TC.get_contributions("Jon Stewart", 2010, top_n=4)
    """

    def __init__(self, login_file = "elections_login.json"):
        self._db_login = self._find_login_details(login_file)
        self.money_in_df, self.money_out_df = self._query_data()

    def _find_login_details(self, login_file, steps=5):
        """
        Gets loggin details from login_file if within 'steps' up from the cwd.

        Returns:
        -------
        login_details (dict) : Dictionary of login info.
            format : {"ip" : $IP_ADDRESS$,
                      "username" : $DB_USERNAME$,
                      "password" : $DB_PASSWORD$,
                      "db" : $DB_NAME$
                      }
        """
        login_file_loc = None
        origin_dir = os.path.abspath(os.curdir)
        for _ in range(steps):
            current_dir = os.path.abspath(os.curdir)
            os.chdir("..")
            if login_file in os.listdir("."):
                login_file_loc = os.getcwd()
        if login_file_loc == None:
            sys.exit("Could not find login file in dir tree.")
        os.chdir(origin_dir)
        with open(os.path.join(login_file_loc, login_file), "rb") as f:
            login_details = json.load(f)
        return login_details

    def _query_data(self):
        """
        Queries postgres DB and pulls transactions table into pandas. Parses data into 'Cash Contributions'
        and 'Cash Expenditures'

        Returns:
        -------
        money_in_df (pandas.DataFrame) : 'Cash Contributions'
        money_out_df (pandas.DataFrame) : 'Cash Expenditures'
        """
        conn = psycopg2.connect(host=self._db_login["ip"]
                       ,dbname=self._db_login["db"]
                       ,user=self._db_login["username"]
                       ,password=self._db_login["password"])
        cursor = conn.cursor()
        transactions_df = pd.read_sql("SELECT * FROM transactions", conn)
        conn.close()
        transactions_df["transaction_date"] = pd.to_datetime(transactions_df["transaction_date"])
        money_in_df = transactions_df[transactions_df.transaction_subtype == "Cash Contribution"].copy()
        money_out_df = transactions_df[transactions_df.transaction_subtype == "Cash Expenditure"].copy()
        return money_in_df, money_out_df

    def get_committee_matches(self,candidate, top_n, data):
        """
        Performs fuzzy match between candidate and committee names against the active comittees for the supplied year.

        Returns:
        --------
        years_dict (dict) : dictionary of top_n matches per year -> {year : ($COMITTEE$, $PERC_MATCH$)}
        """
        years_dict = {}
        for year in range(2004, 2018):
            range_df = data[data.transaction_date >= "{0}-03-01".format(year)]
            range_df = range_df[range_df.transaction_date < "{0}-03-01".format(year+1)]
            choices = range_df.filer_committee.unique()
            top = process.extract(candidate, choices, limit = top_n)
            years_dict[year] = top
        return years_dict

    def get_contributions(self, candidate, year, data=None, top_n=3):
        """
        Performs grouping of top committees for the supplied year for a candidate.

        Returns:
        -------
        comitteee_amounts (dict) : {committee : {"match" : $PERC_MATCH$,
                                                 "amount": $CONTRIB$
                                                }
                                    } 
        """
        if type(data) == type(None):
            data = self.money_in_df
        year_dict = self.get_committee_matches(candidate,top_n,data)
        comittee_matches = year_dict[year]
        comitteee_amounts = {}
        for committee in comittee_matches:
            amount = data[data.filer_committee == committee[0]]["amount"].sum()
            comitteee_amounts[committee[0]] = {"match": committee[1],
                                               "amount": amount}
        return comitteee_amounts
