import glob
import sys
from ete3 import Tree
from collections import defaultdict
from collections import Counter
import pandas as pd
import warnings
warnings.filterwarnings("ignore", ".*is with a literal.*", SyntaxWarning)

def main(args=None):
    """Main function that can be called with arguments or use sys.argv"""
    if args is None:
        args = sys.argv[1:]

    tree_in = args[0]
    queries_in = args[1]
    outname = args[2]

    def unpack_family(node, leaves, query, seen, queries):
        """
        get all leaves under a parental node
        """
        if node is None or node.up is None:
            return leaves

        parent = node.up
        children = parent.get_children()
        for child in children:
            if child.is_leaf():
                childname = str(child.name).replace("--","").replace("/-", "").replace("\\-", "").replace("\\n","")
                if childname not in queries and childname not in seen:
                    seen.append(childname)
                    leaves.append(childname)
                elif childname == query:
                    seen.append(childname)
            elif not child.is_leaf() and str(child) not in seen:
                seen.append(str(child))
                # Recursively get leaves from subtree
                for leaf in child.get_leaves():
                    leafname = str(leaf.name).replace("--","").replace("/-", "").replace("\\-", "").replace("\\n","")
                    if leafname not in queries and leafname not in leaves:
                        leaves.append(leafname)

        # If still no leaves found, go up one more level
        if len(leaves) == 0 and parent.up is not None:
            return unpack_family(parent, leaves, query, seen, queries)
        return leaves


    def get_closestrelative(query, leaves, node, tree):
        distance = float('inf')
        closestrelative = "nd"
        query_node = None

        # Find the query node in the tree
        for n in tree.traverse():
            if n.name == query:
                query_node = n
                break

        if query_node is None:
            return closestrelative, distance

        for leaf_name in leaves:
            if leaf_name != query:
                # Find the leaf node
                leaf_node = None
                for n in tree.traverse():
                    if n.name == leaf_name:
                        leaf_node = n
                        break

                if leaf_node is not None:
                    try:
                        newdist = tree.get_distance(leaf_node, query_node, topology_only=False)
                        if newdist < distance:
                            distance = newdist
                            closestrelative = leaf_name
                    except:
                        # If distance calculation fails, try topology-only
                        try:
                            newdist = tree.get_distance(leaf_node, query_node, topology_only=True)
                            if newdist < distance:
                                distance = newdist
                                closestrelative = leaf_name
                        except:
                            continue

        return closestrelative, distance if distance != float('inf') else 0


    def get_neighbor(tree, query, queries):
        query_node = None
        for node in tree.traverse():
            if node.name == query:
                query_node = node
                break

        if query_node is None:
            return ["nd", "nd"]

        # collect all terminal leaves under the parent node
        leaves = []
        seen = []
        leaves = unpack_family(query_node, leaves, query, seen, queries)

        if not leaves:
            # If no leaves found, get all leaves from the tree except queries
            for leaf in tree.get_leaves():
                if leaf.name not in queries:
                    leaves.append(leaf.name)

        closestrelative, distance = get_closestrelative(query, leaves, query_node, tree)
        return [closestrelative, distance]

    try:
        # get queries
        with open(queries_in) as infile:
            queries = infile.read().splitlines()

        # all distances
        tree_dict_all = {}
        tree = Tree(tree_in)

        for query in queries:
            tree_dict_all[query] = get_neighbor(tree, query, queries)

        # Write results
        with open(outname + ".pairs", "w") as outfile:
            outfile.write("Query\tClosest_Relative\tDistance\n")  # Header
            for query, bestref in tree_dict_all.items():
                if bestref and bestref[0] != "nd":
                    outfile.write(f"{query}\t{bestref[0]}\t{bestref[1]}\n")
                else:
                    outfile.write(f"{query}\tnd\tnd\n")

    except Exception as e:
        print(f"Error in nearest neighbor analysis: {e}")
        # Create empty file so workflow continues
        with open(outname + ".pairs", "w") as outfile:
            outfile.write("Query\tClosest_Relative\tDistance\n")
            outfile.write("# Analysis failed - check tree file and query names\n")


if __name__ == "__main__":
    main()
