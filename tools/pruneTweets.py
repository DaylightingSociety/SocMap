#!/usr/bin/env python3

import sys, os
import igraph as ig

# This script deletes all nodes with < threshold number of tweets
# It does *not* delete inaccessible nodes afterwards (see pruneInaccessible.py)

if __name__ == "__main__":
	if( len(sys.argv) != 4 ):
		print("USAGE: %s <tweet threshold> <original.gml> <pruned.gml>" % sys.argv[0])
		sys.exit(1)
	tweetThreshold = int(sys.argv[1])
	origFilename = sys.argv[2]
	newFilename = sys.argv[3]

	if( tweetThreshold < 1 ):
		print("ERROR: Tweet threshold must be at least one")
		sys.exit(1)

	orig = ig.Graph.Read_GML(origFilename)
	toPrune = orig.vs.select(tweets_lt=tweetThreshold)
	orig.delete_vertices(toPrune)
	orig.write_gml(newFilename)
