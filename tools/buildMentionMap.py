#!/usr/bin/env python3

import sys, os, tempfile, shutil

folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder + "/..") # Allow us to import files from one level up

import acquire, analyze, socmap

if __name__ == "__main__":
	if( len(sys.argv) != 5 ):
		print("USAGE: %s <userlist.txt> <directory with tweets> <number of layers> <mentions.gml>" % sys.argv[0])
		sys.exit(1)
	origUserlist = socmap.getUsernames(sys.argv[1])
	tweetDir = sys.argv[2]
	numLayers = int(sys.argv[3])
	outFileName = sys.argv[4]

	if( numLayers < 1 ):
		print("ERROR: Map must include at least one layer")
		sys.exit(1)

	# Work in a random temp directory so we can run multiple instances of
	# this script at once
	workDir = tempfile.TemporaryDirectory()
	workDirName = workDir.name

	# Setup is done, let's read all the tweets we've downloaded
	userlist = origUserlist
	for layer in range(0, numLayers):
		layerMentioned = dict()
		print("Layer %d: Reading data on %d users" % (layer, len(userlist)))
		for username in userlist:
			if( acquire.userTweetsPresent(username, tweetDir) ):
				mentions, rts = acquire.getUserReferences(username, tweetDir)
				layerMentioned[username] = list(mentions)
		print("Layer %d: Saving map" % layer)
		userlist = acquire.flattenUserDictionary(layerMentioned)
		analyze.saveNetwork(workDirName, layer, origUserlist, dict(), layerMentioned)

	# Now move the final map over to the user-requested location
	origFileName = workDirName + "/layer" + str(numLayers) + ".gml"
	shutil.move(origFileName, outFileName)
