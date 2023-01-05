from Bio import SeqIO
from collections import defaultdict
import glob
import pandas as pd
import sys
import subprocess

alndir = sys.argv[1] # dir with aligned multifa
aln_concat = sys.argv[2] # name of concat aln

def get_aln(aln, taxa, final_dict):
    # get aln_len in case there is no seq or a given taxon
    for seq_record in SeqIO.parse(aln, "fasta"):
        aln_len = len(seq_record.seq)
        break
    for taxon in taxa:
        seq = "?" * aln_len
        for seq_record in SeqIO.parse(aln, "fasta"):
            # if aln exist for taxon use the actual seq
            if taxon == seq_record.id.split("|")[0]:
                seq = str(seq_record.seq)
        final_dict[taxon].append(seq)
    return final_dict


def get_taxa(alndir):
    taxa = []
    for aln in glob.glob(alndir + "/*.*"):
        for seq_record in SeqIO.parse(aln, "fasta"):
            if seq_record.id.split("|")[0] not in taxa:
                taxa.append(seq_record.id.split("|")[0])
    return taxa


final_dict = defaultdict(list)
# iterate over dir with aligned multifa
for aln in glob.glob(alndir + "/*"):
    try:
        final_dict = (get_aln(aln, get_taxa(alndir), final_dict))
    except:
        if aln.split(".")[-1] not in ["faa", "fa", "fasta", "fna", "mafft", "mafft01", "aln", "afa"]:
            print ("Check content of dir, all need to be aligned multifasta with typical suffix: fna, fasta, fa, faa...")
        else:
            print ("Something else is wrong")


# create concatenated aln
concat_dict = {x:"".join(y) for x,y in final_dict.items()}
with open(aln_concat, "w") as outfile:
    for seqid, seq in concat_dict.items():
        outfile.write(">" + seqid + "\n" + seq + "\n")

