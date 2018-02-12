#!/usr/bin/env python3

# Dependencies
import tweepy, os, jsonpickle, re, json, datetime, time, gzip
import analyze

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
				print("Error on Twitter's end during data collection:", e)
				raise StopIteration
			if( response.status_code == 404 ):
				print("Exception during data collection: User does not exist")
				raise StopIteration
			elif( response.status_code == 401 ):
				print("Exception during data collection: User account is set to private")
				raise StopIteration
			remaining = int(response.headers['x-rate-limit-remaining'])
			if( remaining == 0 ):
				reset = int(response.headers['x-rate-limit-reset'])
				reset = datetime.datetime.fromtimestamp(reset)
				delay = (reset - datetime.datetime.now()).total_seconds() + 10 # 10 second buffer
				print("Rate limited, sleeping ", str(delay), " seconds")
				time.sleep(delay)
			else:
				print("Exception during data collection:", e)
				raise StopIteration # No more data we can read

# Returns whether we have tweets from a particular user stored
def userTweetsPresent(username, tweetdir, compression):
	if( compression ):
		return os.path.isfile(tweetdir + "/" + username + ".json.gz")
	else:
		return os.path.isfile(tweetdir + "/" + username + ".json")

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

# Read tweets back from file, with optional GZIP compression
def loadTweetsFromFile(username, tweetdir, compression):
	if( compression ):
		f = gzip.open(tweetdir + "/" + username + ".json.gz", "rb")
		blob = f.read()
		f.close()
		return jsonpickle.decode(blob.decode())
	else:
		f = open(tweetdir + "/" + username + ".json", "r")
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
def getUserReferences(username, tweetdir, workdir, compression):
	tweets = loadTweetsFromFile(username, tweetdir, compression)
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

def getLayers(api, numLayers, options, userlist):
	for layer in range(0, numLayers):
		if( layer > 0 ):
			oldRTs = loadUserList(options.workdir, "layer" + str(layer-1) + "retweetedUsers")
			oldMentions = loadUserList(options.workdir, "layer" + str(layer-1) + "mentionedUsers")
			rtUsernames = flattenUserDictionary(oldRTs)
			mentionUsernames = flattenUserDictionary(oldMentions)
			userlist = list(rtUsernames.union(mentionUsernames))
		nextLayerRTs = dict()
		nextLayerMentions = dict()
		for username in userlist:
			if( not userTweetsPresent(username, options.tweetdir, options.compress) ):
				getUserTweets(api, username, options.tweetdir, options.numtweets, options.compress)
				mentions, rts = getUserReferences(username, options.tweetdir, options.workdir, options.compress)
				if( len(rts) > 0 ):
					nextLayerRTs[username] = list(rts)
				if( len(mentions) > 0 ):
					nextLayerMentions[username] = list(mentions)
		saveUserList(options.workdir, "layer" + str(layer) + "mentionedUsers", nextLayerMentions)
		saveUserList(options.workdir, "layer" + str(layer) + "retweetedUsers", nextLayerRTs)
		analyze.saveNetwork(options.mapdir, layer, userlist, nextLayerRTs, nextLayerMentions)
