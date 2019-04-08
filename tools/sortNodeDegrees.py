#!/usr/bin/env python3

"""
	This script reads a social map, and prints out users in order of degree.
	Outputs in format:
username,degree
"""

import sys
import igraph as ig

if __name__ == "__main__":
	if( len(sys.argv) != 2 ):
		print("USAGE: %s <map.gml>" % sys.argv[0])
		sys.exit(1)
	mapFilename = sys.argv[1]

	orig = ig.Graph.Read_GML(mapFilename)

	users = []

	for i,e in enumerate(orig.vs):
		users.append((e["name"], orig.degree(i, mode="in")))

	try:
		for username, degree in (sorted(users, key=lambda n: n[1], reverse=True)):
			print("%s,%d" % (username, degree))
	except (BrokenPipeError, IOError):
		pass # Behave yourself when piped to 'head'
