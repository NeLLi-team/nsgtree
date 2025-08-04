#!/usr/bin/env python3
"""
NSGTree CLI - Comprehensive command-line interface for phylogenetic analysis
Built with Typer for an excellent user experience
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import Optional, List
import sys
import os

# Import the main workflow
from nsgtree.main import NSGTreeWorkflow

console = Console()

def version_callback(value: bool):
    """Handle version display"""
    if value:
        console.print("NSGTree version 0.5.1")
        console.print("DOE Joint Genome Institute")
        raise typer.Exit()

app = typer.Typer(
    name="nsgtree",
    help="🧬 NSGTree - New Simple Genome Tree: Fast phylogenetic analysis from protein sequences",
    epilog="For more information, visit: https://github.com/NeLLi-team/nsgtree",
    no_args_is_help=True,
    rich_markup_mode="rich"
)

@app.callback()
def cli_main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback,
        help="Show version information"
    )
):
    """NSGTree - Fast phylogenetic analysis"""
    pass

def print_banner():
    """Print a nice banner for NSGTree"""
    banner = """
[bold blue]🧬 NSGTree - New Simple Genome Tree[/bold blue]
[dim]Fast phylogenetic analysis from concatenated protein alignments[/dim]
[dim]Version 0.5.1 | DOE Joint Genome Institute[/dim]
    """
    console.print(Panel(banner, style="blue"))

def validate_path(path: str, must_exist: bool = True, path_type: str = "file") -> Path:
    """Validate and return a Path object"""
    p = Path(path)
    if must_exist and not p.exists():
        console.print(f"[red]Error: {path_type.title()} '{path}' does not exist![/red]")
        raise typer.Exit(1)
    return p

def list_available_models():
    """List available HMM model files"""
    models_dir = Path("resources/models")
    if models_dir.exists():
        models = list(models_dir.glob("*.hmm"))
        if models:
            table = Table(title="Available HMM Models")
            table.add_column("Model File", style="cyan")
            table.add_column("Description", style="green")

            descriptions = {
                "rnapol.hmm": "RNA polymerase markers (3 proteins)",
                "UNI56.hmm": "Universal single-copy markers (56 proteins)",
                "UNI56nr.hmm": "Universal markers, non-redundant",
                "UNI56r.hmm": "Universal markers, ribosomal",
                "gtdbbac.hmm": "GTDB bacterial markers",
                "gtdbarc.hmm": "GTDB archaeal markers",
                "mitomarkers108.hmm": "Mitochondrial markers (108 proteins)",
                "COX123.hmm": "Cytochrome oxidase subunits",
                "RProt16.hmm": "Ribosomal proteins (16 markers)",
                "GVOG7.hmm": "Giant virus orthologous groups",
                "GVOG9.hmm": "Giant virus orthologous groups",
                "mcrABG.hmm": "Methyl-coenzyme M reductase subunits"
            }

            for model in sorted(models):
                desc = descriptions.get(model.name, "Custom HMM markers")
                table.add_row(str(model), desc)

            console.print(table)
        else:
            console.print("[yellow]No HMM model files found in resources/models/[/yellow]")
    else:
        console.print("[yellow]Models directory not found. Make sure you're in the NSGTree directory.[/yellow]")

@app.command()
def run(
    qfaadir: str = typer.Argument(..., help="Directory containing query FAA files"),
    models: str = typer.Argument(..., help="Path to HMM models file"),
    rfaadir: Optional[str] = typer.Option(None, "--rfaadir", "-r", help="Directory containing reference FAA files (optional)"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="User configuration file (YAML format)"),
    cores: int = typer.Option(8, "--cores", "-j", help="Number of CPU cores to use", min=1, max=64),
    tree_method: Optional[str] = typer.Option(None, "--tree-method", "-t",
                                            help="Tree building method: 'fasttree' or 'iqtree'"),
    min_marker: Optional[float] = typer.Option(None, "--min-marker", "-m",
                                             help="Minimum fraction of markers required per genome", min=0.0, max=1.0),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
    output_name: Optional[str] = typer.Option(None, "--output-name", "-o", help="Custom output directory name"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Enable interactive mode with confirmation prompts")
):
    """
    🚀 Run complete NSGTree phylogenetic analysis

    This command performs the full NSGTree workflow:
    1. Reformat input sequences
    2. Run HMM search against protein markers
    3. Filter results and extract hits
    4. Align and trim sequences
    5. Build individual protein trees
    6. Create concatenated alignment
    7. Build species tree
    8. Generate visualization files
    9. Clean up and compress results

    By default, the analysis runs automatically without confirmation prompts,
    making it suitable for HPC environments and batch processing.

    Example usage:

    [bold cyan]Basic analysis:[/bold cyan]
    nsgtree run example resources/models/rnapol.hmm

    [bold cyan]With reference genomes:[/bold cyan]
    nsgtree run example_q resources/models/UNI56.hmm -r example_r

    [bold cyan]Interactive mode with confirmation:[/bold cyan]
    nsgtree run example resources/models/rnapol.hmm --interactive

    [bold cyan]Custom parameters:[/bold cyan]
    nsgtree run example resources/models/rnapol.hmm -c config.yml -j 16 -v
    """

    print_banner()

    # Validate inputs
    qfaa_path = validate_path(qfaadir, must_exist=True, path_type="directory")
    models_path = validate_path(models, must_exist=True, path_type="file")
    rfaa_path = None
    if rfaadir:
        rfaa_path = validate_path(rfaadir, must_exist=True, path_type="directory")

    # Count input files
    qfaa_files = list(qfaa_path.glob("*.faa"))
    rfaa_files = list(rfaa_path.glob("*.faa")) if rfaa_path else []

    if not qfaa_files:
        console.print(f"[red]Error: No .faa files found in {qfaadir}[/red]")
        raise typer.Exit(1)

    # Display analysis summary
    console.print("\n[bold green]Analysis Summary:[/bold green]")
    table = Table(show_header=False)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Query genomes", f"{len(qfaa_files)} files")
    if rfaa_files:
        table.add_row("Reference genomes", f"{len(rfaa_files)} files")
    table.add_row("HMM models", str(models_path))
    table.add_row("CPU cores", str(cores))
    if config:
        table.add_row("Config file", config)
    if tree_method:
        table.add_row("Tree method", tree_method)
    if min_marker:
        table.add_row("Min marker fraction", str(min_marker))

    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run completed. Use --verbose to see more details.[/yellow]")
        return

    # Confirm before running (only in interactive mode)
    if interactive:
        if not typer.confirm("\nProceed with analysis?"):
            console.print("Analysis cancelled.")
            raise typer.Exit(0)
    else:
        console.print("\n[green]Starting analysis...[/green]")

    # Set up workflow
    try:
        workflow = NSGTreeWorkflow(user_config_file=config)

        # Override config with command line arguments
        if cores:
            workflow.config['hmmsearch_cpu'] = str(cores)
            workflow.config['extract_processes'] = str(cores)
            workflow.config['tree_cpus'] = str(cores)
        if tree_method:
            workflow.config['tmethod'] = tree_method
        if min_marker:
            workflow.config['minmarker'] = str(min_marker)

        if verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)

        # Run workflow with progress indication
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running NSGTree analysis...", total=None)

            result_dir = workflow.run_workflow(
                qfaadir=str(qfaa_path),
                models=str(models_path),
                rfaadir=str(rfaa_path) if rfaa_path else None,
                output_dir=output_name
            )

            progress.update(task, completed=True, description="Analysis completed!")

        # Success message
        console.print(f"\n[bold green]✅ NSGTree analysis completed successfully![/bold green]")
        console.print(f"[green]Results saved to:[/green] {result_dir}")

        # Show output files
        result_path = Path(result_dir)
        console.print(f"\n[bold cyan]Key output files:[/bold cyan]")
        key_files = [
            (f"{result_path.name}.treefile", "Species tree (Newick format)"),
            (f"{result_path.name}.mafft_t", "Concatenated alignment"),
            ("proteintrees/", "Individual protein trees"),
            ("itol/", "Tree visualization files"),
            ("analyses.tar.gz", "Compressed results")
        ]

        for filename, description in key_files:
            file_path = result_path / filename
            if file_path.exists():
                console.print(f"  📄 {filename} - {description}")

        # Show visualization instructions
        tree_file = result_path / f"{result_path.name}.treefile"
        if tree_file.exists():
            console.print(f"\n[bold cyan]🎨 Tree Visualization:[/bold cyan]")
            console.print("1. Upload your tree to https://itol.embl.de/")
            console.print("2. Use ITOL annotation files in the 'itol/' directory")
            console.print("3. Check nearest neighbor analysis in '.pairs' files")

    except Exception as e:
        console.print(f"\n[bold red]❌ Analysis failed:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)

@app.command()
def models(
    list_models: bool = typer.Option(False, "--list", "-l", help="List available HMM model files")
):
    """
    📚 Manage HMM model files

    View information about available Hidden Markov Model files used for protein identification.
    These models define the phylogenetic markers used to build your trees.
    """
    if list_models or True:  # Always show models for now
        print_banner()
        console.print("[bold cyan]HMM Model Files[/bold cyan]\n")
        list_available_models()

@app.command()
def examples():
    """
    📖 Show example usage commands

    Display common usage patterns and example commands for different analysis scenarios.
    """
    print_banner()

    console.print("[bold cyan]Example Usage Commands[/bold cyan]\n")

    examples_table = Table(title="Common Analysis Scenarios")
    examples_table.add_column("Scenario", style="green", width=25)
    examples_table.add_column("Command", style="cyan", width=60)

    examples_data = [
        ("Basic analysis", "nsgtree run example resources/models/rnapol.hmm"),
        ("With references", "nsgtree run example_q resources/models/UNI56.hmm -r example_r"),
        ("Custom output dir", "nsgtree run example resources/models/rnapol.hmm -o my_results"),
        ("Custom config", "nsgtree run example resources/models/rnapol.hmm -c user_config.yml"),
        ("More CPU cores", "nsgtree run example resources/models/rnapol.hmm -j 16"),
        ("IQ-TREE method", "nsgtree run example resources/models/UNI56.hmm -t iqtree"),
        ("Strict filtering", "nsgtree run example resources/models/UNI56.hmm -m 0.8"),
        ("Verbose output", "nsgtree run example resources/models/rnapol.hmm -v"),
        ("Dry run test", "nsgtree run example resources/models/rnapol.hmm --dry-run")
    ]

    for scenario, command in examples_data:
        examples_table.add_row(scenario, command)

    console.print(examples_table)

    console.print(f"\n[bold green]Quick Start Guide:[/bold green]")
    console.print("1. List available models: [cyan]nsgtree models --list[/cyan]")
    console.print("2. Run basic analysis: [cyan]nsgtree run example resources/models/rnapol.hmm[/cyan]")
    console.print("3. Results are saved to [green]./nsgt_out/[/green] with timestamp (safe from overwrites)")
    console.print("4. Upload .treefile to https://itol.embl.de/ for visualization")

@app.command()
def check(
    qfaadir: Optional[str] = typer.Argument(None, help="Directory to check for FAA files"),
    models: Optional[str] = typer.Argument(None, help="HMM models file to validate")
):
    """
    🔍 Check input files and system requirements

    Validate your input files and verify that NSGTree is properly configured.
    This is helpful for troubleshooting before running an analysis.
    """
    print_banner()

    console.print("[bold cyan]NSGTree System Check[/bold cyan]\n")

    # Check dependencies
    console.print("[bold green]Checking dependencies...[/bold green]")
    dependencies = [
        ("Python", "python"),
        ("BioPython", "biopython"),
        ("HMMER", "hmmsearch"),
        ("MAFFT", "mafft"),
        ("trimAl", "trimal"),
        ("FastTree", "fasttree"),
        ("IQ-TREE", "iqtree"),
        ("ete3", "ete3")
    ]

    for name, module in dependencies:
        try:
            if module == "python":
                console.print(f"  ✅ {name}: Python {sys.version.split()[0]}")
            elif module in ["hmmsearch", "mafft", "trimal", "fasttree", "iqtree"]:
                import subprocess
                result = subprocess.run([module, "--help"], capture_output=True, text=True, timeout=5)
                console.print(f"  ✅ {name}: Available")
            else:
                __import__(module)
                console.print(f"  ✅ {name}: Available")
        except Exception:
            console.print(f"  ❌ {name}: Not available or not working")

    # Check input files if provided
    if qfaadir:
        console.print(f"\n[bold green]Checking input directory: {qfaadir}[/bold green]")
        qfaa_path = Path(qfaadir)
        if qfaa_path.exists():
            faa_files = list(qfaa_path.glob("*.faa"))
            console.print(f"  📁 Directory exists: {qfaa_path}")
            console.print(f"  📄 FAA files found: {len(faa_files)}")

            if faa_files:
                # Check a few files
                for i, faa_file in enumerate(faa_files[:3]):
                    with open(faa_file) as f:
                        first_line = f.readline().strip()
                        if first_line.startswith('>'):
                            console.print(f"  ✅ {faa_file.name}: Valid FASTA format")
                        else:
                            console.print(f"  ⚠️  {faa_file.name}: May not be valid FASTA format")

                if len(faa_files) > 3:
                    console.print(f"  ... and {len(faa_files) - 3} more files")
            else:
                console.print("  ❌ No .faa files found")
        else:
            console.print(f"  ❌ Directory does not exist: {qfaadir}")

    # Check models file if provided
    if models:
        console.print(f"\n[bold green]Checking models file: {models}[/bold green]")
        models_path = Path(models)
        if models_path.exists():
            console.print(f"  ✅ File exists: {models_path}")
            console.print(f"  📏 File size: {models_path.stat().st_size / 1024:.1f} KB")

            # Count HMM models in file
            try:
                with open(models_path) as f:
                    content = f.read()
                    model_count = content.count('NAME ')
                    console.print(f"  🧬 HMM models found: {model_count}")
            except Exception as e:
                console.print(f"  ⚠️  Could not parse HMM file: {e}")
        else:
            console.print(f"  ❌ File does not exist: {models}")

    console.print(f"\n[green]System check completed![/green]")

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show version information")
):
    """
    🧬 NSGTree - New Simple Genome Tree

    Fast and easy phylogenetic analysis from protein sequences using HMM markers.
    Build species trees from concatenated alignments with automatic visualization.
    """
    if version:
        console.print("NSGTree version 0.5.1")
        console.print("DOE Joint Genome Institute")
        raise typer.Exit()

if __name__ == "__main__":
    app()
