# NSGTree with Pixi

This document describes the pixi-based version of NSGTree, which simplifies installation and usage compared to the original Snakemake version.

## Installation

1. Install pixi (if not already installed):
```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

2. Clone and setup NSGTree:
```bash
git clone <repository>
cd nsgtree
pixi install
```

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

### Configuration

The pipeline uses the `user_config.yml` file for configuration. Key parameters include:

- `tmethod`: Tree building method ("fasttree" or "iqtree")
- `minmarker`: Minimum fraction of markers required per genome
- `maxsdup`: Maximum single-copy duplicates allowed
- `maxdupl`: Maximum duplicates allowed

## Output

Results are saved to `<qfaadir>/nsgt_out/<analysis_name>/`:
- `<analysis_name>.treefile`: Final species tree
- `<analysis_name>.mafft_t`: Concatenated alignment
- `analyses/`: Intermediate analysis files
- `analyses.tar.gz`: Compressed results

## Differences from Snakemake Version

1. **Simplified Installation**: No need to manage conda environments manually
2. **Single Command**: Run entire pipeline with one command
3. **Automatic Dependencies**: All required tools installed automatically via pixi
4. **Better Error Handling**: More informative error messages and logging
5. **No Snakemake Required**: Pure Python implementation

## Troubleshooting

1. **Empty tree files**: Check that input genomes pass filtering thresholds
2. **MAFFT errors**: Ensure sequences are in proper FASTA format
3. **Memory issues**: Reduce the number of cores with `--cores` parameter

## Performance Notes

- FastTree is used by default for speed
- Use IQ-TREE for more accurate phylogenies (set `tmethod: iqtree` in config)
- Processing time scales with number of genomes and HMM models

## Example Run

```bash
cd nsgtree
pixi run nsgtree --qfaadir example --models resources/models/rnapol.hmm --config user_config.yml
```

This produces a species tree from 12 example genomes using RNA polymerase HMMs, completing in about 5 minutes.
