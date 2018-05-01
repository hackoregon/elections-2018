
import pickle
import requests
from pandas import DataFrame as DF, Series
import numpy as np


client_token = '230875850816746|hh1JJh8ebiRPuFb_V85xqto4lNo'
def search(q):
    url = 'https://graph.facebook.com/v2.12/search?'
    params = {'access_token': client_token,
              'q': q,
              'type': 'place',
              'fields': 'category_list,about,website,name,location'}
    r = requests.get(url, params=params).json()['data']
    if len(r) > 0:
        r = [x["name"] for x in r]
        return r[0]
    else:
        return None
    """if len(r) > 0:
        locations = []
        results = []
        for d in r:
            for k in list(d):
                if k == 'category_list':
                    d[k] = ','.join([_['name'] for _ in d[k]])
                elif k == 'location':
                    _ = d[k].copy()
                    _['id'] = d['id']
                    locations.append(_)
                    del d[k], _
            results.append(d)
        return DF(results).merge(DF(locations), on='id')
    else:
        return None"""
