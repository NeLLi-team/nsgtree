# NSGTree - New Simple Genome Tree

_v0.5.1 August 2025_

NSGTree is a computational pipeline for fast and easy construction of phylogenetic trees from a set of user-provided genomes and phylogenetic markers. It builds species trees based on concatenated alignments of proteins identified with HMM markers, and also constructs individual protein trees for each marker.

This version uses **Pixi** for simplified installation and dependency management, with a modern **Typer-based CLI** that makes it extremely easy to use for the scientific community.

## Why NSGTree?

- **Fast**: 20-50% faster than SGTree depending on dataset size
- **Simple**: Modern CLI with comprehensive help and examples
- **Reliable**: Pure Python implementation with comprehensive error handling
- **Safe**: Timestamped output directories prevent accidental overwrites
- **Flexible**: Supports various tree-building methods (FastTree, IQ-TREE)
- **User-Friendly**: Rich terminal interface with progress bars and beautiful output
- **HPC-Ready**: Runs automatically without prompts by default, with optional interactive mode

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

That's it! All dependencies (MAFFT, trimAl, FastTree, IQ-TREE, HMMER, ete3, etc.) are automatically installed.

## Usage

### Getting Started

NSGTree provides a comprehensive CLI with built-in help and examples:

```bash
# Show available commands
pixi run python nsgtree_main.py --help

# Show example usage patterns
pixi run python nsgtree_main.py examples

# List available HMM models
pixi run python nsgtree_main.py models --list

# Check your system and input files
pixi run python nsgtree_main.py check example resources/models/rnapol.hmm
```

### Basic Analysis

```bash
# Run with query genomes only
pixi run python nsgtree_main.py run example resources/models/rnapol.hmm

# Run with query and reference genomes for comparative analysis
pixi run python nsgtree_main.py run example_q resources/models/UNI56.hmm -r example_r

# Use more CPU cores for faster processing
pixi run python nsgtree_main.py run example resources/models/rnapol.hmm -j 16
```

### Advanced Options

```bash
# Custom output directory (default: ./nsgt_out/ with timestamp)
pixi run python nsgtree_main.py run example resources/models/rnapol.hmm -o my_analysis

# Use IQ-TREE instead of FastTree for more accurate trees
pixi run python nsgtree_main.py run example resources/models/UNI56.hmm -t iqtree

# Custom configuration file
pixi run python nsgtree_main.py run example resources/models/rnapol.hmm -c user_config.yml

# Enable verbose logging to see detailed progress
pixi run python nsgtree_main.py run example resources/models/rnapol.hmm -v

# Dry run to see what would be done without executing
pixi run python nsgtree_main.py run example resources/models/rnapol.hmm --dry-run

# Interactive mode with confirmation prompts (useful for manual analysis)
pixi run python nsgtree_main.py run example resources/models/rnapol.hmm --interactive
```

### Command Reference

**Main Commands:**
- `run`: Execute complete phylogenetic analysis
- `models`: Manage and list HMM model files
- `examples`: Show usage examples and scenarios
- `check`: Validate input files and system requirements

**Run Command Options:**
- `qfaadir`: Directory containing query FAA files (required)
- `models`: Path to HMM models file (required)
- `-r, --rfaadir`: Directory containing reference FAA files (optional)
- `-o, --output-name`: Custom output directory name (optional)
- `-c, --config`: User configuration file in YAML format (optional)
- `-j, --cores`: Number of CPU cores to use (default: 8)
- `-t, --tree-method`: Tree building method: 'fasttree' or 'iqtree' (optional)
- `-m, --min-marker`: Minimum fraction of markers required per genome (optional)
- `-i, --interactive`: Enable interactive mode with confirmation prompts (optional)
- `-v, --verbose`: Enable verbose logging
- `--dry-run`: Show what would be done without executing

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

Results are saved to timestamped directories in `./nsgt_out/` (or custom directory with `-o`):

```
./nsgt_out/example--rnapol-fasttree-perc1_20250801_152613/
```

**Key Output Files:**
- `<analysis_name>.treefile`: Final species tree (Newick format)
- `<analysis_name>.mafft_t`: Concatenated alignment
- `proteintrees/`: Individual protein trees for each marker
- `itol/`: Tree visualization files for ITOL (Interactive Tree of Life)
  - `query_genomes.txt`: List of query genomes
  - `*_clades.itol`: ITOL annotation file for highlighting query clades
  - `*_neighbors.pairs`: Nearest neighbor relationships (when references provided)
  - `*_analysis_summary.txt`: Summary of analysis and visualization files
- `analyses.tar.gz`: Compressed intermediate results
- `workflow.log`: Analysis log

**Safety Features:**
- **Timestamped directories**: Each run gets a unique directory with `YYYYMMDD_HHMMSS` timestamp
- **No overwrites**: Multiple analyses never conflict or overwrite each other
- **Organized output**: All results clearly separated by timestamp

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

# Show help and available commands
pixi run python nsgtree_main.py --help

# Run example analysis
pixi run python nsgtree_main.py run example resources/models/rnapol.hmm
```

This analyzes 12 example genomes using RNA polymerase markers and completes in about 5 minutes, producing a species tree in `./nsgt_out/example--rnapol-fasttree-perc1_YYYYMMDD_HHMMSS/`.

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

### Modern CLI Interface
- **Comprehensive Help System**: Built-in examples, model management, and system checking
- **Rich Terminal Interface**: Beautiful progress bars, tables, and colored output
- **Interactive Confirmations**: Safe execution with confirmation prompts
- **Command Validation**: Built-in checks for input files and system requirements

### Enhanced Safety & Usability
- **Timestamped Output Directories**: Each analysis gets a unique directory (no more overwrites!)
- **Current Directory Output**: Results saved to `./nsgt_out/` by default (much more intuitive)
- **Custom Output Names**: Use `-o` to specify custom output directory names
- **Dry Run Mode**: See what will be done before executing with `--dry-run`

### Improved Phylogenetic Analysis
- **Enhanced ete3 Integration**: Full tree visualization and analysis capabilities
- **Working Nearest Neighbor Analysis**: Find closest relatives for query genomes
- **Comprehensive Tree Analysis**: Automatic clade detection and ITOL annotation generation
- **Robust Error Handling**: Better error messages and recovery from failures

### Technical Improvements
- **Simplified Installation**: Single `pixi install` command handles all dependencies
- **Cross-Platform Support**: Works on Linux, macOS, and Windows (with WSL)
- **Better Dependency Management**: Automatic handling of bioinformatics tools
- **Performance Optimizations**: Faster execution and better resource usage

### For Scientists
- **Example-Driven Documentation**: Learn by example with built-in usage patterns
- **Model Management**: Easy listing and selection of HMM models
- **System Validation**: Check your setup before running analyses
- **Visualization Ready**: Automatic generation of publication-ready tree files

## Acknowledgements

NSGTree was developed by the [New Lineages of Life Group](https://jgi.doe.gov/our-science/scientists-jgi/new-lineages-of-life/) at the DOE Joint Genome Institute, supported by the Office of Science of the U.S. Department of Energy under contract no. DE-AC02-05CH11231.
