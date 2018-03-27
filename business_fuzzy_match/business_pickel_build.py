import pandas as pd
import numpy as np
import time
import re



class BusinessMatching(object):
    def __init__(self, input_file):
        if input_file == None:
            self.input_dataframe = pd.read_csv("transaction_detail_first_batch.csv", low_memory=False)
        else:
            self.input_dataframe = pd.read_csv(input_file, low_memory=False)
        self.build_sub_df()

    def build_sub_df(self):
        self.business_sub_df = transaction_detail_df[self.input_dataframe["Address Book Type"] == "Business Entity"].copy()
