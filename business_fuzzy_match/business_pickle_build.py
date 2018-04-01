import pandas as pd
import numpy as np
import time
import re
import pickle
from fuzzymatchlist import FuzzyList
from nltk import ngrams
import argparse
import os

class BusinessMatching(object):
    def __init__(self, input_file):
        self.input_name = input_file
        try:
            with open("state_city.pickle", 'rb') as f:
                self.state_city_dict = pickle.load(f)
        except:
            raise OSError("File Not Found: 'state_city.pickle'")
        self.input_dataframe = pd.read_csv(self.input_name, low_memory=False)
        self.build_choices_list()

    def build_choices_list(self):
        """
        Checks to see if there is a pickled list of companies.
        If there is:
            Open it then append the companies from the current incoming file (create_choices_list)
        If there isn't:
            create_choices_list
        """
        if os.path.isfile("companies.pickle"):
            with open("companies.pickle", "rb") as f:
                choices_list = pickle.load(f)
            self.create_choices_list(list(choices))
        else:
            self.create_choices_list()

    def create_choices_list(self, current=None):
        """
        Extends and/or creates the company list for fuzzy matching against.
        """
        company_list = []
        if current != None:
            company_list.extend(current)
        business_sub_df = self.input_dataframe[self.input_dataframe["Address Book Type"] == "Business Entity"].copy()
        individual_sub_df = self.input_dataframe[self.input_dataframe["Address Book Type"] == "Individual"].copy()
        company_list.extend(list(np.unique(list(business_sub_df["Name"]))))
        individual_sub_employer_list = []
        for employer_name in list(individual_sub_df["Employer Name"]):
            employer_name, _, _ = self.get_name_parts(employer_name)
            if employer_name != None:
                individual_sub_employer_list.append(employer_name)
        company_list.extend(individual_sub_employer_list)
        self.choices_set = set(company_list.copy())
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

    def build_top_choices(self, num=5):
        """
        Build top 'num' fuzzy match choices dict for all of the currently loaded choices in self.choices_set.
        """
        self.top_choices_dict = {}
        start_time = time.time()
        full_list = list(self.choices_set)
        FL = FuzzyList(full_list)
        for i, name in enumerate(full_list):
            self.top_choices_dict[name] = FL.get_top_n_matches(name, num)
            if i % 100 == 0:
                print(str(np.round(i/len(full_list),3) * 100) + "%")
                print(str(time.time() - start_time))

    def save_pickle(self):
        with open("{}{}.pickle".format(re.sub("(\.).+", "", self.input_name), "_fm"), "wb") as f:
            pickle.dump(self.top_choices_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

def main_call(input_file_name):
    BM = BusinessMatching(input_file_name)
    BM.build_top_choices()
    BM.save_pickle()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fuzzy match on business names.")
    parser.add_argument('--input_doc', help='Input CSV doc.')
    args = parser.parse_args()
    main_call(args.input_doc)
