from Bio import SeqIO
import pandas as pd
import sys
import os
import glob

faaindir = sys.argv[1]
faaoutdir = sys.argv[2]

# header in format ><filebasename|<proteinid>

reformatted = []

for faain in glob.glob(faaindir+"/*.faa"):
    faaout = os.path.join(faaoutdir, os.path.basename(faain))
    reformatted = []
    for seq_record in SeqIO.parse(faain, "fasta"):
        querybase = os.path.splitext(os.path.basename(faain))[0]
        if "|" in seq_record.id:
            if seq_record.id.split("|")[0] == querybase:
                seq_record.id = seq_record.id.split()[0]
                seq_record.description = ""
                reformatted.append(seq_record)
            else:
                seq_record.id= querybase + "|" + seq_record.id.split()[0]
                seq_record.description = ""
                reformatted.append(seq_record)
        else:
            seq_record.id= querybase + "|" + seq_record.id.split()[0]
            seq_record.description = ""
            reformatted.append(seq_record)
    SeqIO.write(reformatted, faaout, "fasta")
