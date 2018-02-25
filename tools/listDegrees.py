#!/usr/bin/env python3
import sys, os
import networkx as nx

if __name__ == "__main__":
	if( len(sys.argv) != 2 ):
		print("USAGE: %s <inputfile.gml>" % sys.argv[0])
		sys.exit(1)
	inFilename = sys.argv[1]

	orig = nx.read_gml(inFilename)

	degree = dict()

	for user in orig.nodes(data=True):
		dg = orig.degree(user[0])
		if( dg in degree.keys() ):
			degree[dg] += 1
		else:
			degree[dg] = 1

	for dg in sorted(degree.keys(), reverse=True):
		print("%d: %d" % (dg, degree[dg]))
