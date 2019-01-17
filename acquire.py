#!/usr/bin/env python3

# Dependencies
import tweepy, os, jsonpickle, re, json, datetime, time, gzip
import analyze, log

class Tweet(object):
	def __init__(self, user, text, timestamp, mentions):
		self.user = user
		self.text = text
		self.timestamp = timestamp
		self.mentions = mentions

class Retweet(Tweet):
	def __init__(self, user, text, timestamp, mentions, source, retweets):
		super().__init__(user, text, timestamp, mentions)
		self.source = source
		self.retweets = retweets

# When you hit the Twitter API for too long it blocks for 15 minutes
# we'll just wait around for that.
def limit_handled(api, cursor):
	while True:
		try:
			yield cursor.next()
		except tweepy.error.TweepError as e:
			response = api.last_response
			if( response.status_code >= 500 ):
				log.log(log.warn, "Error on Twitter's end during data collection: " + str(e))
				return
			if( response.status_code == 404 ):
				log.log(log.debug, "Exception during data collection: User does not exist")
				return
			elif( response.status_code == 401 ):
				log.log(log.debug, "Exception during data collection: User account is set to private")
				return
			remaining = int(response.headers['x-rate-limit-remaining'])
			if( remaining == 0 ):
				reset = int(response.headers['x-rate-limit-reset'])
				reset = datetime.datetime.fromtimestamp(reset)
				delay = (reset - datetime.datetime.now()).total_seconds() + 10 # 10 second buffer
				log.log(log.info, "Rate limited, sleeping "+str(delay)+" seconds")
				time.sleep(delay)
			else:
				log.log(log.warn, "Exception during data collection: " + str(e))
				return
		# Tweepy still raises StopIteration, which is no longer Pythonic in 3.7
		except StopIteration:
			return

# Returns whether we have tweets from a particular user stored
# Detects compressed and plain JSON files
def userTweetsPresent(username, tweetdir):
	cFile = os.path.isfile(tweetdir + "/" + username + ".json.gz")
	pFile = os.path.isfile(tweetdir + "/" + username + ".json")
	return cFile or pFile

# Saves a tweet blob as JSON, with optional GZIP compression
def saveTweetsToFile(username, tweets, tweetdir, compression):
	tweetDump = jsonpickle.encode(tweets)
	if( compression ):
		f = gzip.open(tweetdir + "/" + username + ".json.gz", "wb")
		tweetDump = bytearray(tweetDump, "utf-8")
	else:
		f = open(tweetdir + "/" + username + ".json", "w")
	f.write(tweetDump)
	f.close()

# Read tweets back from file
# Loads compressed file if available, falls back to plaintext otherwise
def loadTweetsFromFile(username, tweetdir):
	pFilename = tweetdir + "/" + username + ".json"
	cFilename = pFilename + ".gz"
	cFile = os.path.isfile(cFilename)
	pFile = os.path.isfile(pFilename)
	if( cFile ):
		f = gzip.open(cFilename, "rb")
		blob = f.read()
		f.close()
		return jsonpickle.decode(blob.decode())
	else:
		f = open(pFilename, "r")
		blob = f.read()
		f.close()
		return jsonpickle.decode(blob)

# Returns the usernames of people mentioned in a body of text
def getMentionsFromText(text):
	usernames = set()
	p = re.compile("@[A-Za-z0-9_]+")
	res = p.findall(text)
	for username in res:
		usernames.add(username[1:].lower())
	return list(usernames)

# Downloads, parses, and saves tweets for a user
def getUserTweets(api, username, tweetdir, numtweets, compression):
	cursor = tweepy.Cursor(api.user_timeline, screen_name=username, count=numtweets)
	tweets = []
	for tweet in limit_handled(api, cursor.items()):
		mentions = getMentionsFromText(tweet.text)
		date = tweet.created_at
		text = tweet.text
		source = tweet.user.screen_name.lower()
		if( hasattr(tweet, "retweeted_status") ):
			orig_author = tweet.retweeted_status.user.screen_name.lower()
			rt_count = tweet.retweeted_status.retweet_count
			rt = Retweet(source, text, date, mentions, orig_author, rt_count)
			tweets.append(rt)
		else:
			tw = Tweet(source, text, date, mentions)
			tweets.append(tw)
	saveTweetsToFile(username, tweets, tweetdir, compression)

# Parse user tweets, return [[people they mentioned], [people they retweeted]]
def getUserReferences(username, tweetdir):
	tweets = loadTweetsFromFile(username, tweetdir)
	retweeted = set()
	mentioned = set()
	for tweet in tweets:
		if( isinstance(tweet, Retweet) ):
			retweeted.add(tweet.source)
		else:
			for user in tweet.mentions:
				mentioned.add(user)
	return [mentioned, retweeted]

def deleteUserTweets(username, tweetdir):
	os.unlink(tweetdir + "/" + username + ".json")

def saveUserList(workdir, name, dictionary):
	blob = json.dumps(dictionary)
	f = open(workdir + "/" + name + ".json", "w")
	f.write(blob)
	f.close()

def loadUserList(workdir, name):
	f = open(workdir + "/" + name + ".json", "r")
	blob = f.read()
	f.close()
	return json.loads(blob)

def flattenUserDictionary(links):
	res = set()
	for username in links.keys():
		for linkedTo in links[username]:
			res.add(linkedTo)
	return res

def getLayers(api, numLayers, options, userlist, olduserlist=set()):
	for layer in range(0, numLayers):
		log.log(log.info, "Beginning data collection for layer " + str(layer))
		if( layer > 0 ):
			oldRTs = loadUserList(options.workdir, "layer" + str(layer-1) + "retweetedUsers")
			oldMentions = loadUserList(options.workdir, "layer" + str(layer-1) + "mentionedUsers")
			rtUsernames = flattenUserDictionary(oldRTs)
			mentionUsernames = flattenUserDictionary(oldMentions)
			userlist = list(rtUsernames.union(mentionUsernames))
		nextLayerRTs = dict()
		nextLayerMentions = dict()
		for username in userlist:
			if( not userTweetsPresent(username, options.tweetdir) ):
				getUserTweets(api, username, options.tweetdir, options.numtweets, options.compress)
			if( not username in olduserlist ):
				olduserlist.add(username)
				mentions, rts = getUserReferences(username, options.tweetdir)
				if( len(rts) > 0 ):
					nextLayerRTs[username] = list(rts)
				if( len(mentions) > 0 ):
					nextLayerMentions[username] = list(mentions)
		log.log(log.info, "Layer " + str(layer) + " data collection complete, saving user lists...")
		saveUserList(options.workdir, "layer" + str(layer) + "mentionedUsers", nextLayerMentions)
		saveUserList(options.workdir, "layer" + str(layer) + "retweetedUsers", nextLayerRTs)
		log.log(log.info, "Saving network to disk...")
		analyze.saveNetwork(options.mapdir, layer, userlist, nextLayerRTs, nextLayerMentions)
