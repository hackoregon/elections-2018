import os
import sys
import re
from glob import glob
import json

import numpy as np
import pandas as pd
from pandas import DataFrame as DF, Series
from collections import OrderedDict as od

class BallotsExtractor(object):

    def _load_ballot_files(self):
        ballotfiles = {}
        for file in self.files:
            try:
                with open(file, 'r') as f:
                    # print(file)
                    lines = [l.rstrip('\n') for l in list(f.readlines())]
                    lines = [l for l in lines if l != '']
                    ballotfiles[file] = lines
            except Exception as e:
                # print(' ', file)
                print(' ', e)
        return ballotfiles

    def _read_all_docs(self):
        ballotfiles = self._load_ballot_files()
        all_docs = {}
        for file,doc in ballotfiles.items():
            doc = [l.lstrip('\t') if l.startswith('\tTotal') else l for l in doc]
            doc = [re.sub('\t{2,}', '\t', l) for l in doc]
            name = file.split('\\')[-1].rstrip('.txt|.TXT')
            all_docs[name] = doc
        return all_docs

    def _extract_titles(self):
        self.all_docs = self._read_all_docs()
        all_titles = od()
        for name,doc in self.all_docs.items():
            titles = od()
            for i,l in enumerate(doc):
                if l.startswith('STATE'):
                    titles[i] = l
            all_titles[name] = titles
        return all_titles

    def _extract_tables(self):
        all_titles = self._extract_titles()
        self.all_tables = {}
        for name,titles in all_titles.items():
            tables = {}
            tlist = list(titles)
            doc = self.all_docs[name]
            for i,(n,title) in enumerate(titles.items()):
                        try:
                            tables[title] = doc[n+1:tlist[i+1]]
                        except:
                            tables[title] = doc[n+1:]
            self.all_tables[name] = tables

    def _toint(self, x):
        try:
            return x.str.replace(',', '').astype(int)
        except:
            return x

    def _create_dfs(self):
        self._extract_tables()
        self.all_dfs = {}
        for name,tables in self.all_tables.items():
            dfs = {}
            for title,data in tables.items():
                i = 1
                for l in data:
                    if not l.startswith('County'):
                        i += 1
                    else:
                        break
                df = DF([l.split('\t') for l in data])
                cols = df.iloc[i-1].apply(lambda x: ''.join(x).strip())
                df = df.iloc[i:]
                df.rename(columns={i:c for i,c in enumerate(cols)}, inplace=True)
                df=df.apply(lambda x: self._toint(x))
                dfs[title] = df
            self.all_dfs[name] = dfs

            
    def sums_equal_totals(self):
        equal = []
        for dfs in self.all_dfs.values():
            for df in dfs.values():
                s = df.iloc[:-1, 1:].apply(lambda x: self._toint(x)).sum()
                equal.append(all(s == df.iloc[-1:, 1:].apply(lambda x: self._toint(x))))
        return all(equal)

    # function formats year to 4 character string
    def _whole_year(self, x):
        try:
            if len(x) == 2:
                return '20' + x
            if len(x) == 4:
                return x
            if len(x) == 6:
                return x[2:]
        except:
            return x
    
    def extract_ballots(self, path=None):
        if not path:
            path = 'measure_ballots_txt/measure_ballots_txt/*.txt'
        self.files = glob(path)

        # dict to store ballots dicts by measure
        ballots_data = {}
                
        #loop over extracted ballots to create/append data
        self._create_dfs()
        for title, dfs in self.all_dfs.items():
            tokens = re.split('(\d+)', title)
            election_type = tokens[0].lstrip(r'ABmeasure')
            year = tokens[1]

            for measure, df in dfs.items():
                cols = df.columns.tolist()

                for name in cols[1:]:
                    ballots_data.setdefault(election_type, [])
                    campaign = {}
                    campaign['election_type'] = election_type
                    campaign['year'] = self._whole_year(year)
                    campaign['state_measure'] = measure.lstrip(r'STATE MEASURE')
                    campaign['passed'] = int(name.startswith('*'))
                    campaign['option'] = name.lstrip('*')
                    campaign['votes'] = df.set_index('County')[name].iloc[:-1].to_dict()
                    
                    ballots_data[election_type].append(campaign)  

        df_list = []
        for types, ballots in ballots_data.items():
            df = DF(ballots_data[types])
            df_list.append(df)
        ballots_df = pd.concat(df_list)
        ballots_df
        
        return ballots_df