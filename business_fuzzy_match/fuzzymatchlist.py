from fuzzywuzzy import process
import string

class FuzzyList(object):
    """
    Class for building a list of the top n fuzzy matches in a list.
    """
    def __init__(self, match_list):
        self.match_list = match_list
        self.rem_punc = self.get_removable_punc()
        self.build_broken_length()

    def get_top_n_matches(self, query, n=20):
        """
        Creates a sub-list to search for fuzzy matches of +- 1 word length in query string.
        Searches sublist for the top 20 matches.
        """
        count, query = self.get_broken_string(query)
        if count > 1:
            search_list = self.broken_length_dict[count - 1] + self.broken_length_dict[count] + self.broken_length_dict[count + 1]
        else:
            search_list = self.broken_length_dict[count + 1] + self.broken_length_dict[count]
        if query in search_list:
            search_list.remove(query)
        return process.extract(query, search_list, limit=n)

    def get_broken_string(self, string):
        """
        Strips string of characters.
        Breaks string into word parts, counts number
        Joins string, returns with count
        """
        translator = str.maketrans(self.rem_punc, " "*len(self.rem_punc))
        string = string.translate(translator)
        split_string = [x.strip() for x in string.split(" ") if len(x) > 0]
        count = len(split_string)
        return (count, str.join(" ", split_string))

    def build_broken_length(self):
        """
        Builds a dictionary of length of strings in words and the corrisponding string for searching
        """
        self.broken_length_dict = {}
        for match_item in self.match_list:
            count, c_match_item = self.get_broken_string(match_item)
            if count in self.broken_length_dict.keys():
                self.broken_length_dict[count].append(c_match_item)
            else:
                self.broken_length_dict[count] = [c_match_item]

    def get_removable_punc(self):
        """
        Only want to remove specific punctuation, in this case, everything but '&'
        """
        punc = string.punctuation
        andtrans = str.maketrans("", "", "&")
        return punc.translate(andtrans)
