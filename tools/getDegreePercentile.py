#!/usr/bin/env python3

import sys, os
from collections import Counter
try:
	import igraph as ig
	has_igraph = True
except ImportError:
	import networkx as nx
	has_igraph = False

def nxVersion(inFilename):
	orig = nx.read_gml(inFilename)

	degree = dict()
	inDegree = dict()
	outDegree = dict()

	numNodes = len(orig.nodes())

	for user in orig.nodes(data=True):
		dg = orig.degree(user[0])
		in_dg = orig.in_degree(user[1]["name"])
		out_dg = orig.out_degree(user[1]["name"])

		if( dg in degree.keys() ):
			degree[dg] += 1
		else:
			degree[dg] = 1

		if( in_dg in inDegree.keys() ):
			inDegree[in_dg] += 1
		else:
			inDegree[in_dg] = 1

		if( out_dg in outDegree.keys() ):
			outDegree[out_dg] += 1
		else:
			outDegree[out_dg] = 1
	return (numNodes, degree, inDegree, outDegree)

def igraphVersion(inFilename):
	g = ig.Graph.Read_GML(inFilename)
	numNodes = len(g.vs)
	degree = Counter(g.vs.degree())
	inDegree = Counter(g.vs.indegree())
	outDegree = Counter(g.vs.outdegree())
	return (numNodes, degree, inDegree, outDegree)

if __name__ == "__main__":
	if( len(sys.argv) != 3 ):
		print("USAGE: %s <percentile> <inputfile.gml>" % sys.argv[0])
		sys.exit(1)
	percentile = int(sys.argv[1])
	inFilename = sys.argv[2]

	if( has_igraph ):
		(numNodes, degree, inDegree, outDegree) = igraphVersion(inFilename)
	else:
		(numNodes, degree, inDegree, outDegree) = nxVersion(inFilename)

	def findThreshold(degree, name):
		discoveredNodes = 0
		for dg in sorted(degree.keys(), reverse=True):
			discoveredNodes += degree[dg]
			if( discoveredNodes >= ((percentile / 100.0)*numNodes) ):
				print("%s threshold: Remove nodes with less than %d %s" % (name, dg, name))
				return

	findThreshold(degree, "degree")
	findThreshold(inDegree, "in_degree")
	findThreshold(outDegree, "out_degree")
