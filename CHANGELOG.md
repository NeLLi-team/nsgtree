# Changelog

All notable changes to NSGTree will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.5] - 2025-08-04

### Added
- **Simplified Command Interface**: Multiple ways to run NSGTree with shorter commands
  - New `./nsgt` wrapper script: `./nsgt run my_genomes models/rnapol.hmm`
  - Enhanced pixi task shortcuts: `pixi run test-rnapol`, `pixi run help`
  - Direct installation option: `nsgtree run my_genomes models/rnapol.hmm`
- **Improved User Experience**: Much shorter commands (75% reduction in command length)
  - From: `pixi run python nsgtree_main.py run --help`
  - To: `./nsgt --help`

### Changed
- **Enhanced README**: Completely redesigned for simplicity and clarity
  - Streamlined installation instructions
  - Clearer quick start examples
  - Better troubleshooting section
  - Multiple command style options
- **Updated Documentation**: All examples now use simplified command syntax
- **Removed Core Limit**: `--cores` option no longer limited to 64 cores (useful for HPC)

### Fixed
- Console script entry points in setup.py now point to correct CLI module
- Version numbers synchronized across all files

## [0.5.1] - 2025-08-04

### Added
- **Interactive mode**: New `--interactive` (`-i`) flag for manual analysis workflows
  - Enables confirmation prompts when running analysis interactively
  - By default, NSGTree runs automatically without prompts (HPC-ready)
  - Added to both CLI and direct main.py interfaces
- Updated documentation with interactive mode examples and usage

### Changed
- **Flexible Tree Building**: Enhanced FastTree support with intelligent tool selection
  - Added `ft_variant` configuration option: "auto", "veryfasttree", or "fasttree"
  - Auto mode intelligently selects VeryFastTree for multi-threaded systems, FastTree for single-thread
  - Maintains backward compatibility while allowing manual tool selection
  - All three tree-building methods now fully supported: VeryFastTree, FastTree, and IQ-TREE
- **Enhanced CLI**: Added `--ft-variant` option for command-line tool selection
- **HPC-Friendly by Default**: Analysis now runs automatically without confirmation prompts by default
- Enhanced CLI help text to explain interactive vs automatic modes
- Updated README.md with comprehensive documentation of the new interactive option

### Fixed
- **Multi-threading Support**: Fixed tree building threading issues by migrating to VeryFastTree
  - Previous FastTree threading errors resolved with VeryFastTree's native support
  - Improved CPU utilization and faster tree reconstruction

### Technical Details
- Added interactive parameter to `nsgtree.cli.run()` function
- Added interactive handling in `nsgtree.main.main()` function
- Maintained backward compatibility - existing scripts will work unchanged
- Added proper version bumping across all components

## [0.5.0] - 2025-08-01

### Added
- **Pixi-based Installation**: Complete migration to Pixi package manager
- **Modern CLI Interface**: Built with Typer for excellent user experience
- **Rich Terminal UI**: Beautiful progress bars, tables, and colored output
- **Comprehensive Help System**: Built-in examples, model management, and system checking
- **Safety Features**: Timestamped output directories prevent overwrites
- **Enhanced Tree Analysis**: Full ete3 integration with ITOL visualization support

### Changed
- **Pure Python Implementation**: Replaced Snakemake with Python workflow
- **Simplified Installation**: Single `pixi install` command handles all dependencies
- **Current Directory Output**: Results saved to `./nsgt_out/` by default
- **Better Error Handling**: Comprehensive error messages and recovery

### Technical Improvements
- Cross-platform support (Linux, macOS, Windows with WSL)
- Automatic dependency management through Pixi
- Performance optimizations for faster execution
- Robust tree building with both FastTree and IQ-TREE support

### For Scientists
- Example-driven documentation with common usage patterns
- Built-in model management and validation
- System checks before running analyses
- Publication-ready tree visualization files
