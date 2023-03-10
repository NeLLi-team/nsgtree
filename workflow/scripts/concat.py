import glob
import sys
from Bio import SeqIO
from collections import defaultdict

alndir = sys.argv[1] # dir with aligned multifa
aln_concat = sys.argv[2] # name of concat aln

def get_aln_len(aln):
    for seq_record in SeqIO.parse(aln, "fasta"):
        return len(seq_record.seq)

def get_taxa(alndir):
    taxa = set()
    for aln in glob.glob(alndir + "/*.*"):
        for seq_record in SeqIO.parse(aln, "fasta"):
            taxa.add(seq_record.id.split("|")[0])
    return list(taxa)

def get_aln(aln, taxa, final_dict, aln_len):
    for taxon in taxa:
        seq = "?" * aln_len
        for seq_record in SeqIO.parse(aln, "fasta"):
            if taxon == seq_record.id.split("|")[0]:
                seq = str(seq_record.seq)
                break
        final_dict[taxon].append(seq)
    return final_dict

final_dict = defaultdict(list)
for aln in glob.glob(alndir + "/*"):
    try:
        aln_len = get_aln_len(aln)
        final_dict = get_aln(aln, get_taxa(alndir), final_dict, aln_len)
    except:
        if aln.split(".")[-1] not in ["faa", "fa", "fasta", "fna", "mafft", "mafft01", "aln", "afa"]:
            print("Check content of dir, all need to be aligned multifasta with typical suffix: fna, fasta, fa, faa...")
        else:
            print("Something else is wrong")

# create concatenated aln
concat_dict = {x:"".join(y) for x,y in final_dict.items()}
with open(aln_concat, "w") as outfile:
    for seqid, seq in concat_dict.items():
        outfile.write(">" + seqid + "\n" + seq + "\n")
