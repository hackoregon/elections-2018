'''
Graph Module
'''

import os
from io import StringIO
from typing import Dict, Tuple, Optional, Set, Iterable, Any, List
from collections import defaultdict as ddict
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.components import connected as nxconn
from sandbox_ggemelos.transaction_analysis.utils import calc_icdf, CachedProperty
from sandbox_ggemelos import RESOURCES
import json
import webbrowser


class Graph(object):
    '''
    Undirected graph class
    '''

    _GraphType = nx.Graph

    def __init__(self, edges: Dict[Tuple[str, str], float]):
        '''
        :param edges: Dictionary of edges, the key is a tuple of nodes and the value is teh strength of the edge
        '''
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
        self.graph = self._GraphType()
        self.graph.add_weighted_edges_from([(nodes[0], nodes[1], strength) for nodes, strength in edges.items()])

        # Get degree statistics
        self.degrees_counts = ddict(lambda: 0)
        for node in self.nodes:
            self.degrees_counts[self.graph.degree(node)] += 1

    @CachedProperty
    def conn_comp(self) -> List[nx.Graph]:
        '''
        Connected components of the graph
        '''
        return sorted(nxconn.connected_component_subgraphs(self.graph),
                      key=lambda g: g.number_of_nodes(),
                      reverse=True)

    def calc_stats(self, percentiles: Optional[Iterable[float]] = None) -> pd.DataFrame:
        '''
        Returns key statistics for the graph

        :param percentiles: Optinal list of percentages to calculate for key graph statistics
        :return:
        '''

        # Get degree statistics
        print('Number of nodes: {:,.0f}'.format(self.graph.number_of_nodes()))
        print('Number of edges: {:,.0f}'.format(self.graph.number_of_edges()))

        percentiles = percentiles if percentiles is not None else [0.25, 0.5, 0.75, 0.90, 0.99, 1]

        degrees, counts = zip(*self.degrees_counts.items())
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

    def create_d3_file(self,
                       filename: Optional[str]=None,
                       nodes: Optional[Iterable[int]]=None,
                       groups: Optional[Dict[str, Iterable[int]]]=None) -> Optional[str]:
        '''
        Create graph JSON file used with D3 visualization.

        :param filename:  File to save JSON file.  If None, JSON file text is returned as a string. (Default: None)
        :param nodes: List of nodes to include.  If None, all nodes are included (Default: None)
        :param groups: Groups
        :return: Optional[str]
        '''

        lookUp = {}
        node_json = []

        if groups is not None:
            group_lookup = ddict(lambda: 'no group specified')
            for name, group in groups.items():
                group_lookup.update({self.get_node_name(node_id): name for node_id in group})

        if nodes is not None:
            uniqueNodesList = sorted([self.get_node_name(node_id) for node_id in self.nodes if node_id in nodes])
        else:
            uniqueNodesList = sorted([self.get_node_name(node_id) for node_id in self.nodes])

        for i, name in enumerate(uniqueNodesList):
            anonDict = {}
            anonDict["nodeID"] = i
            lookUp[name] = i
            anonDict["name"] = name
            anonDict["group"] = group_lookup[name]
            node_json.append(anonDict)

        link_json = []
        weights = []
        for source, target in self.graph.edges:
            value = abs(self.graph.get_edge_data(source, target)['weight'])
            anonDict = {}
            if self.get_node_name(source) not in uniqueNodesList or self.get_node_name(target) not in uniqueNodesList:
                continue
            sourceID = lookUp[self.get_node_name(source)]
            targetID = lookUp[self.get_node_name(target)]
            anonDict["source"] = sourceID
            anonDict["target"] = targetID
            anonDict["value"] = value

            weights.append(value)
            link_json.append(anonDict)

        # Map edge weights
        min_weight = min(weights)
        max_weight = max(weights)
        for link in link_json:
            if min_weight == max_weight:
                link['value'] = 3
            else:
                link['value'] = 9 * (link['value'] - min_weight) / (max_weight - min_weight) + 1

        load_json = {}
        load_json["nodes"] = node_json
        load_json["links"] = link_json

        if filename is None:
            io = StringIO()
            json.dump(load_json, io, indent=4)
            return io.getvalue()
        else:
            with open(filename, 'w') as fout:
                json.dump(load_json, fout, indent=4)

    def show_in_d3_force_directed(self,
                                  file_path,
                                  nodes: Optional[Iterable[int]]=None,
                                  groups: Optional[Dict[str, Iterable[int]]]=None) -> None:
        '''
        Show graph in D3 visualization.  Function will create necessary D3 files and launch browser to display graph.

        :param file_path: Path to write D3 files
        :param nodes: Optional list of node ids to display.  If not specified, entire graph is plotted.  If the graph is
                      large, this could freeze the browser.
        :param groups: Optional dictionary where keys are group names and values are lists of node ids.
        '''
        def create_d3_html_file(filename: str, graph_file: str) -> None:
            html_code = '''
            <!DOCTYPE html>
            <meta charset="utf-8">
            <style>

            .node {
              stroke: #fff;
              stroke-width: 5px;
            }

            .link {
              stroke: #999;
              stroke-opacity: .6;
            }

            </style>
            <body>
            <script src="%s"></script>
            <script>

            var width = 2000,
                height = 1500;

            var color = d3.scale.category10();

            var force = d3.layout.force()
                .charge(-500)
                .linkDistance(300)
                .size([width, height]);

            var svg = d3.select("body").append("svg")
                .attr("width", width)
                .attr("height", height);

            d3.json("%s", function(error, graph) {
              force
                  .nodes(graph.nodes)
                  .links(graph.links)
                  .start();

              var link = svg.selectAll(".link")
                  .data(graph.links)
                  .enter().append("line")
                  .attr("class", "link")
                  .style("stroke-width", function(d) { return d.value; });

              var node = svg.selectAll(".node")
                  .data(graph.nodes)
                  .enter().append("circle")
                  .attr("class", "node")
                  .attr("r", 10)
                  .style("fill", function(d) { return color(d.group); })
                  .call(force.drag);

              node.append("title")
                  .text(function(d) { return d.name; });

              force.on("tick", function() {
                link.attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node.attr("cx", function(d) { return d.x; })
                    .attr("cy", function(d) { return d.y; });
              });
            });

            </script>
            ''' % (os.path.join(RESOURCES, 'd3.v3.min.js'), graph_file)

            with open(filename, 'w') as fout:
                fout.write(html_code)


        graph_file = os.path.join(file_path, 'graph.json')
        html_file = os.path.join(file_path, 'force_directed.html')

        self.create_d3_file(filename=graph_file, nodes=nodes, groups=groups)
        create_d3_html_file(filename=html_file, graph_file=graph_file)

        webbrowser.open('file://' + html_file)



class DiGraph(Graph):
    '''
    Directed graph class
    '''

    _GraphType = nx.DiGraph

    def __init__(self, edges: Dict[Tuple[str, str], float]):
        '''
        :param edges: Dictionary of edges, the key is a tuple of nodes and the value is teh strength of the edge
        '''
        super().__init__(edges=edges)

        # Get degree statistics
        self.degrees_in_counts = ddict(lambda: 0)
        self.degrees_out_counts = ddict(lambda: 0)
        for node in self.nodes:
            self.degrees_in_counts[self.graph.in_degree(node)] += 1
            self.degrees_out_counts[self.graph.out_degree(node)] += 1


    @property
    def undirected_graph(self) -> nx.Graph:
        '''
        An undirected graph
        '''
        return self.graph.to_undirected()

    @CachedProperty
    def conn_comp(self) -> List[nx.Graph]:
        return sorted(nxconn.connected_component_subgraphs(self.undirected_graph),
                      key=lambda g: g.number_of_nodes(),
                      reverse=True)

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

        return self.graph.subgraph(get_node_list(self.undirected_graph, node_id, distance, [node_id]))
