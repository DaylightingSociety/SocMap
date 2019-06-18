#!/usr/bin/env python3
import sys, os

folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder + "/..") # Allow us to import files from one level up

import analyze

# This script takes an existing map, and a text file with a list of usernames, one per line.
# It removes those users, and anything no longer reachable by the seeds, from the map.

if __name__ == "__main__":
	if( len(sys.argv) != 4 ):
		print("USAGE: %s <map.gml> <userlist.txt> <pruned_output.gml>" % sys.argv[0])
		sys.exit(1)
	map1 = sys.argv[1]
	userfile = sys.argv[2]
	output = sys.argv[3]
	with open(userfile, "r") as f:
		userlist = f.read().split("\n")
		userlist = list(map(lambda m: m.lower(), userlist))[:-1]
	analyze.pruneNetwork(map1, userlist, output)
