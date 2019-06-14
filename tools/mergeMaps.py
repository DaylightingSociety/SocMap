#!/usr/bin/env python3
import sys, os

folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder + "/..") # Allow us to import files from one level up

import analyze

if __name__ == "__main__":
	if( len(sys.argv) != 4 ):
		print("USAGE: %s <map1.gml> <map2.gml> <merged.gml>" % sys.argv[0])
		sys.exit(1)
	map1 = sys.argv[1]
	map2 = sys.argv[2]
	merged = sys.argv[3]
	analyze.combineNetworks(map1, map2, merged)
