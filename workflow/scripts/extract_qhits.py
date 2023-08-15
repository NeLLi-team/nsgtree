import os
from itertools import repeat
import sys
import glob
import multiprocessing as mp
from Bio import SeqIO

hmmout = sys.argv[1]
faadir = sys.argv[2]
threads = int(sys.argv[3])
blacklist = sys.argv[4]
outfaa = sys.argv[5] # contains the model name

def export_hits_faa(hit, faadir):
    hit_genome_id = hit.split("|")[0]
    faa_file = os.path.join(faadir, hit_genome_id + ".faa")
    for seq_record in SeqIO.parse(faa_file, "fasta"):
        if seq_record.description == hit:
            return (seq_record.description, seq_record.seq)

def get_hits(hmmout, model, removed_taxa):
    hits_list = []
    with open(hmmout, "r") as infile:
        for line in infile:
            if not line.startswith("#") and line.split()[0] not in hits_list and line.split()[3] == model and line.split("|")[0]:
                if line.split("|")[0] not in removed_taxa:
                    hits_list.append(line.split()[0])
    return hits_list

def get_removed_taxa(blacklist):
    removed_taxa = [line.split()[0] for line in open(blacklist, "r")]
    return removed_taxa

def main():
    removed_taxa = get_removed_taxa(blacklist)
    model = outfaa.split("/")[-1].split(".faa")[0]
    hits_list = get_hits(hmmout, model, removed_taxa)

    with mp.Pool(processes=threads) as pool:
        results = pool.starmap(export_hits_faa, zip(hits_list, repeat(faadir)))

    with open(outfaa, "w") as outfile:
        for hit in results:
            outfile.write(">" + hit[0] + "\n" + str(hit[1]) + "\n")

if __name__ == '__main__':
    main()
