import glob
import sys
from ete3 import Tree
from collections import defaultdict
from collections import Counter
import pandas as pd


tree_in = sys.argv[1]
queries_in = sys.argv[2]
outname = sys.argv[3]


def unpack_family(node, leaves, query, seen, queries):
    """
    get all leaves under a parental node
    """
    children = node.get_children()
    for child in children:
        childname = str(child).replace("--","").replace("/-", "").replace("\-", "").replace("\n","")
        if child.is_leaf() and childname not in queries:
                seen.append(childname)
                leaves.append(childname)
        elif not child.is_leaf() and childname not in seen:
            seen.append(childname)
            unpack_family(child, leaves, query, seen, queries) 
        elif child.is_leaf() and childname == query:
            seen.append(childname)
        else:
            pass
    if len(leaves)==0:
        parentnode = node.up
        unpack_family(parentnode, leaves, query, seen, queries) 
    return leaves


def get_closestrelative(query, leaves, node, tree):
    distance = 10
    closestrelative = "nd"
    for child in leaves:
        if child != query:
            newdist = t.get_distance(child, query, topology_only = False)
            if newdist < distance:
                distance = newdist
                closestrelative = child
            else:
                pass
    return closestrelative, distance


def get_neighbor(t, query, queries):
    tree_dict_nn = {} 
    for node in t.traverse():
        if node.name == query:
            child = str(node.name).replace("--","").replace("/-", "").replace("\-", "").replace("\n","")
            queryintree = node.name
            # move up one node in the tree
            # collect all terminal leaves under the parent node
            leaves = []
            seen = []
            leaves = unpack_family(node, leaves, query, seen, queries)
            closestrelative, distance = get_closestrelative(queryintree, leaves, node, t)
            tree_dict_nn[closestrelative] = distance
    return tree_dict_nn


# get queries
with open(queries_in) as infile:
    queries = infile.read().splitlines()

# all distances
tree_dict_all = {}
# dict with only single paralog that had shortest distance to reference
for query in queries:
    t = Tree(tree_in)
    tree_dict_all[query] =  get_neighbor(t, query, queries)

df = pd.DataFrame.from_dict(tree_dict_all).fillna("nd").T
df.to_csv(outname, sep="\t")
