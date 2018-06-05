import os
import sys
import re
from glob import glob
import json

import numpy as np
import pandas as pd
from pandas import DataFrame as DF, Series
from collections import OrderedDict as od

from correct_names.correct_names import CorrectNames as CN


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
            doc = [l.lstrip('\t') if l.startswith('\tTOTAL') else l for l in doc]
            doc = [re.sub('\t{2,}', '\t', l) if l.startswith('TOTAL') else l for l in doc]
            name = file.split('/')[-1].rstrip('.txt')
            all_docs[name] = doc
        return all_docs

    def _extract_titles(self):
        self.all_docs = self._read_all_docs()
        all_titles = od()
        for name,doc in self.all_docs.items():
            titles = od()
            for i,l in enumerate(doc):
                if l.isupper() & ~l.startswith('TOTAL'):
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
                    if doc[n+1] in ['Democrat','Republican']:
                        title += '-' + doc[n+1][:3].upper()
                        n += 1
                    tables[title] = doc[n+1:tlist[i+1]]
                except:
                    tables[title] = doc[n+1:]
                    # print('Exception:', title)
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
                collines = data[:i]
                df = DF([l.split('\t') for l in data])
                cols = df.iloc[:i].apply(lambda x: ' '.join(x).strip())
                df = df.iloc[i:]
                df.rename(columns={i:c for i,c in enumerate(cols)}, inplace=True)
                df = df.apply(lambda x: self._toint(x))
                for c in df.columns.tolist()[1:]:
                    df.loc[:, c] = df[c].apply(lambda x: None if x == '' else x)
                dfs[title] = df
            self.all_dfs[name] = dfs

    def sums_equal_totals(self):
        equal = []
        for dfs in self.all_dfs.values():
            for df in dfs.values():
                s = df.iloc[:-1, 1:].apply(lambda x: self._toint(x)).sum()
                equal.append(all(s == df.iloc[-1:, 1:].apply(lambda x: self._toint(x))))
        return all(equal)

    def extract_ballots(self, path=None):
        if not path:
            path = 'ballots/ballots_txt/*.txt'
        self.files = glob(path)
        # get clean names mapping
        cn = CN()
        cndict = cn.generate()
        self.cndict = cndict

        # dict to store ballots dicts by candidate
        ballots_data = {}
        parties = [
            '(DEM)', 
            '(REP)', 
            '(IND)', 
            '(LIB)', 
            '(PAC)', 
            '(CON)', 
            '(WI)', 
            '(WFP)', 
            '(PRO)',
            '(NA)',
        ]
        # loop over extracted ballots to create/append data
        # per doc/position/candidate
        self._create_dfs()
        i = 0
        for title,dfs in self.all_dfs.items():
            tokens = title.split()
            election_type = tokens[0]
            year = tokens[1]
            partisan = tokens[2][2:].startswith('partisan')

            for position,df in dfs.items():
                i += 1
                cols = df.columns.tolist()
                write_in = 0
                postoks = position.split(',')
                for name in cols[1:]:
                    clean_name = name.strip('*')
                    cname_toks = clean_name.split()
                    alt_toks = clean_name.split('(')
                    partyname = False
                    if cname_toks[-1] in parties:
                        partyname = cname_toks[-1].strip('()')
                        clean_name = ' '.join(cname_toks[:-1])
                    elif clean_name[-4:] in parties:
                        partyname = clean_name[-4:].strip('()')
                        clean_name = clean_name[:-4].strip(')')
                    elif clean_name[-5:] in parties:
                        partyname = clean_name[-5:].strip('()')
                        clean_name = clean_name[:-5].strip(')')
                    if partyname == 'WI':
                        write_in = 1
                    # correct the name (consolidated from name variations)
                    clean_name = cndict[clean_name]
                    pos = postoks[0]
                    if len(postoks) > 1:
                        disttoks = ', '.join(postoks[1:]).split('-')
                        dist = disttoks[0].strip()
                    else:
                        dist = '-'
                    if dist != '-':
                        try:
                            party = disttoks[1]
                        except:
                            party = 'UNK'
                    else:
                        if partyname:
                            party = partyname
                        elif disttoks[-1] in ['DEM','REP']:
                            party = disttoks[-1]
                        else:
                            party = 'UNK'
                    ballots_data.setdefault(clean_name, [])
                    campaign = {}
                    campaign['name'] = clean_name
                    campaign['year'] = year
                    campaign['race'] = pos
                    campaign['district'] = dist
                    campaign['party'] = party
                    campaign['votes'] = df.set_index('County')[name].iloc[:-1].to_dict()
                    campaign['won'] = int(name.startswith('*'))
                    campaign['type'] = title[0]
                    campaign['doc_title'] = title
                    campaign['writein'] = write_in
                    ballots_data[clean_name].append(campaign)

        # consolidate write-ins data
        for name,data in ballots_data.items():
            dcopy = data.copy()
            for d in data:
                if d['writein'] == 1:
                    dist = d['district']
                    pos = d['race']
                    title = d['doc_title']
                    votes = d['votes']
                    for dx in data:
                        dxc = dx.copy()
                        if (
                            (dx['district'] == dist)
                            & (dx['race'] == pos)
                            & (dx['doc_title'] == title)
                            & (dx['writein'] == 0)
                        ):
                            counts = dx['votes']
                            for county in votes:
                                counts.setdefault(county, 0)
                                try:
                                    counts[county] += int(votes[county])
                                except Exception as e:
                                    print(e)
                            dx['votes'] = counts
                            dcopy.remove(d)
                            dcopy.remove(dxc)
        #                     dx['votes'] = json.dumps(dx['votes'])
                            dcopy.append(dx)
                            break
            ballots_data[name] = dcopy

        return ballots_data
