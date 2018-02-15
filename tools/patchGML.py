#!/usr/bin/env python3
import sys, os, shutil
import networkx as nx

folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder + "/..") # Allow us to import files from one level up

import analyze

if __name__ == "__main__":
	if( len(sys.argv) != 3 ):
		print("USAGE: %s <inputfile.gml> <patched.gml>" % sys.argv[0])
		sys.exit(1)
	inFilename = sys.argv[1]
	patchFilename = sys.argv[2]

	shutil.copy(inFilename, patchFilename)
	analyze.patchGML(patchFilename)
