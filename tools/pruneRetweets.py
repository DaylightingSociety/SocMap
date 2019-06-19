#!/usr/bin/env python3

import sys, os
import igraph as ig

# This script deletes all edges with < threshold number of retweets
# It does *not* delete inaccessible nodes afterwards (see pruneInaccessible.py)

if __name__ == "__main__":
	if( len(sys.argv) != 4 ):
		print("USAGE: %s <retweet threshold> <original.gml> <pruned.gml>" % sys.argv[0])
		sys.exit(1)
	retweetThreshold = int(sys.argv[1])
	origFilename = sys.argv[2]
	newFilename = sys.argv[3]

	if( retweetThreshold < 1 ):
		print("ERROR: Retweet threshold must be at least one")
		sys.exit(1)

	orig = ig.Graph.Read_GML(origFilename)
	toPrune = orig.es.select(retweets_lt=retweetThreshold)
	orig.delete_edges(toPrune)
	orig.write_gml(newFilename)
