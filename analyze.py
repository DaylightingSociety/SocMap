#!/usr/bin/env python3

from graph_tool.all import *
import re

# NetworkX produces GML files that include a numeric 'label' attribute.
# This attribute prevents Cytoscape from opening the files, so we'll patch it.
def patchGML(filename):
	with open(filename, "r+") as f:
		content = f.read()
		newcontent = re.sub("label (\S+)\s+", r'', content)
		f.seek(0, 0)
		f.truncate()
		f.write(newcontent)

def saveNetwork(mapDir, layer, baseUsers, retweeted, mentioned):
	net = None
	oldMapFilename = None
	newMapFilename = mapDir + "/layer" + str(layer+1) + ".gml"
	newMapFilenameCytoscape = mapDir + "/layer" + str(layer+1) + "_cytoscape.gml"
	if( layer > 0 ):
		oldMapFilename = mapDir + "/layer" + str(layer) + ".gml"

	# For layer 0 we need to explicitly create seed nodes
	users = dict()
	u_name = g.new_vertex_property("string")
	u_layer = g.new_vertex_property("int")
	u_retweeted = g.new_vertex_property("bool")
	if( layer == 0 ):
		net = Graph()
		for username in baseUsers:
			users[user]

# ENDED HERE, NEED TO GIVE ATTRIBUTES TO EACH USER

			net.add_node(username, name=username, layer=0, retweeted="false", mentioned="false")
	else:
		net = nx.read_gml(oldMapFilename)

	# Now let's add the new users
	# This is messy, because we have to add all of the users *and* their
	# attributes up front -- there's no clean way to update them later
	mentionedUsernames = set()
	retweetedUsernames = set()
	nodeNames = set(net.nodes())
	# Get a set of all the usernames we'll be working with
	for srcUser in retweeted.keys():
		rts = retweeted[srcUser]
		for dstUser in rts:
			if( dstUser not in nodeNames ):
				retweetedUsernames.add(dstUser)
	for srcUser in mentioned.keys():
		rts = mentioned[srcUser]
		for dstUser in rts:
			if( dstUser not in nodeNames ):
				mentionedUsernames.add(dstUser)
	# Now add those usernames with appropriate retweeted/mentioned attributes
	for username in mentionedUsernames:
		if( username in nodeNames ):
			next
		if( username in retweetedUsernames ):
			net.add_node(username, name=username, layer=layer+1, retweeted="true", mentioned="true")
		else:
			net.add_node(username, name=username, layer=layer+1, retweeted="false", mentioned="true")
		nodeNames.add(username)
	for username in retweetedUsernames:
		if( username in nodeNames or username in mentionedUsernames ):
			next
		net.add_node(username, name=username, layer=layer+1, retweeted="true", mentioned="false")
		nodeNames.add(username)

	# Next, let's add the edges
	for srcUser in retweeted.keys():
		rts = retweeted[srcUser]
		for dstUser in rts:
			net.add_edge(srcUser, dstUser)
	for srcUser in mentioned.keys():
		mts = mentioned[srcUser]
		for dstUser in mts:
			net.add_edge(srcUser, dstUser)

	# Finally save it to disk
	nx.write_gml(net, newMapFilename)
	nx.write_gml(net, newMapFilenameCytoscape)
	patchGML(newMapFilenameCytoscape)
