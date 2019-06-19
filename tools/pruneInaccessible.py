#!/usr/bin/env python3

import sys, os
import igraph as ig

# This script deletes all nodes that cannot be reached by the seed layer

if __name__ == "__main__":
	if( len(sys.argv) != 3 ):
		print("USAGE: %s <original.gml> <pruned.gml>" % sys.argv[0])
		sys.exit(1)
	origFilename = sys.argv[1]
	newFilename = sys.argv[2]

	orig = ig.Graph.Read_GML(origFilename)
	seeds = orig.vs.select(layer_eq=0)
	reachable = set()
	for seed in seeds:
		s = seed.index # subcomponents wants index form, not object
		from_s = orig.subcomponent(s, mode=ig.OUT) # Returns list of indices
		reachable.add(s)
		reachable.update(from_s)
	remaining = orig.subgraph(reachable)
	remaining.write_gml(newFilename)
