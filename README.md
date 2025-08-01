# NSGTree - New Simple Genome Tree

_v0.5 March 2024_

NSGTree is a computational pipeline for fast and easy construction of phylogenetic trees from a set of user-provided genomes and phylogenetic markers. It builds species trees based on concatenated alignments of proteins identified with HMM markers, and also constructs individual protein trees for each marker.

This version uses **Pixi** for simplified installation and dependency management, making it much easier to use than previous versions.

## Why NSGTree?

- **Fast**: 20-50% faster than SGTree depending on dataset size
- **Simple**: Single command execution with automatic dependency management
- **Reliable**: Pure Python implementation with comprehensive error handling
- **Flexible**: Supports various tree-building methods (FastTree, IQ-TREE)

## Installation

### Prerequisites
First install Pixi (modern conda-compatible package manager):
```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

### Install NSGTree
```bash
git clone https://github.com/NeLLi-team/nsgtree.git
cd nsgtree
pixi install
```

That's it! All dependencies (MAFFT, trimAl, FastTree, IQ-TREE, HMMER, etc.) are automatically installed.

## Usage

### Basic Usage
```bash
# Run with query genomes only
pixi run nsgtree --qfaadir example --models resources/models/rnapol.hmm

# Run with custom configuration
pixi run nsgtree --qfaadir example --models resources/models/rnapol.hmm --config user_config.yml

# Run with query and reference genomes
pixi run nsgtree --qfaadir example_q --rfaadir example_r --models resources/models/UNI56.hmm
```

### Command Line Options
- `--qfaadir`: Directory containing query FAA files (required)
- `--models`: Path to HMM models file (required)
- `--rfaadir`: Directory containing reference FAA files (optional)
- `--config`: User configuration file in YAML format (optional)
- `--cores`: Number of CPU cores to use (default: 8)
- `--verbose`: Enable verbose logging

### Example Datasets
The repository includes example datasets:
- `example/`: 12 genome FAA files for testing
- `example_q/`: Query genomes
- `example_r/`: Reference genomes

### Available Models
Pre-built HMM models are provided in `resources/models/`:
- `rnapol.hmm`: RNA polymerase markers (3 proteins)
- `UNI56.hmm`: Universal single-copy markers (56 proteins)
- `gtdbbac.hmm`: GTDB bacterial markers
- `gtdbarc.hmm`: GTDB archaeal markers
- And more...

## Configuration

Customize analysis parameters in `user_config.yml`:

```yaml
# Tree building method
tmethod: "fasttree"  # or "iqtree"

# Filtering thresholds
minmarker: "0.1"     # Minimum fraction of markers required per genome
maxsdup: "1.5"       # Maximum single-copy duplicates allowed
maxdupl: "3.0"       # Maximum duplicates allowed

# Tool-specific parameters
trimal_gt: "-gt 0.5"
ft_speciestree: "-spr 4 -mlacc 3 -slownni -lg"
iq_speciestree: "LG+F+R10"
```

## Output

Results are saved to `<qfaadir>/nsgt_out/<analysis_name>/`:
- `<analysis_name>.treefile`: Final species tree (Newick format)
- `<analysis_name>.mafft_t`: Concatenated alignment
- `proteintrees/`: Individual protein trees for each marker
- `itol/`: Tree visualization files for ITOL (Interactive Tree of Life)
  - `query_genomes.txt`: List of query genomes
  - `*_clades.itol`: ITOL annotation file for highlighting query clades
  - `*_neighbors.pairs`: Nearest neighbor relationships (when available)
  - `*_analysis_summary.txt`: Summary of analysis and visualization files
- `analyses.tar.gz`: Compressed intermediate results
- `workflow.log`: Analysis log

## Performance Notes

- **FastTree** (default): Fast approximate ML trees, good for large datasets
- **IQ-TREE**: More accurate ML trees with model selection, slower
- Processing time scales with number of genomes and HMM models
- Memory usage is generally modest (<8GB for typical datasets)

## Troubleshooting

1. **Empty tree files**: Check filtering thresholds - increase `minmarker` or decrease `maxsdup`/`maxdupl`
2. **MAFFT errors**: Ensure sequences are properly formatted FASTA files
3. **Memory issues**: Reduce `--cores` parameter
4. **No hits found**: Check that your genomes contain the expected proteins for your HMM models

## Quick Start Example

```bash
cd nsgtree
pixi run nsgtree --qfaadir example --models resources/models/rnapol.hmm
```

This analyzes 12 example genomes using RNA polymerase markers and completes in about 5 minutes, producing a species tree in `example/nsgt_out/example--rnapol-fasttree-perc1/`.

## Tree Visualization

NSGTree automatically generates visualization files for use with ITOL (Interactive Tree of Life):

1. **Upload your tree**: Go to https://itol.embl.de/ and upload your `.treefile`
2. **Add annotations**: Use the generated `.itol` files to highlight query clades in different colors
3. **Analyze relationships**: Check the `.pairs` files for nearest neighbor relationships
4. **Customize visualization**: Use ITOL's web interface for additional styling and analysis

The visualization files help you:
- **Identify monophyletic groups**: See which query genomes cluster together
- **Highlight query taxa**: Distinguish your genomes from references in the tree
- **Find closest relatives**: Understand phylogenetic relationships between queries and references

## What's New in the Pixi Version

- **Simplified Installation**: No conda environment management needed
- **Single Command**: Replace complex Snakemake commands with simple CLI
- **Better Error Handling**: Clear error messages and logging
- **Faster Setup**: All dependencies automatically managed
- **Cross-platform**: Works on Linux, macOS, and Windows (with WSL)
- **Tree Visualization**: Automatic generation of ITOL annotation files for phylogenetic visualization
- **Clade Analysis**: Identification and highlighting of monophyletic query clades
- **Nearest Neighbor Analysis**: Find closest phylogenetic relatives for query genomes

## Acknowledgements

NSGTree was developed by the [New Lineages of Life Group](https://jgi.doe.gov/our-science/scientists-jgi/new-lineages-of-life/) at the DOE Joint Genome Institute, supported by the Office of Science of the U.S. Department of Energy under contract no. DE-AC02-05CH11231.
