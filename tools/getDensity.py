#!/usr/bin/env python3

import sys, os
import igraph as ig

"""
	This tool returns an insularity score within a given userlist. That is,
	it tells you what percentage of retweets from the users listed are *other*
	users in the list, rather than outsiders.
"""

if __name__ == "__main__":
	if( len(sys.argv) != 2 ):
		print("USAGE: %s <map.gml>" % sys.argv[0])
		sys.exit(1)
	tweetmap = sys.argv[1]
	net = ig.Graph.Read_GML(tweetmap)
	print("%f" % net.density())
