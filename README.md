# nsgtree
_v0.4.0 February 4 2023_

## Why use NSGTree (over SGTree)
New Simple Genome Tree (NSGTree) is a computational pipeline for fast and easy construction of phylogenetic trees from a set of user provided genomes and a set of phylogenetic markers. NSGTree builds a species tree based on a concatenated alignment of all proteins that were identified with the provided  HMMs. NSGTree also builds single protein trees for every marker protein that was found. It is a highly simplified version of SGTree. In contrast to SGTree, NSGTree does currently not support marker selection. Initial benchmarking showed that NSGTree is faster than SGTree (~20-50% depending on number of query faa and HMMs)

## How to run it
### Workflow
* Snakemake in a conda environment
* Input is a dir with faa files and a single file that contains a set of HMMs to identify makers
```
snakemake -j 24 --use-conda --config qfaadir="example" models="resources/models/rnapol.hmm" --configfile user_config.yml
```
```
snakemake -j <number of processes> --use-conda --config qfaadir="<dir with query faa>" models="<single file that contains all marker HMMs" --configfile <settings specified in user_config.yml>
```
* Alternatively, inputs can be a dir with query faa files and a dir with reference faa files, output dir will be created in the dir with query faa files
```
snakemake -j 24 --use-conda --config rfaadir="example_r"  qfaadir="example_q" models="resources/models/rnapol.hmm" --configfile user_config.yml
```
* Setting for alignment, trimming and tree building can be changed in user_config.yml
* Several sets of marker HMMs are provided in subdir resources/models/
* Results can be found in a subdir in <query faa dir\>/nsgt_<analysis name\>"

### Docker / Shifter
* Shifter on NERSC Perlmutter or Cori
```
shifterimg pull fschulzjgi/nsgtree:0.4.0
```
* Load the working directory that contains files with models, querydir and config file with shifter
```
shifter \
  --volume=$(pwd):/nsgtree/example \
  --image=fschulzjgi/nsgtree:0.4.0 \
  bash -c \
  "snakemake --snakefile /nsgtree/workflow/Snakefile \
  -j 24 \
  --use-conda \
  --config \
  qfaadir="/nsgtree/example/test" \
  models="/nsgtree/example/rnapol.hmm" \
  --conda-prefix /nsgtree/.snakemake/conda \
  --configfile /nsgtree/example/user_config.yml"
```
* Specify ref dir and query dir and config file with shifter, using the UNI56 models provided by nsgtree
```
qfaa=$1
rfaa=$2
configf=$3
shifter \
  --volume=$(pwd):/nsgtree/example \
  --image=fschulzjgi/nsgtree:0.4.0 \
  bash -c \
  "snakemake --snakefile /nsgtree/workflow/Snakefile \
  -j 24 \
  --use-conda \
  --config \
  qfaadir="/nsgtree/example/$qfaa" \
  rfaadir="/nsgtree/example/$rfaa" \
  models="/nsgtree/resources/models/UNI56.hmm" \
  --conda-prefix /nsgtree/.snakemake/conda \
  --configfile /nsgtree/example/$configf"
```
* For docker paths to modeldir, querydir, configfile can be loaded separately with the -v flag
```
docker pull fschulzjgi/nsgtree:0.4.0
docker run -t -i -v $(pwd):/nsgtree/modelsdir -v $(pwd)/test:/nsgtree/querydir --user $(id -u):$(id -g) fschulzjgi/nsgtree:0.4.0 snakemake --use-conda -j 16 --config qfaadir="querydir" models="/nsgtree/modelsdir/COX123.hmm"
```

## Acknowledgements
NSGTree was developed by the [New Lineages of Life Group](https://jgi.doe.gov/our-science/scientists-jgi/new-lineages-of-life/) at the DOE Joint Genome Institute supported by the Office of Science of the U.S. Department of Energy under contract no. DE-AC02-05CH11231.
