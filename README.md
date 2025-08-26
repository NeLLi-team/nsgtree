# NSGTree - New Simple Genome Tree

Build phylogenetic trees from your genomes in just one command!

NSGTree takes a folder of genome files (.faa format) and builds a phylogenetic tree showing how they're related. It's designed to be simple to use while producing publication-quality results.

## What NSGTree Does

1. **Finds marker proteins** in your genomes using HMM models
2. **Aligns sequences** of the same proteins across genomes
3. **Builds phylogenetic trees** showing evolutionary relationships
4. **Creates visualizations** ready for publication

Perfect for comparative genomics, phylogenetic placement, and understanding evolutionary relationships!

## Key Features

- ✅ **One-command analysis** - Just point it at your genome files
- ✅ **Fast** - Builds trees 20-50% faster than similar tools
- ✅ **Easy to install** - All dependencies installed automatically
- ✅ **Safe** - Each run gets its own timestamped folder
- ✅ **Visualization ready** - Outputs work directly with tree viewers

## Installation

### Step 1: Install Pixi

First install Pixi (a modern package manager):

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

### Step 2: Install NSGTree

```bash
git clone https://github.com/NeLLi-team/nsgtree.git
cd nsgtree
pixi install
```

### Step 3: Choose Your Preferred Command Style

After installation, you have several ways to run NSGTree:

**Option A: Use the simple wrapper script (recommended)**
```bash
./nsgt --help                                      # Show help
./nsgt run my_genomes resources/models/rnapol.hmm  # Run analysis
```

**Option B: Use pixi shortcuts**
```bash
pixi run help                                      # Show help
pixi run run my_genomes resources/models/rnapol.hmm  # Run analysis
pixi run test-rnapol                               # Quick test
```

**Option C: Install as a command-line tool**
```bash
./install.sh    # Run this once
nsgtree --help  # Then use 'nsgtree' directly
```

## Quick Start

### Basic Usage

Build a tree from your genome files in one command:

```bash
# Basic analysis - put your .faa files in a folder called "my_genomes"
./nsgt run my_genomes resources/models/rnapol.hmm

# Use more CPU cores (faster)
./nsgt run my_genomes resources/models/rnapol.hmm -j 16
```

### Try the Examples

Test with included example data:

```bash
# Test with small RNA polymerase markers (fast, ~2 minutes)
./nsgt run example resources/models/rnapol.hmm

# Test with comprehensive protein markers (more accurate, ~10 minutes)
./nsgt run example resources/models/UNI56.hmm

# Or use the pre-built shortcuts:
pixi run test-rnapol
pixi run test-uni56
```

### What You Need

1. **Genome files**: Put your protein FASTA files (.faa) in a folder
2. **Choose markers**: Pick from pre-built marker sets (see below)

That's it!

## Available Marker Sets

NSGTree includes several pre-built marker sets for different purposes:

- **`rnapol.hmm`**: RNA polymerase (3 proteins) - Fast, good for initial analysis
- **`UNI56.hmm`**: Universal markers (56 proteins) - Most comprehensive
- **`gtdbbac.hmm`**: Bacterial-specific markers
- **`gtdbarc.hmm`**: Archaeal-specific markers

## Understanding Your Results

Results are saved in `./nsgt_out/` with a timestamp:

```
./nsgt_out/my_analysis_20250804_143022/
  ├── my_analysis_20250804_143022.treefile  ← Your phylogenetic tree
  ├── my_analysis_20250804_143022.mafft_t   ← Protein alignment used
  ├── proteintrees/                         ← Individual protein trees
  └── itol/                                 ← Files for tree visualization
```

**Key file**: The `.treefile` contains your phylogenetic tree in standard Newick format.

## Tree Visualization

Upload your `.treefile` to any tree viewer:

- **Online**: [iTOL](https://itol.embl.de) (free, web-based)
- **Desktop**: FigTree, Dendroscope, or similar

The `itol/` folder contains files to color and annotate your tree automatically.

## Common Options

```bash
# Use a different tree-building method (more accurate but slower)
./nsgt run my_genomes resources/models/UNI56.hmm -t iqtree

# Custom output folder name
./nsgt run my_genomes resources/models/rnapol.hmm -o my_analysis

# Verbose output to see what's happening
./nsgt run my_genomes resources/models/rnapol.hmm -v
```

## Getting Help

```bash
# Show all available commands
./nsgt --help

# Show examples
./nsgt examples

# List available marker sets
./nsgt models --list

# Check if your files are formatted correctly
./nsgt check my_genomes resources/models/rnapol.hmm
```
## Troubleshooting

**Problem**: No tree file generated
- **Solution**: Your genomes may not contain the expected proteins. Try a different marker set or check that your .faa files contain protein sequences.

**Problem**: Analysis runs slowly
- **Solution**: Use more CPU cores with `-j 16` (or however many cores you have)

**Problem**: "No .faa files found" error
- **Solution**: Make sure your protein files end with `.faa` and are in FASTA format

**Problem**: Out of memory errors
- **Solution**: Use fewer CPU cores with `-j 4` or analyze fewer genomes at once

## Advanced Usage

### Custom Configuration

For advanced users, create a config file to set custom parameters:

```yaml
# my_config.yml
cores: 32                    # Use all your CPU cores
tmethod: "iqtree"           # Use IQ-TREE for more accurate trees
minmarker: 0.2              # Require at least 20% of markers per genome
```

Then run with:

```bash
./nsgt run my_genomes resources/models/UNI56.hmm -c my_config.yml
```

### All Command Options

```bash
./nsgt run GENOME_FOLDER MARKER_FILE [OPTIONS]

Options:
  -j, --cores INTEGER          Number of CPU cores to use
  -t, --tree-method TEXT       Tree method: 'fasttree' or 'iqtree'
  -m, --min-marker FLOAT       Minimum fraction of markers per genome
  -o, --output-name TEXT       Custom output folder name
  -c, --config TEXT           Configuration file
  -v, --verbose               Show detailed progress
  --dry-run                   Preview what will be done
  -r, --rfaadir TEXT          Reference genomes folder
```

## Acknowledgments

NSGTree was developed by the [New Lineages of Life Group](https://jgi.doe.gov/our-science/scientists-jgi/new-lineages-of-life/) at the DOE Joint Genome Institute.

## Version

NSGTree v0.6.5 - August 2025
