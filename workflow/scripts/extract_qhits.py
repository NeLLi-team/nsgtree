import sys
from multiprocessing import Pool
import multiprocessing as mp
from itertools import repeat
from Bio import SeqIO

# fschulz@lbl.gov, Jan 2019
# usage: python extract-hmmhits_MP.py <hmmout> <dir with faa files used in hmmsearch> <threads> <name of outfile> <model>
# usage: python extract-hmmhits_MP.py allgenomes_rnapol.out allgenomes_faa 24 allgenomes_rnapol.faa COG0086

hmmout = sys.argv[1]
faadir = sys.argv[2]
threads= int(sys.argv[3])
blacklist = sys.argv[4]
outfaa = sys.argv[5] #  contains modelname

def export_hitsfaa(hit, faadir):
    hitgenomeid = hit.split("|")[0]
    for seq_record in SeqIO.parse(faadir + "/" + hitgenomeid + ".faa", "fasta"):
        if seq_record.description == hit:
            return (seq_record.description, seq_record.seq)


def get_hits(hmmout, model, removedtaxa):
    hitslist = []
    with open(hmmout, "r") as infile:
        for line in infile:
            if not line.startswith("#") and line.split()[0] not in hitslist and line.split()[3] == model and line.split("|")[0]:
                if line.split("|")[0] not in removedtaxa:
                    hitslist.append(line.split()[0])
    return hitslist


def get_removedtaxa(blacklist):
    rtaxa = [line.split()[0] for line in open(blacklist, "r")]
    return rtaxa

def get_taxa (queryfaadir):
    taxa = [taxon.split("/")[-1].split(".")[0] for taxon in glob.glob(queryfaadir + "/*.faa")]
    return taxa


def main():
    removedtaxa = get_removedtaxa(blacklist)
    model = outfaa.split("/")[-1].split(".faa")[0]
    hitslist = get_hits(hmmout, model, removedtaxa)
    with Pool() as pool:
        pool = mp.Pool(processes=threads)
        # repeat for arguments that dont change, without repeat for iterables=list
        res = pool.starmap(export_hitsfaa, zip(hitslist, repeat(faadir)))
    with open(outfaa, "w") as outfile:
        for hit in res:
            outfile.write(">" + hit[0] + "\n" + str(hit[1]) + "\n")


if __name__ == '__main__':
    main()
