'''
Funding similarity module
'''

from functools import reduce
from sandbox_ggemelos.transaction_analysis.utils import fetch_transactions, fetch_statement_of_org
from sandbox_ggemelos.transaction_analysis.graphs import Graph
import numpy as np
import datetime
import itertools
from typing import Iterable, Dict, Optional

# SET OF DONORS TO IGNORE
INVALID_PAYEES = set(['Miscellaneous Cash Expenditures $100 and under',
                      'Miscellaneous Cash Contributions $100 and under'])


class SimilarityGraph():
    '''
    Class for graphical representation of funding similarities between committees.  As a similarity measure between
    committee funding sources, we use the projection of the normalized funding profiles
    '''
    def __init__(self,
                 start_date: datetime.date,
                 end_data: datetime.date,
                 min_donation_amount: float=1000,
                 min_similarity: float=0.5):
        '''
        :param start_date: Start date for transactions
        :param end_data: End date for transactions
        :param min_donation_amount: Minimum total donation amount to a committee.  Any total donation amount from donor
                                    below this amount is ignored.  (Default: 1000)
        :param min_similarity: Minimum similarity score for a connection. (Default: 0.5)
        '''
        def map_to_dict(data):
            contributors = data.contributor_payee.values
            amounts = data.amount.values
            return {cont: amt for cont, amt in zip(contributors, amounts)}

        ## GET TRANSCTION DATA
        stmnt_of_org = fetch_statement_of_org()
        trans = fetch_transactions(statement_of_org=stmnt_of_org,
                                   start_date=start_date,
                                   end_date=end_data)
        trans = trans[trans['amount'] > 0]

        # Filter out bad payees
        trans['is_valid'] = trans['contributor_payee'].apply(lambda x: x != 'None' and
                                                                       x not in INVALID_PAYEES and
                                                                       x.count('$') == 0)
        trans = trans[trans['is_valid']]

        ## AGGREGATE TRANSACIONS
        agg_contributions = trans.groupby(['committee_id', 'contributor_payee']).sum().reset_index() \
            .groupby(['committee_id']).apply(map_to_dict).reset_index()
        agg_contributions.columns = ['committee_id', 'donors']

        # Remove committes with less than given min donations
        agg_contributions['is_valid'] = agg_contributions['donors'].apply(
            lambda x: sum(x.values()) >= min_donation_amount)
        agg_contributions = agg_contributions[agg_contributions['is_valid']]
        del agg_contributions['is_valid']

        ## CALCULATE SIMILARITIES
        projections = dict()
        for comm1, comm2 in itertools.combinations(agg_contributions.values, 2):
            cid1, cont1 = comm1
            cid2, cont2 = comm2

            pids = list(set(cont1.keys()) | set(cont2.keys()))

            sig1 = np.array([cont1[pid] if pid in cont1 else 0 for pid in pids])
            sig2 = np.array([cont2[pid] if pid in cont2 else 0 for pid in pids])

            # Map each funding profile to the unit sphere by dividing by the L2-norm
            sig1 = sig1 / np.linalg.norm(sig1)
            sig2 = sig2 / np.linalg.norm(sig2)

            # Calculate the projection between the two normalized funding profiles
            projections[(cid1, cid2) if cid1 < cid2 else (cid2, cid1)] = (
                np.dot(sig1, sig2), len(set(cont1.keys()) & set(cont2.keys())))

        ## BUILD GRAPH
        edges = {(cnames[0], cnames[1]): sim[0] for cnames, sim in projections.items() if sim[0] >= min_similarity}

        self.__graph = Graph(edges)
        self.__agg_contributions = agg_contributions
        self.__trans = trans

    def _group_summary(self, committees: Iterable[str], mode: str = 'union',
                      min_prct: float = 0.01) -> Dict[str, Dict[str, float]]:
        '''
        Calculate a representative funding profile for a group of committees.

        :param committees: List of committees to summarize.
        :param mode: Either union of intersection.  If union, the funding profile consists of all donors in the group.
                     If intersection, the funding profile consists of the donors common to all.
        :param min_prct: Min percent to consider.  Any donor which represent less than the min percentage is removed
                         from the representative funding profile.  (Default: 0.01)
        :return: Dictionary with keys being the donor names and values containing the percent the donor represents of
                 in the funding profile and the overlap with the members in the committee list.  The later being the
                 number of committees in the list that received a donation from the donor.
        '''

        data = []
        for cid in committees:
            temp = self.__agg_contributions[self.__agg_contributions['committee_id'] == cid]['donors'].values
            if temp.size > 0:
                data.append((cid, temp[0]))

        if mode == 'intersection':
            pids = list(reduce(lambda x, y: x & y, (set(donors.keys()) for cid, donors in data)))
        elif mode == 'union':
            pids = list(reduce(lambda x, y: x | y, (set(donors.keys()) for cid, donors in data)))

        sigantures = []
        for cid, donors in data:
            siganture = np.array([donors[pid] if pid in donors else 0 for pid in pids])
            siganture = siganture / np.linalg.norm(siganture)
            sigantures.append(siganture)

        overlap = np.mean(np.vstack(sigantures) > 0, axis=0)
        profile = np.sum(np.vstack(sigantures), axis=0)
        profile = profile / np.sum(profile)

        index = profile >= min_prct
        profile = profile[index]
        overlap = overlap[index]
        pids = np.array(pids)[index]

        profile = profile / np.sum(profile)

        return {pid: {'percent': prct, 'overlap': over} for pid, prct, over in
                sorted(zip(pids, profile, overlap), key=lambda x: x[1], reverse=True)}

    def look_up(self,
                name: str,
                d3_path: Optional[str]=None,
                profile_mode: str='union',
                distance: Optional[int]=None) -> dict:
        '''
        Look up committees with similar funding profiles.

        :param name: Target committee name
        :param d3_path: Optional path to save D3 visualization files.  If None, D3 visualization is not launched.
                        (Default: None)
        :param profile_mode: Mode for funding profile representation.  Either union of intersection.  (Default: union)
        :param distance: Max distance to traverse on the graph for generating the neighborhood.  If None, the full
                         connected component is returned (Default: None)
        :return: Dictionary with list of committees in the neighborhood, donor profile, and graph JSON string.
        '''

        neighborhood = self.__graph.get_neighborhood(node_name=name, distance=distance)
        neighborhood_names = set((self.__graph.get_node_name(gid) for gid in neighborhood.nodes()))


        if d3_path is not None:
            self.__graph.show_in_d3_force_directed(file_path=d3_path,
                                                   nodes=set(neighborhood.nodes),
                                                   groups={'target': [self.__graph.get_node_id(name)]})
        return {'neighborhood': neighborhood_names,
                'donor_profile': self._group_summary(neighborhood_names, mode=profile_mode),
                'graph_json': self.__graph.create_d3_file(nodes=set(neighborhood.nodes),
                                                          groups={'target': [self.__graph.get_node_id(name)]})}




