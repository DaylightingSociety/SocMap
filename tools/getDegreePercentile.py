#!/usr/bin/env python3

import sys, os
import networkx as nx

if __name__ == "__main__":
	if( len(sys.argv) != 3 ):
		print("USAGE: %s <percentile> <inputfile.gml>" % sys.argv[0])
		sys.exit(1)
	percentile = int(sys.argv[1])
	inFilename = sys.argv[2]

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
