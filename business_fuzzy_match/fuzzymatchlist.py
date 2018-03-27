from fuzzywuzzy import process
import string

class FuzzyList(object):
    def __init__(self, match_list):
        self.match_list = match_list

    def get_top_n_matches(self, query, n=20):
        search_list = list(self.match_list.copy())
        search_list.remove(query)
        return process.extract(query, search_list, limit=n)


    def get_broken_string(self, string):
        string = string.strip()

    def broken_length(self):
        """
        Create a global dict that is:
        k: length of list of broken string
        v: list of strings with those breaks
        broken string: break first by punc, then strip
        """
