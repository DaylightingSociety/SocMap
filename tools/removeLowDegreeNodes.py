#!/usr/bin/env python3

import sys, os
import networkx as nx

if __name__ == "__main__":
	if( len(sys.argv) != 4 ):
		print("USAGE: %s <degree threshold> <original.gml> <pruned.gml>" % sys.argv[0])
		sys.exit(1)
	degreeThreshold = int(sys.argv[1])
	origFilename = sys.argv[2]
	newFilename = sys.argv[3]

	if( degreeThreshold < 1 ):
		print("ERROR: Degree threshold must be at least one")
		sys.exit(1)

	orig = nx.read_gml(origFilename)
	pruned = nx.DiGraph()

	remainingUsers = []
	remainingEdges = []

	nodes = orig.nodes(data=True)
	for i in range(0, len(nodes)):
		user = nodes[i]
		name = user[1]["name"]
		layer = user[1]["layer"]
		degree = orig.in_degree(name)
		if( layer == 0 or degree >= degreeThreshold ):
			remainingUsers.append(user)

	pruned.add_nodes_from(remainingUsers)

	for edge in orig.edges(data=True):
		src = edge[0]
		dst = edge[1]
		data = edge[2]
		if( src in pruned and dst in pruned ):
			remainingEdges.append(edge)

	pruned.add_edges_from(remainingEdges)
	nx.write_gml(pruned, newFilename)
