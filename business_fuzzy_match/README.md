# Building Fuzzy Matching for Business Name Cleaning in Data

### Files:
* business_pickle_build.py:
	> Main FM logic. Creates a dict of business names and their top N matches from the passed in csv data dump.
* companies.pickle:
  > Saved output from business_pickle_build.py
* fuzzymatchlist.py:
  > Script for pulling first N fuzzy matches based off input list. Utilizes the package fuzzywuzzy as well as some string gram length logic for speed.
