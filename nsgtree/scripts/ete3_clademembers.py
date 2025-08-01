import sys
from ete3 import Tree
import ete3 as ete
import os.path
import warnings
warnings.filterwarnings("ignore", ".*is with a literal.*", SyntaxWarning)

treein = sys.argv[1] # tree in newick format
queryids_or_pattern = sys.argv[2] # file with leaf names or pattern to look for leaves
hexcolor =  sys.argv[3] # color for identified branches
itolout = sys.argv[4] # name of outfile

def get_alltaxa(t, queryids_or_pattern):
    target = []
    if os.path.isfile(queryids_or_pattern):
        with open(queryids_or_pattern, "r") as infile:
            target = [line.strip() for line in infile]
    else:
        for node in t.traverse():
            if node.is_leaf() and node.name.startswith(queryids_or_pattern):
                target.append(node.name)
    return target


def unpack_family(parentnode, leaves, target):
    """
    get all leaves under a parental node
    """
    children = parentnode.get_children()
    for child in children:
        if child.is_leaf() and child.name not in leaves:
            leaves.append(child.name)
        else:
            unpack_family(child, leaves, target) 
    return leaves


def check_monophyly(node, target, mono_leaves):
    # move up one node in the tree
    parentnode = node.up
    # collect all terminal leaves under the parent node
    leaves = unpack_family(parentnode, [], target)
    if len(leaves) == len([x for x in leaves if x in target]):
        mono_leaves.extend(leaves)
        check_monophyly(parentnode, target, mono_leaves)
    return mono_leaves

def main():
    t = Tree(treein)
    target = get_alltaxa(t, queryids_or_pattern)
    mono_leaves_all = []
    for node in t.traverse():
        if node.name in target and node.name not in [x for sublist in mono_leaves_all for x in sublist]:
            try:
                mono_leaves_all.append(check_monophyly(node, target, []))
            except:
                mono_leaves_all.append([node.name])
    #write to output
    queriesinclades = [x for sublist in mono_leaves_all for x in sublist]
    singletons = [x for x in target if x not in queriesinclades]
    with open(itolout, "w") as outfile:
        for monotclade in mono_leaves_all:
            if len(monotclade) > 1:
                outfile.write("|".join(list(set(monotclade))) + ",clade,#"+hexcolor+",normal,2\n")
        for singleton in singletons:
            outfile.write(singleton + ",branch,#"+hexcolor+",normal,2\n")

if __name__ == '__main__':
    main()
