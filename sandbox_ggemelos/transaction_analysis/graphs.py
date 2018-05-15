'''
Graph Module
'''


from typing import Dict, Tuple, Optional, Set, Iterable
from collections import defaultdict as ddict
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.components import connected as nxconn
from sandbox_ggemelos.transaction_analysis.utils import calc_icdf


class Graph(object):
    '''
    Class for Graphical Analysis of Transactions
    '''

    def __init__(self, edges: Dict[Tuple[str, str], float], calc_connected_comp: bool = False):
        sources, sinks = zip(*edges.keys())

        # Relabel Nodes with Ints
        node_names = set(sources + sinks)
        self.__name_lookup = {node_id: node_name for node_id, node_name in enumerate(node_names)}
        self.__id_lookup = {node_name: node_id for node_id, node_name in self.__name_lookup.items()}
        edges = {(self.__id_lookup[epoints[0]], self.__id_lookup[epoints[1]]): val for epoints, val in edges.items()}

        sources, sinks = zip(*edges.keys())
        self.sources = np.unique(np.array(sources))
        self.sinks = np.unique(np.array(sinks))
        self.nodes = np.unique(np.hstack((self.sources, self.sinks)))

        # Create Graph
        self.graph = nx.Graph()
        self.graph.add_weighted_edges_from([(nodes[0], nodes[1], strength) for nodes, strength in edges.items()])

        # Get degree statistics
        self.degrees = ddict(lambda: 0)
        for node in self.nodes:
            self.degrees[self.graph.degree(node)] += 1

        # Calc connected comp
        if calc_connected_comp:
            self.conn_comp = sorted(nxconn.connected_component_subgraphs(self.graph),
                                    key=lambda g: g.number_of_nodes(),
                                    reverse=True)
        else:
            self.conn_comp = None

    def calc_stats(self, percentiles: Optional[Iterable[float]] = None) -> pd.DataFrame:

        # Get degree statistics
        print('Number of nodes: {:,.0f}'.format(self.graph.number_of_nodes()))
        print('Number of edges: {:,.0f}'.format(self.graph.number_of_edges()))

        percentiles = percentiles if percentiles is not None else [0.25, 0.5, 0.75, 0.90, 0.99, 1]

        degrees, counts = zip(*self.degrees.items())
        prct_degree = calc_icdf(percentiles, counts, degrees)

        df = pd.DataFrame(data=prct_degree,
                          columns=['Degree'],
                          index=['{:,.2%}'.format(pp) for pp in percentiles])

        if self.conn_comp is not None:

            print('Number of connected components: {:,.0f}'.format(len(self.conn_comp)))

            ccsize = ddict(lambda: 0)
            for ccomp in self.conn_comp:
                ccsize[ccomp.number_of_nodes()] += 1

            ccsize, counts = zip(*ccsize.items())
            prct_ccsize = calc_icdf(percentiles, counts, ccsize)

        df['Connected Component Size'] = prct_ccsize

        df['Degree'] = df['Degree'].apply(lambda x: '{:,.2f}'.format(x))
        df['Connected Component Size'] = df['Connected Component Size'].apply(lambda x: '{:,.2f}'.format(x))

        return df

    def get_node_name(self, node_id: int) -> str:
        '''
        Node graph id to node name lookup
        '''
        return self.__name_lookup[node_id]

    def get_node_id(self, node_name: str) -> int:
        '''
        Node name to node graph id lookup
        '''
        return self.__id_lookup[node_name]

    def get_neighborhood(self, node_name=None, node_id=None, distance: Optional[int] = 1,
                         valid_bridging_node_ids: Optional[Set[int]] = None) -> nx.DiGraph:
        '''
        Find the subgraph consiting off all nodes a set distance from the specified node.  Can specify the
        set of nodes which can be tranversed/used to bridge, e.g. can choose to only bridge on nodes representing
        committees.  None commite nodes can appear in teh resulting subgraph, but can not used to connect to otherwise
        unconnected subgraphs

        :param node_name: Name of node in desired subgraph (can specify name or id)
        :param node_id: Id of node in desired subgraph (can specify name or id)
        :param distance: Max distance from specified node to include in subgraph.  If None, returns entire
                         connected component (default: 1)
        :param valid_bridging_nodes: Set of node ids to which can be traversed, the connecting nodes.  The set must be
                                     the node ids and not the node names. If not specified, all conected node will be
                                     transerved.
        '''

        def get_node_list(graph, node_id, distance, nodes):
            if distance == 0:
                return nodes + [node_id]
            else:
                neighborhood = [neigh for neigh in graph.adj[node_id] if neigh not in nodes]
                for neigh in neighborhood:
                    nodes = nodes + [neigh]
                    if valid_bridging_node_ids is None or neigh in valid_bridging_node_ids:
                        nodes = get_node_list(graph, neigh, None if distance is None else distance - 1, nodes)

                return nodes


        node_id = node_id if node_id is not None else self.get_node_id(node_name)

        return self.graph.subgraph(get_node_list(self.graph, node_id, distance, [node_id]))