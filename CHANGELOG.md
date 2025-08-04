# Changelog

All notable changes to NSGTree will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2025-08-04

### Added
- **Interactive mode**: New `--interactive` (`-i`) flag for manual analysis workflows
  - Enables confirmation prompts when running analysis interactively
  - By default, NSGTree runs automatically without prompts (HPC-ready)
  - Added to both CLI and direct main.py interfaces
- Updated documentation with interactive mode examples and usage

### Changed
- **HPC-Friendly by Default**: Analysis now runs automatically without confirmation prompts by default
- Enhanced CLI help text to explain interactive vs automatic modes
- Updated README.md with comprehensive documentation of the new interactive option

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
