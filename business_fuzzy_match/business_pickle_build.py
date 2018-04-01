import pandas as pd
import numpy as np
import time
import re
import pickle
from fuzzymatchlist import FuzzyList


class BusinessMatching(object):
    def __init__(self, input_file=None):
        if input_file == None:
            self.input_name = "transaction_detail_first_batch.csv"
        else:
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

if __name__ == "__main__":
    BM = BusinessMatching()
    BM.build_sub_df()
    BM.build_top_choices()
    BM.save_pickle()
