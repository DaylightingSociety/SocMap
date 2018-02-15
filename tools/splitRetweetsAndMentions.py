#!/usr/bin/env python3
import sys, os
import networkx as nx

if __name__ == "__main__":
	if( len(sys.argv) != 4 ):
		print("USAGE: %s <inputfile.gml> <retweets.gml> <mentions.gml>" % sys.argv[0])
		sys.exit(1)
	inFilename = sys.argv[1]
	rtFilename = sys.argv[2]
	mentionFilename = sys.argv[3]

	orig = nx.read_gml(inFilename)
	rtGraph = nx.DiGraph()
	mentionGraph = nx.DiGraph()

	rtCopyNodes = []
	rtCopyEdges = []
	mentionCopyNodes = []
	mentionCopyEdges = []

	for user in orig.nodes(data=True):
		if( user[1]["retweeted"] == "true" or user[1]["layer"] == 0 ):
			rtCopyNodes.append(user)
		if( user[1]["mentioned"] == "true" or user[1]["layer"] == 0 ):
			mentionCopyNodes.append(user)

	rtGraph.add_nodes_from(rtCopyNodes)
	mentionGraph.add_nodes_from(mentionCopyNodes)

	for edge in orig.edges(data=True):
		src = edge[0]
		dst = edge[1]
		data = edge[2]
		if( src in rtGraph and dst in rtGraph ):
			rtCopyEdges.append(edge)
		if( src in mentionGraph and dst in mentionGraph ):
			mentionCopyEdges.append(edge)

	rtGraph.add_edges_from(rtCopyEdges)
	mentionGraph.add_edges_from(mentionCopyEdges)

	nx.write_gml(rtGraph, rtFilename)
	nx.write_gml(mentionGraph, mentionFilename)
