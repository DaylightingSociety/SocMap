#!/usr/bin/env python3
import igraph as ig
import sys

if __name__ == "__main__":
	if( len(sys.argv) != 3 ):
		print("USAGE: %s <map.gml> <output.gml>" % sys.argv[0])
		sys.exit(1)

net = ig.Graph.Read_GML(sys.argv[1])
print("Network loaded.")
prune = []
for i,e in enumerate(net.vs):
	if( e["layer"] > 0 and e["retweeted"] == "false" ):
		prune.append(i)
print("Vertices selected.")
net.delete_vertices(prune)
print("Vertices deleted.")
net2 = net.components(mode="weak").giant()
print("Giant component isolated.")
net2.write_gml(sys.argv[2])
print("Pruned network saved.")
