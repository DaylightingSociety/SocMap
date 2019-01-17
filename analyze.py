#!/usr/bin/env python3

import re,sys
try:
	import igraph as ig
	has_igraph = True
except ImportError:
	import networkx as nx
	has_igraph = False
except ImportError:
	sys.stderr.write("ERROR: Module requires either igraph (preferred) or networkx (slower)")
	sys.exit(1)
import log

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
	if( layer == 0 ):
		if( has_igraph ):
			net = ig.Graph(directed=True)
			net.add_vertices(len(baseUsers))
			for i in range(0, len(baseUsers)):
				username = baseUsers[i]
				net.vs[i]["name"] = username
				# NetworkX won't read our GML files unless we include a "label"
				net.vs[i]["label"] = username
				net.vs[i]["layer"] = 0
				net.vs[i]["retweeted"] = "false"
				net.vs[i]["mentioned"] = "false"
		else:
			net = nx.DiGraph()
			for username in baseUsers:
				net.add_node(username, name=username, layer=0, retweeted="false", mentioned="false")
	else:
		if( has_igraph ):
			# When igraph writes to GML, it saves the ids as floats
			# When it reads this data back in, it creates an extra "id"
			# attribute. If we then add vertices and write to GML again,
			# some vertices will have an "id" attribute and some won't,
			# and igraph will become *very* confused
			net = ig.Graph.Read_GML(oldMapFilename)
			for i in range(0, len(net.vs)):
				if( "id" in net.vs[i].attribute_names() ):
					del net.vs[i]["id"]
		else:
			net = nx.read_gml(oldMapFilename)

	# Now let's add the new users
	# This is messy in networkx, because we have to add all of the users *and*
	# their attributes up front -- there's no clean way to update them later
	mentionedUsernames = set()
	retweetedUsernames = set()
	if( has_igraph ):
		nodeNames = set(net.vs.select()["name"])
	else:
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
			continue
		if( username in retweetedUsernames ):
			if( has_igraph ):
				net.add_vertex(username)
				i = net.vs.find(username).index
				net.vs[i]["name"] = username
				net.vs[i]["label"] = username
				net.vs[i]["layer"] = layer+1
				net.vs[i]["retweeted"] = "true"
				net.vs[i]["mentioned"] = "true"
			else:
				net.add_node(username, name=username, layer=layer+1, retweeted="true", mentioned="true")
		else:
			if( has_igraph ):
				net.add_vertex(username)
				i = net.vs.find(username).index
				net.vs[i]["name"] = username
				net.vs[i]["label"] = username
				net.vs[i]["layer"] = layer+1
				net.vs[i]["retweeted"] = "false"
				net.vs[i]["mentioned"] = "true"
			else:
				net.add_node(username, name=username, layer=layer+1, retweeted="false", mentioned="true")
		nodeNames.add(username)
	for username in retweetedUsernames:
		if( username in nodeNames ):
			continue
		if( has_igraph ):
			net.add_vertex(username)
			i = net.vs.find(username).index
			net.vs[i]["name"] = username
			net.vs[i]["label"] = username
			net.vs[i]["layer"] = layer+1
			net.vs[i]["retweeted"] = "true"
			net.vs[i]["mentioned"] = "false"
		else:
			net.add_node(username, name=username, layer=layer+1, retweeted="true", mentioned="false")
		nodeNames.add(username)

	# Next, let's add the edges
	for srcUser in retweeted.keys():
		rts = retweeted[srcUser]
		for dstUser in rts:
			if( has_igraph ):
				srcID = net.vs.find(name=srcUser).index
				dstID = net.vs.find(name=dstUser).index
				# Only add edge if it doesn't exist
				if( net.get_eid(srcID,dstID,directed=True,error=False) == -1 ):
					net.add_edge(srcID,dstID)
			else:
				# We didn't declare a multigraph, so networkx will ignore
				# duplicate edges
				net.add_edge(srcUser, dstUser)
	for srcUser in mentioned.keys():
		mts = mentioned[srcUser]
		for dstUser in mts:
			if( has_igraph ):
				srcID = net.vs.find(name=srcUser).index
				dstID = net.vs.find(name=dstUser).index
				# Only add edge if it doesn't exist
				if( net.get_eid(srcID,dstID,directed=True,error=False) == -1 ):
					net.add_edge(srcID,dstID)
			else:
				# We didn't declare a multigraph, so networkx will ignore
				# duplicate edges
				net.add_edge(srcUser, dstUser)

	# Finally save it to disk
	if( has_igraph ):
		try:
			net.write_gml(newMapFilename)
		except ig._igraph.InternalError:
			# Sometimes igraph freaks out and won't save as GML
			# but it saves fine as GraphML, and we can convert
			msg = "Could not save GML file: We will save a GraphML file and "
			msg += "what we can export to GML to aid in debugging"
			log.log(log.warn, msg)
			net.write_graphml(newMapFilename+".graphml")
			tmp = ig.Graph.Read_GraphML(newMapFilename+".graphml")
			tmp.write_gml(newMapFilename)
	else:
		nx.write_gml(net, newMapFilename)
		nx.write_gml(net, newMapFilenameCytoscape)
		patchGML(newMapFilenameCytoscape)
