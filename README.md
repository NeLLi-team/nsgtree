# nsgtree

Version: _0.4.2 August 18 2023_

## Why use NSGTree (over SGTree)

New Simple Genome Tree (NSGTree) is a computational pipeline for fast and easy construction of phylogenetic trees from a set of user provided genomes and a set of phylogenetic markers. NSGTree builds a species tree based on a concatenated alignment of all proteins that were identified with the provided markers HMMs. NSGTree also builds single protein trees for every marker protein that was found. It is a highly simplified version of SGTree. In contrast to SGTree, NSGTree does currently not support marker selection. Initial benchmarking showed that NSGTree is faster than SGTree (~20-50% depending on number of query faa and HMMs)

## How to run it

Clone the repository:

```bash
git clone https://github.com/NeLLi-team/nsgtree.git
cd nsgtree
```

Create a Snakemake conda (mamba) environment:

```bash
mamba create -n snakemake snakemake
```

Activate the Snakemake environment:

```bash
mamba activate snakemake
```

Run test 1 (make sure you are inside the `nsgtree` folder):

```bash
snakemake -j 8 --use-conda --config qfaadir="example" models="resources/models/rnapol.hmm" --configfile user_config.yml
```

In general, this are the required arguments to run `nsgtree`:

```bash
snakemake \
  -j <number of processes> \
  --use-conda \
  --config \
  qfaadir="<dir with query faa>" \
  models="<single file that contains all marker HMMs" \
  --configfile <settings specified in user_config.yml>
```

* Alternatively, inputs can be a dir with query faa files and a dir with reference faa files, output dir will be created in the dir with query faa files

```bash
snakemake \
  -j 24 \
  --use-conda \
  --config \
  rfaadir="example_r"  \
  qfaadir="example_q" \
  models="resources/models/rnapol.hmm" \
  --configfile user_config.yml
```

## Notes

* Setting for alignment, trimming and tree building can be changed in user_config.yml
* Several sets of marker HMMs are provided in subdir resources/models/
* Results can be found in a subdir in <query faa dir\>/nsgt_<analysis name\>"

### Docker

* For docker paths to modeldir, querydir, configfile can be loaded separately with the -v flag

```bash
docker pull fschulzjgi/nsgtree:0.4.1
docker run -t -i -v $(pwd):/nsgtree/modelsdir -v $(pwd)/test:/nsgtree/querydir --user $(id -u):$(id -g) fschulzjgi/nsgtree:0.4.1 snakemake --use-conda -j 16 --config qfaadir="querydir" models="/nsgtree/modelsdir/rnapol.hmm"
```

## Acknowledgements

NSGTree was developed by the [New Lineages of Life Group](https://jgi.doe.gov/our-science/scientists-jgi/new-lineages-of-life/) at the DOE Joint Genome Institute supported by the Office of Science of the U.S. Department of Energy under contract no. DE-AC02-05CH11231.
