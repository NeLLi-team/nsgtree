from scipy.cluster import hierarchy
import numpy as np
import subprocess
import sys
import pandas as pd
import glob
from collections import defaultdict
import os

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

queryfaadir = sys.argv[1]
modelscombined = sys.argv[2] # e.g. pathtofiles + "models/GVOGuni9.hmm"
hmmout = sys.argv[3] # e.g. pathtofiles + "Fadolivirus_GVOGuni9.out"
countout = sys.argv[4] # summarized hit counts per model from hmmout
removedtaxa = sys.argv[5] # list of removed taxa with info on why removed these were removed
minmarker = float(sys.argv[6]) # percentage of markers to be present for a genome to be included in downstream analysis$
maxsdup = int(sys.argv[7]) # max copy number of any marker, if exceeded respective genome will be excluded
maxdupl = float(sys.argv[8]) # percentage of markers that can be present in multiple copies
outitol = sys.argv[9]


def get_models (modelsin):
    """
    Generate list of all model names
    Some models might have no hits in hmmout, but they should be displayed in count matrix
    """
    with open(modelsin, "r") as f:
        models = [line.split()[-1].rstrip() for line in f if line.startswith("NAME")]
    return models


def get_taxa (queryfaadir):
    taxa = [taxon.split("/")[-1].split(".")[0] for taxon in glob.glob(queryfaadir + "/*.faa")]
    return taxa


def get_markercompleteness (models, hmmout, query):
    """
    Get copy numbers for each marker
    """
    # add 0s to include models that are not in hmmout
    count_dict = { x:0 for x in models }
    seen = []
    with open(hmmout, "r") as f:
        lines = [line.rstrip() for line in f if not line.startswith("#")]
        for line in lines:
            if line.split()[0] not in seen and line.split("|")[0]==query:
                count_dict[line.split()[3]] += 1
                seen.append(line.split()[0])
    return count_dict


def filter_taxa(df, models, minmarker, maxsdup, maxdupl):
    """ Quality filtering"""
    filteredtaxa_dict = defaultdict(list)
    df['max'] = df.max(axis=1)
    filtered_taxa = df[df['max'] > maxsdup].index
    filteredtaxa_dict.update({taxon: ["maxsdup:{}".format(df.at[taxon, 'max'])] for taxon in filtered_taxa})
    df.drop(['max'], inplace=True, axis=1)
    df['duplications'] = (df > 1).sum(axis=1)
    filtered_taxa = df[df['duplications'] / len(models) > maxdupl].index
    filteredtaxa_dict.update({taxon: ["maxdupl:{:.4f}".format(df.at[taxon, 'duplications'] / len(models))] for taxon in filtered_taxa})
    df.drop(['duplications'], inplace=True, axis=1)
    df[df > 1] = 1
    df['sum'] = df.sum(axis=1)
    filtered_taxa = df[df['sum'] < len(models) * minmarker].index
    filteredtaxa_dict.update({taxon: ["completeness:{:.4f}".format(df.at[taxon, 'sum'] / len(models))] for taxon in filtered_taxa})
    return filteredtaxa_dict


def reorder_cols(df):
    """Reorder columns in countmatrix using hierarchical clustering"""
    Z = hierarchy.linkage(df.T, method='ward')
    reordered_ind = hierarchy.leaves_list(Z)
    df = df[df.columns[reordered_ind]]
    return df

def convert2itol(flabels, outfile):
    with open(outfile, "w") as outfile:
        outfile.write("DATASET_HEATMAP\n"
                        "SEPARATOR COMMA\n"
                        "DATASET_LABEL,Count\n"
                        "COLOR,#ff0000\n"
                        "COLOR_MIN,#ff0000\n"
                        "COLOR_MAX,#0000ff\n"
                        "FIELD_LABELS," + ",".join(flabels) + "\n"
                        "DATA\n"
                       )

def main():
    models = get_models(modelscombined)
    taxa = get_taxa(queryfaadir)

    count_dict = {query: get_markercompleteness(models, hmmout, query) for query in taxa}
    df = pd.DataFrame.from_dict(count_dict).T
    df.to_csv(countout, sep='\t', index=True)

    filteredtaxa_dict = filter_taxa(df, models, minmarker, maxsdup, maxdupl)
    with open(removedtaxa, 'w') as outfile:
        for taxon, reasons in filteredtaxa_dict.items():
            outfile.write(f'{taxon}\t{";".join(reasons)}\n')

    df.drop('sum', axis=1, inplace=True)
    reordered_df = reorder_cols(df)
    convert2itol(list(df.columns), outitol)
    with open(outitol, "a") as outitolA:
        df.to_csv(outitolA, header = False, sep = ",")

if __name__ == '__main__':
    main()
