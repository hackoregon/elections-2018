import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import time
import json
import re



class data 
transaction_detail_df = pd.read_csv("./transaction_detail_first_batch.csv", low_memory=False)

business_sub_df = transaction_detail_df[transaction_detail_df["Address Book Type"] == "Business Entity"].copy()
