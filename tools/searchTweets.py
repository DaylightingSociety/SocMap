#!/usr/bin/env python3
import sys, os, shutil, re

folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder + "/..") # Allow us to import files from one level up

from acquire import Tweet, loadTweetsFromFile

if __name__ == "__main__":
	if( len(sys.argv) != 3 ):
		print("USAGE: %s <search_term> <tweetdir>" % sys.argv[0])
		sys.exit(1)
	term = sys.argv[1]
	tweetdir = sys.argv[2]
	search = re.compile(term)

	for filename in os.listdir(tweetdir):
		uname = os.path.basename(filename).split(".")[0]
		tweets = loadTweetsFromFile(uname, tweetdir)
		#print("User '%s' tweets: %d" % (uname, len(tweets)))
		for tweet in tweets:
			if search.match(tweet.text):
				print(tweet.text)
