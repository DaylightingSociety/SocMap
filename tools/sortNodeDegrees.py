#!/usr/bin/env python3

"""
	This script reads a social map, and prints out users in order of degree.
	Outputs in format:
username,degree
"""

import sys
import networkx as nx

if __name__ == "__main__":
	if( len(sys.argv) != 2 ):
		print("USAGE: %s <map.gml>" % sys.argv[0])
		sys.exit(1)
	mapFilename = sys.argv[1]

	orig = nx.read_gml(mapFilename)

	users = dict()

	for user in orig.nodes(data=True):
		name = user[1]["name"]
		degree = orig.in_degree(name)
		users[name] = degree

	try:
		for username, degree in (sorted(users.items(), key=lambda n: n[1], reverse=True)):
			print("%s,%d" % (username, degree))
	except (BrokenPipeError, IOError):
		pass # Behave yourself when piped to 'head'
