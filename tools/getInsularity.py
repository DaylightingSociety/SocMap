#!/usr/bin/env python3

import sys, os
folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder + "/..") # Allow us to import files from one level up
import acquire, socmap

"""
	This tool returns an insularity score within a given userlist. That is,
	it tells you what percentage of retweets from the users listed are *other*
	users in the list, rather than outsiders.
"""

if __name__ == "__main__":
	if( len(sys.argv) != 3 ):
		print("USAGE: %s <userlist.txt> <directory with tweets>" % sys.argv[0])
		sys.exit(1)
	tweetdir = sys.argv[2]
	userlist = socmap.getUsernames(sys.argv[1])

	totalRTs = 0
	insularRTs = 0
	for user in userlist:
		if( not acquire.userTweetsPresent(user, tweetdir) ):
			continue
		tweets = acquire.loadTweetsFromFile(user, tweetdir)
		for tweet in tweets:
			if( isinstance(tweet, acquire.Retweet) ):
				totalRTs += 1
				if( tweet.source in userlist ):
					insularRTs += 1

	print("Total RTs in userlist: %d" % totalRTs)
	print("Insular RTs in userlist: %d" % insularRTs)
	print("Insularity score: %f%%" % (float(insularRTs) / float(totalRTs) * 100))
