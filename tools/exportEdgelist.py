#!/usr/bin/env python3

import sys
import igraph as ig

# Some networking tools only accept input in space-delimited edgelist format
# Like "source destination weight"
# This tool will read an arbitrary GML file output by SocMap, and re-exports
# in the painful edgelist format. You'll lose all metadata except node names
# and edge weight, but hopefully that's good enough!

if __name__ == "__main__":
	if( len(sys.argv) != 2 ):
		print("USAGE: %s <network.gml>" % sys.argv[0])
		sys.exit(1)
	filename = sys.argv[1]
	g = ig.Graph.Read_GML(filename)
	for e in g.es:
		srcID = e.source
		dstID = e.target
		srcName = g.vs[srcID]["name"]
		dstName = g.vs[dstID]["name"]
		weight = 1.0
		if( "weight" in e.attribute_names() ):
			weight = float(e["weight"])
		print("%s %s %f" % (srcName, dstName, weight))
