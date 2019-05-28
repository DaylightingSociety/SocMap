#!/usr/bin/env python3

# Dependencies
import argparse, sys, signal, os, threading
import tweepy

# Local imports
import acquire, log

# Signal handler for Control-C
def sigExit(signal, frame):
	print("") # Send newline in platform-agnostic way
	# Perform any cleanup here
	sys.exit(0)

# Custom argument parser that prints usage information
# when something goes wrong
class Parser(argparse.ArgumentParser):
	def error(self, message):
		sys.stderr.write('error: %s\n' % message)
		self.print_help()
		sys.exit(2)	

def parseOptions():
	descr = "A Framework for Social-Network Mapping"
	currentdir = os.path.dirname(os.path.realpath(__file__))
	parser = Parser(description=descr)
	parser.add_argument("-c", "--compress", default=False,
	                    action="store_true", dest="compress", 
	                    help="Compress downloaded tweets with GZIP")
	parser.add_argument("-l", "--layers", default=3,
	                    action="store", type=int, dest="layers", 
	                    help="How many layers out to download")
	parser.add_argument("-n", "--numtweets", default=1000,
	                    action="store", type=int, dest="numtweets",
	                    help="How many tweets to download from each user")
	parser.add_argument("-M", "--maxreferences", default=float('inf'),
	                    action="store", type=int, dest="maxreferences",
	                    help="Maximum number of retweeted and mentioned users to track per user")
	parser.add_argument("-w", "--workdir", default=currentdir+"/work",
	                    action="store", type=str, dest="workdir",
	                    help="Where to store temporary files")
	parser.add_argument("-t", "--tweetdir", default=currentdir+"/tweets",
	                    action="store", type=str, dest="tweetdir",
	                    help="Where to store downloaded tweets")
	parser.add_argument("-m", "--mapdir", default=currentdir+"/map",
	                    action="store", type=str, dest="mapdir",
	                    help="Where to store map data")
	parser.add_argument("-a", "--authfile", metavar="<file>", required=True,
	                    action="store", type=str, dest="authfile", 
	                    help="File containing consumer keys and access tokens")
	parser.add_argument("-u", "--userlist", metavar="<file>", required=True,
	                    action="store", type=str, dest="userlist", 
	                    help="File containing list of starting usernames")
	parser.add_argument("-L", "--logfile", metavar="<file>", default=None,
	                    action="store", type=str, dest="logfile",
	                    help="Where to store log data relative to workdir (detault stdout)")
	parser.add_argument("-d", "--debug", default=False,
	                    action="store_true", dest="debug",
	                    help="Enable debug-level logging")
	options = parser.parse_args()
	return options

# Read authentication keys from a file
def loadKeys(authfile):
	f = open(authfile, "r")
	lines = f.readlines()
	consumer_key = lines[0].rstrip()
	consumer_secret = lines[1].rstrip()
	access_token = lines[2].rstrip()
	access_token_secret = lines[3].rstrip()
	f.close()
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api = tweepy.API(auth)
	return api

# Pulls initial usernames from a file
def getUsernames(filename):
	usernames = []
	f = open(filename)
	lines = f.readlines()
	f.close()
	for line in lines:
		usernames.append(line.rstrip().lower())
	return usernames

# Make sure the directories we need exist before we try to save files
def createDirectories(options):
	for d in [options.tweetdir, options.mapdir, options.workdir]:
		if( not os.path.isdir(d) ):
			print("WARNING: Directory '" + d + "' does not exist - creating...")
			os.mkdir(d)

def startLogging(workdir, logfile, debug):
	logger = threading.Thread(target=log.logHandler, args=(workdir, logfile, debug))
	logger.daemon = True
	logger.start()

if __name__ == "__main__":
	options = parseOptions()
	createDirectories(options)
	api = loadKeys(options.authfile)
	layer0 = getUsernames(options.userlist)
	startLogging(options.workdir, options.logfile, options.debug)
	acquire.getLayers(api, options.layers, options, layer0)
