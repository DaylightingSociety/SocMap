#!/usr/bin/env python3
import sys, os, shutil, re

folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder + "/..") # Allow us to import files from one level up

from acquire import Tweet, loadTweetsFromFile

if __name__ == "__main__":
	if( len(sys.argv) < 3 ):
		print("USAGE: %s <search term as regular expression> <tweetdir> [username] ..." % sys.argv[0])
		sys.exit(1)
	term = sys.argv[1]
	search = re.compile(term)
	tweetdir = sys.argv[2]

	# If provided a list of users, check those
	if( len(sys.argv) >= 4 ):
		for username in sys.argv[3:]:
			tweets = loadTweetsFromFile(username, tweetdir)
			for tweet in tweets:
				if search.match(tweet.text):
					print(tweet.text)

	# Otherwise, check all users in the tweetdir by default
	else:
		for filename in os.listdir(tweetdir):
			username = os.path.basename(filename).split(".")[0]
			tweets = loadTweetsFromFile(username, tweetdir)
			for tweet in tweets:
				if search.match(tweet.text):
					print(tweet.text)
