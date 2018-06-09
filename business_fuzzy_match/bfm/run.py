import pickle
import numpy as np
from src.data_pull import DataPuller
from src.fuzzymatchlist import FuzzyList
from src.business_pickle_build import BusinessMatching
import os
import time

def save_pickle():
    with open("fm_choices.pickle", "wb") as f:
        pickle.dump(top_choices_dict, f)

def load_pickle():
    if os.path.exists("fm_choices.pickle"):
        with open("fm_choices.pickle", "rb") as f:
            return pickle.load(f)
    else:
        return {}

DP = DataPuller()
DP.get_data()
BM = BusinessMatching(DP.data_dict)
BM.create_choices_list()
FL = FuzzyList(match_list=BM.choices_set)

top_choices_dict = load_pickle()
start_time = time.time()
full_list = list(BM.choices_set.copy())
diff = len(set(full_list + list(top_choices_dict.keys()))) - len(top_choices_dict.keys())
print("Adding {0} fuzzy matches.".format(diff))
for i, name in enumerate(full_list):
    if name not in top_choices_dict.keys():
        top_choices_dict[name] = FL.get_top_n_matches(name)
        if i % 100 == 0:
            print(str(np.round(i/len(full_list),3) * 100) + "%")
            print(str(time.time() - start_time))
            save_pickle()
save_pickle()
