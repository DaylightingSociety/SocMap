#!/usr/bin/env python3

import sys, os
import igraph as ig

"""
	This tools returns a density measurement for each map provided as an argument
	and prints the densities in order
"""

if __name__ == "__main__":
	if( len(sys.argv) < 2 ):
		print("USAGE: %s <map.gml> [map2.gml...]" % sys.argv[0])
		sys.exit(1)

	for fname in sys.argv[1:]:
		net = ig.Graph.Read_GML(fname)
		print("%s,%f" % (fname,net.density()))
