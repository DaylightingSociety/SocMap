#!/usr/bin/env python3

import re,sys
from shutil import copyfile
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

# When igraph writes to GML, it saves the ids as floats
# When it reads this data back in, it creates an extra "id"
# attribute. If we then add vertices and write to GML again,
# some vertices will have an "id" attribute and some won't,
# and igraph will become *very* confused
# Instead we'll strip the "id" attributes while loading.
def igraphReadGML(filename):
	net = ig.Graph.Read_GML(filename)
	for i in range(0, len(net.vs)):
		if( "id" in net.vs[i].attribute_names() ):
			del net.vs[i]["id"]
	return net

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
	baseUserList = list(baseUsers.keys())
	if( layer == 0 ):
		if( has_igraph ):
			net = ig.Graph(directed=True)
			net.add_vertices(len(baseUserList))
			for i in range(0, len(baseUserList)):
				username = baseUserList[i]
				net.vs[i]["name"] = username
				# NetworkX won't read our GML files unless we include a "label"
				net.vs[i]["label"] = username
				net.vs[i]["layer"] = 0
				net.vs[i]["retweeted"] = "false"
				net.vs[i]["mentioned"] = "false"
				net.vs[i]["tweets"] = baseUsers[username]
		else:
			net = nx.DiGraph()
			for username in baseUserList:
				net.add_node(username, name=username, layer=0, retweeted="false", mentioned="false", tweets=baseUsers[username])
	else:
		# Load old network, update tweet counts for users we now have data on
		if( has_igraph ):
			net = igraphReadGML(oldMapFilename)
			for username in baseUserList:
				net.vs.select(name_eq=username)[0]["tweets"] = baseUsers[username]
		else:
			net = nx.read_gml(oldMapFilename)
			for username in baseUserList:
				net.node[username]["tweets"] = baseUsers[username]

	# Now let's add the new users
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
				net.vs[i]["tweets"] = 0
			else:
				net.add_node(username, name=username, layer=layer+1, retweeted="true", mentioned="true", tweets=0)
		else:
			if( has_igraph ):
				net.add_vertex(username)
				i = net.vs.find(username).index
				net.vs[i]["name"] = username
				net.vs[i]["label"] = username
				net.vs[i]["layer"] = layer+1
				net.vs[i]["retweeted"] = "false"
				net.vs[i]["mentioned"] = "true"
				net.vs[i]["tweets"] = 0
			else:
				net.add_node(username, name=username, layer=layer+1, retweeted="false", mentioned="true", tweets=0)
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
			net.vs[i]["tweets"] = 0
		else:
			net.add_node(username, name=username, layer=layer+1, retweeted="true", mentioned="false", tweets=0)
		nodeNames.add(username)

	# Next, let's add the edges
	for srcUser in retweeted.keys():
		rts = retweeted[srcUser].keys()
		for dstUser in rts:
			if( has_igraph ):
				srcID = net.vs.find(name=srcUser).index
				dstID = net.vs.find(name=dstUser).index
				# Only add edge if it doesn't exist
				if( net.get_eid(srcID,dstID,directed=True,error=False) == -1 ):
					net.add_edge(srcID,dstID,weight=retweeted[srcUser][dstUser])
			else:
				# We didn't declare a multigraph, so networkx will ignore
				# duplicate edges
				net.add_edge(srcUser, dstUser, weight=retweeted[srcUser][dstUser])
	for srcUser in mentioned.keys():
		mts = mentioned[srcUser].keys()
		for dstUser in mts:
			if( has_igraph ):
				srcID = net.vs.find(name=srcUser).index
				dstID = net.vs.find(name=dstUser).index
				# Only add edge if it doesn't exist
				if( net.get_eid(srcID,dstID,directed=True,error=False) == -1 ):
					net.add_edge(srcID,dstID,weight=mentioned[srcUser][dstUser])
			else:
				# We didn't declare a multigraph, so networkx will ignore
				# duplicate edges
				net.add_edge(srcUser, dstUser, weight=mentioned[srcUser][dstUser])

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
		copyfile(newMapFilename, newMapFilenameCytoscape)
		patchGML(newMapFilenameCytoscape)

def combineNetworks(file1, file2, outputfile):
	if( has_igraph ):
		net1 = igraphReadGML(file1)
		net2 = igraphReadGML(file2)
	else:
		net1 = nx.read_gml(file1)
		net2 = nx.read_gml(file2)
		outputfileCytoscape = outputfile + "_cytoscape.gml"

	# Now that the networks are loaded, we'll add net2 onto net1
	# Start with a list of usernames
	if( has_igraph ):
		net1names = set(net1.vs.select()["name"])
		net2names = set(net2.vs.select()["name"])
	else:
		net1names = set(net1.nodes())
		net2names = set(net2.nodes())

	# First, find all the nodes we have to add
	# If a node exists in both graphs, merge the attributes
	toadd = set()
	for name in net2names:
		if( not name in net1names ):
			toadd.add(name)
		else:
			# Merge attributes
			if( has_igraph ):
				net1node = net1.vs.select(name=name)[0]
				net2node = net2.vs.select(name=name)[0]
				if( net2node["mentioned"] == "true" ):
					net1node["mentioned"] = "true"
				if( net2node["retweeted"] == "true" ):
					net1node["retweeted"] = "true"
				net1node["layer"] = min(net1node["layer"], net2node["layer"])
			else:
				if( net2.node[name]["mentioned"] == "true" ):
					net1.node[name]["mentioned"] = "true"
				if( net2.node[name]["retweeted"] == "true" ):
					net1.node[name]["retweeted"] = "true"
				net1.node[name]["layer"] = min(net1.node[name]["layer"], net2.node[name]["layer"])

	# Add all the new nodes with attributes from network2
	# Note: Loads attributes dynamically, so *should* be future-proof to adding
	# more attributes to SocMap
	for name in toadd:
		if( has_igraph ):
			attributes = net2.vs.select(name=name)[0].attributes()
			net1.add_vertex(**attributes)
		else:
			net1.add_node(name, **net2.node[name])

	# Now add all the new edges, copying edge attributes
	# TODO: Merge edge attributes if edge already exists
	# (Low priority since we don't currently have any edge attributes in SocMap)
	if( has_igraph ):
		for name in net2names:
			net2node = net2.vs.select(name=name)[0]
			edges = net2.incident(net2node)
			for edge in edges:
				e = net2.es[edge]
				atts = e.attributes()
				dstName = net2.vs[e.target]["name"]
				srcID = net1.vs.select(name=name)[0].index
				dstID = net1.vs.select(name=dstName)[0].index
				# If edge does not exist, add it with same attributes
				if( net1.get_eid(srcID, dstID, directed=True, error=False) == -1 ):
					net1.add_edge(srcID, dstID, **atts)
	else:
		# NetworkX doesn't provide a clear way to get the edge attributes of
		# all edges between two nodes (net.edges(src) discards the attributes!)
		# So we'll iterate over edges instead of over nodes
		edges = net2.edges.data()
		for (src,dst,attributes) in edges:
			if( not net1.has_edge(src, dst) ):
				net1.add_edge(src, dst, **attributes)

	# Finally, save the resulting network
	if( has_igraph ):
		net1.write_gml(outputfile)
	else:
		nx.write_gml(net1, outputfile)
		copyfile(outputfile, outputfileCytoscape)
		patchGML(outputfileCytoscape)

# Takes a GML filename for input, a Python list of usernames, and an output
# filename. All users from pruneUsernames are removed from the graph. Anything
# not reachable from layer 0 is then pruned from the graph. Resulting network
# is saved to outputfile. You can force low memory usage, which may be slow.
def pruneNetwork(infile, pruneUsernames, outputfile, forceLowMemoryUsage=False):
	if( has_igraph ):
		net1 = igraphReadGML(infile)
	else:
		net1 = nx.read_gml(infile)
		outputfileCytoscape = outputfile + "_cytoscape.gml"

	# Delete all nodes with given usernames
	if( has_igraph ):
		toPrune = net1.vs.select(name_in=pruneUsernames)
		net1.delete_vertices(toPrune)
	else:
		pruneNames = set(pruneUsernames)
		toPrune = [n for n,a in net1.nodes(data=True) if a["name"] in pruneNames]
		net1.remove_nodes_from(toPrune)

	# Now find the seed nodes
	if( has_igraph ):
		seeds = net1.vs.select(layer_eq=0)
	else:
		# NOTE: We could combine this line with the block above to avoid
		# iterating over the graph twice. This is cleaner, but slower.
		# Consider if speed on large graphs is a serious issue.
		seeds = [n for n,a in net1.nodes(data=True) if a["layer"] == 0]

	# Now find everything reachable from the seed nodes
	reachable = set()
	if( has_igraph ):
		for seed in seeds:
			s = seed.index # subcomponents wants index form, not object
			from_s = net1.subcomponent(s, mode=ig.OUT) # Returns list of indices
			reachable.add(s)
			reachable.update(from_s)
	else:
		for seed in seeds:
			reachable.add(seed)
			reachable.update(nx.descendants(net1, seed))

	# Next, delete all nodes not reachable
	if( has_igraph ):
		if( forceLowMemoryUsage ):
			# Delete nodes in place, involves multiple O(n) passes and going
			# between C and Python a few times
			reachable_nodes = [net1.vs[i]["name"] for i in reachable]
			toPrune = net1.vs.select(name_notin=reachable_nodes)
			net1.delete_vertices(toPrune)
		else:
			# Lots of memory? Great, copy just the part of the graph we need
			# one O(n) pass, in C
			net2 = net1.subgraph(reachable)
	else:
		if( forceLowMemoryUsage ):
			toPrune = [n for n in net1.nodes() if n not in reachable]
			net1.remove_nodes_from(toPrune)
		else:
			net2 = net1.subgraph(reachable)

	# Finally, save results
	if( has_igraph ):
		if( forceLowMemoryUsage ):
			net1.write_gml(outputfile)
		else:
			net2.write_gml(outputfile)
	else:
		if( forceLowMemoryUsage ):
			nx.write_gml(net1, outputfile)
		else:
			nx.write_gml(net2, outputfile)
		copyfile(outputfile, outputfileCytoscape)
		patchGML(outputfileCytoscape)
