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
				continue
			if( response.status_code == 404 ):
				log.log(log.debug, "Exception during data collection: User does not exist")
				continue
			elif( response.status_code == 401 ):
				log.log(log.debug, "Exception during data collection: User account is set to private")
				continue
			remaining = int(response.headers['x-rate-limit-remaining'])
			if( remaining == 0 ):
				reset = int(response.headers['x-rate-limit-reset'])
				reset = datetime.datetime.fromtimestamp(reset)
				delay = (reset - datetime.datetime.now()).total_seconds() + 10 # 10 second buffer
				log.log(log.info, "Rate limited, sleeping "+str(delay)+" seconds")
				if( delay == None or delay <= 0 ):
					delay = 0
				time.sleep(delay)
			else:
				log.log(log.warn, "Exception during data collection: " + str(e))
				continue
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

# Returns the usernames an account is following
def getUserFollowing(api, username):
	usernames = []
	cursor = tweepy.Cursor(api.friends_ids, screen_name=username)
	for accountID in limit_handled(api, cursor.items()):
		u = api.get_user(accountID)
		usernames.append(u.screen_name)
	return usernames

# Returns the usernames of who is following this account
def getUserFollowers(api, username):
	usernames = []
	cursor = tweepy.Cursor(api.followers_ids, screen_name=username)
	for accountID in limit_handled(api, cursor.items()):
		u = api.get_user(accountID)
		usernames.append(u.screen_name)
	return usernames

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

# Builds two related graphs at once:
# One of retweets (seed retweets A, A retweets B, etc)
# One of mentions (seed mentioned A, A mentioned B, etc)
# We save off each layer as a dictionary of which users retweeted/mentioned
# which other users, and also export each layer as a complex graph network
def getLayers(api, numLayers, options, userlist, olduserlist=[]):
	for layer in range(0, numLayers):
		log.log(log.info, "Beginning 'tweet' data collection for layer " + str(layer))
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
				mentions, rts = getUserReferences(username, options.tweetdir)
				if( len(rts) > 0 ):
					nextLayerRTs[username] = list(rts)
				if( len(mentions) > 0 ):
					nextLayerMentions[username] = list(mentions)
		log.log(log.info, "Layer " + str(layer) + " 'tweet' data collection complete, saving user lists...")
		saveUserList(options.workdir, "layer" + str(layer) + "mentionedUsers", nextLayerMentions)
		saveUserList(options.workdir, "layer" + str(layer) + "retweetedUsers", nextLayerRTs)
		log.log(log.info, "Saving network to disk...")
		analyze.saveTweetNetwork(options.mapdir, layer, userlist, nextLayerRTs, nextLayerMentions)

# Graph a tree starting with seeds, arrows to who they're following,
# arrows to who *they're* following, etc
# Simpler than retweets and mentions, but may yield interesting results
def getFollowing(api, numLayers, options, userlist, olduserlist=[]):
	for layer in range(0, numLayers):
		log.log(log.info, "Beginning 'following' data collection for layer " + str(layer))
		if( layer > 0 ):
				oldFollowing = loadUserList(options.workdir, "layer" + str(layer-1) + "followingUsers")
				userlist = list(flattenUserDictionary(oldFollowing))
		nextLayerFollowing = dict()
		for username in userlist:
			following = getUserFollowing(api, username)
			if( len(following) > 0 ):
				nextLayerFollowing[username] = list(following)
		log.log(log.info, "Layer " + str(layer) + " 'following' data collection complete, saving user lists...")
		saveUserList(options.workdir, "layer" + str(layer) + "followingUsers", nextLayerFollowing)
		log.log(log.info, "Saving network to disk...")
		analyze.saveSimpleNetwork(options.mapdir, layer, userlist, nextLayerFollowing, "following")

# Graph a tree starting with seeds, arrows to who's following them,
# arrows to who's following *them*, etc
# Simpler than retweets and mentions, but may yield interesting results
#
# TODO: Would it make sense to invert the arrows on this graph so
# directionality matches getFollowing?
def getFollowers(api, numLayers, options, userlist, olduserlist=[]):
	for layer in range(0, numLayers):
		log.log(log.info, "Beginning 'followers' data collection for layer " + str(layer))
		if( layer > 0 ):
				oldFollowers = loadUserList(options.workdir, "layer" + str(layer-1) + "followerUsers")
				userlist = list(flattenUserDictionary(oldFollowers))
		nextLayerFollowers = dict()
		for username in userlist:
			following = getUserFollowers(api, username)
			if( len(following) > 0 ):
				nextLayerFollowing[username] = list(following)
		log.log(log.info, "Layer " + str(layer) + " 'followers' data collection complete, saving user lists...")
		saveUserList(options.workdir, "layer" + str(layer) + "followerUsers", nextLayerFollowing)
		log.log(log.info, "Saving network to disk...")
		analyze.saveSimpleNetwork(options.mapdir, layer, userlist, nextLayerFollowing, "followers")


