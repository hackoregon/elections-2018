import pandas as pd
import numpy as np
import time
import re
import pickle
from fuzzymatchlist import FuzzyList
import argparse

class BusinessMatching(object):
    def __init__(self, input_file):
        self.input_name = input_file
        self.input_dataframe = pd.read_csv(self.input_name, low_memory=False)
        self.build_sub_df()

    def build_sub_df(self):
        self.business_sub_df = self.input_dataframe[self.input_dataframe["Address Book Type"] == "Business Entity"].copy()

    def build_top_choices(self):
        self.top_choices_dict = {}
        start_time = time.time()
        full_list = list(np.unique(list(self.business_sub_df["Name"])))
        FL = FuzzyList(full_list)
        for i, name in enumerate(full_list):
            self.top_choices_dict[name] = FL.get_top_n_matches(name, 5)
            if i % 100 == 0:
                print(str(np.round(i/len(full_list),3) * 100) + "%")
                print(str(time.time() - start_time))

    def save_pickle(self):
        with open("{}{}.pickle".format(re.sub("(\.).+", "", self.input_name), "_fm"), "wb") as f:
            pickle.dump(self.top_choices_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

def main_call(input_file):
    BM = BusinessMatching()
    BM.build_sub_df()
    BM.build_top_choices()
    BM.save_pickle()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Camera frame grab.")
    parser.add_argument('--save_loc', help='Image save location.')
    parser.add_argument('--rec_time', help='Length of time you want to record for.')
    parser.add_argument('--camera_num', help='Camera number in camera_info.json')
    args = parser.parse_args()
