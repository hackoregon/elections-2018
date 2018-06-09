import pandas as pd
import numpy as np
import pickle
from src.fuzzymatchlist import FuzzyList
import json
from nltk import ngrams
import argparse
import os
import re

class BusinessMatching(object):
    def __init__(self, input_dict):
        with open("state_city.pickle", 'rb') as f:
            self.state_city_dict = pickle.load(f)
        self.input_dict = input_dict
        self.company_set = set()
        self.import_choices()

    def import_choices(self):
        """
        """
        if os.path.isfile("companies.pickle"):
            with open("companies.pickle", "rb") as f:
                choices_list = pickle.load(f)
            self.company_set = self.company_set.union(set(choices_list))
        else:
            pass

    def create_choices_list(self):
        """
        Extends and/or creates the company list for fuzzy matching against.
        """
        self.self_employed = []
        individual_sub_employer_list = []
        for full_name in self.input_dict[1]:
            employer_name, _, _ = self.get_name_parts(full_name)
            if employer_name != None:
                individual_sub_employer_list.append(employer_name)
            else:
                self.self_employed.append(full_name)
        self.company_set = self.company_set.union(set(individual_sub_employer_list))
        self.company_set = self.company_set.union(set(self.input_dict[0]))
        self.company_set = self.company_set.difference(set(''))
        self.choices_set = self.company_set.copy()
        with open("companies.pickle", "wb") as f:
            pickle.dump(self.choices_set, f, protocol=pickle.HIGHEST_PROTOCOL)

    def get_name_parts(self, employer_name):
        """
        Break Employer Name field into: Employer, City State
        """
        try:
            employer_name_l = employer_name.lower()
        except:
            return None, None, None
        state = None
        city = None
        last_2 = employer_name_l[-2:]
        if last_2 in self.state_city_dict.keys():
            state = last_2
            remainder = employer_name_l[:-2]
            deep = 3
            n_gram_list = []
            for n in range(1,deep+1):
                current = [set([str.join(" ", x)]) for x in list(ngrams(remainder.strip().split(" ")[-deep:],n))]
                n_gram_list.append(current)
            pos_cities = self.state_city_dict[state]
            for ng_list in n_gram_list:
                for ng_set in ng_list:
                    if len(pos_cities.intersection(ng_set)) > 0:
                        city = list(ng_set)[0]
            cleaned_city = re.sub("({})".format(city), "", self.get_backwards_string(employer_name), 1, flags=re.IGNORECASE)
            cleaned_employer = re.sub("({})".format(state), "", cleaned_city, 1, flags=re.IGNORECASE)
        else:
            return employer_name, None, None
        return self.get_backwards_string(cleaned_employer.strip()), city, state

    def get_backwards_string(self, string):
        """
        Reverses string by word.
        """
        return str.join(" ", string.split(" ")[::-1])
