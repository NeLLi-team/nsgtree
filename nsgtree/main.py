#!/usr/bin/env python3
"""
NSGTree: New SGTree workflow implementation
Replaces the Snakemake workflow with a Python-based implementation
"""

import os
import sys
import argparse
import yaml
import logging
import subprocess
import shutil
from pathlib import Path
import tempfile
from datetime import datetime
import json

from .scripts import reformat
from .scripts import hmmsearch_count_filter
from .scripts import extract_qhits
from .scripts import concat
from .scripts import cleanup
from .scripts import ete3_clademembers
from .scripts import ete3_nntree


class ResourceMonitor:
    """Monitor CPU, memory, and wall-clock time using /usr/bin/time"""

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.resource_log = self.output_dir / f"resource_usage_{self.timestamp}.log"
        self.total_resources = {
            'wall_time_seconds': 0.0,
            'cpu_time_seconds': 0.0,
            'max_memory_gb': 0.0,
            'commands_executed': 0
        }

        # Check if /usr/bin/time is available
        self.time_available = self._check_time_availability()

        # Initialize log file
        self._initialize_log()

    def _check_time_availability(self):
        """Check if /usr/bin/time is available"""
        try:
            result = subprocess.run(["/usr/bin/time", "--version"],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except (FileNotFoundError, PermissionError):
            return False

    def _initialize_log(self):
        """Initialize the resource usage log file"""
        with open(self.resource_log, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"NSGTree Resource Usage Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Time monitoring available: {self.time_available}\n")
            f.write("Format: Command | Wall Time (s) | CPU Time (s) | Max Memory (GB) | CPU %\n")
            f.write("-" * 80 + "\n")

    def run_with_monitoring(self, cmd, description="Command", **kwargs):
        """Run a command with resource monitoring"""
        if not self.time_available:
            # Fallback to regular subprocess if /usr/bin/time is not available
            result = subprocess.run(cmd, **kwargs)
            self._log_command_fallback(cmd, description)
            return result

        # Create temporary file for time output
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.time', delete=False) as tmp:
            time_output_file = tmp.name

        try:
            # Prepare time command with custom format
            time_format = "%C\\n%e\\n%U\\n%S\\n%M\\n%P"
            time_cmd = [
                "/usr/bin/time",
                "-f", time_format,
                "-o", time_output_file
            ] + cmd

            # Run the command
            result = subprocess.run(time_cmd, **kwargs)

            # Parse the time output
            self._parse_and_log_time_output(time_output_file, cmd, description)

            return result

        finally:
            # Clean up temporary file
            try:
                os.unlink(time_output_file)
            except OSError:
                pass

    def _parse_and_log_time_output(self, time_output_file, cmd, description):
        """Parse /usr/bin/time output and log it"""
        try:
            with open(time_output_file, 'r') as f:
                lines = [line.strip() for line in f.readlines()]

            if len(lines) >= 6:
                command_str = lines[0]
                wall_time = float(lines[1])
                user_time = float(lines[2])
                sys_time = float(lines[3])
                max_memory_kb = int(lines[4])
                cpu_percent = lines[5].rstrip('%')

                cpu_time = user_time + sys_time
                max_memory_gb = max_memory_kb / (1024 * 1024)  # Convert KB to GB

                # Update totals
                self.total_resources['wall_time_seconds'] += wall_time
                self.total_resources['cpu_time_seconds'] += cpu_time
                self.total_resources['max_memory_gb'] = max(
                    self.total_resources['max_memory_gb'], max_memory_gb
                )
                self.total_resources['commands_executed'] += 1

                # Log to file
                with open(self.resource_log, 'a') as f:
                    f.write(f"{description}: {' '.join(cmd)}\n")
                    f.write(f"  Wall Time: {wall_time:.2f}s | CPU Time: {cpu_time:.2f}s | ")
                    f.write(f"Max Memory: {max_memory_gb:.3f} GB | CPU: {cpu_percent}%\n")
                    f.write("-" * 80 + "\n")

        except (ValueError, IndexError, FileNotFoundError) as e:
            self._log_command_fallback(cmd, description, error=str(e))

    def _log_command_fallback(self, cmd, description, error=None):
        """Log command without resource monitoring"""
        with open(self.resource_log, 'a') as f:
            f.write(f"{description}: {' '.join(cmd)}\n")
            if error:
                f.write(f"  Resource monitoring failed: {error}\n")
            else:
                f.write("  Resource monitoring not available\n")
            f.write("-" * 80 + "\n")

        self.total_resources['commands_executed'] += 1

    def generate_final_report(self):
        """Generate final resource usage report"""
        report = {
            'timestamp': self.timestamp,
            'total_wall_time_seconds': self.total_resources['wall_time_seconds'],
            'total_wall_time_formatted': self._format_time(self.total_resources['wall_time_seconds']),
            'total_cpu_time_seconds': self.total_resources['cpu_time_seconds'],
            'total_cpu_time_formatted': self._format_time(self.total_resources['cpu_time_seconds']),
            'max_memory_gb': self.total_resources['max_memory_gb'],
            'commands_executed': self.total_resources['commands_executed'],
            'monitoring_available': self.time_available
        }

        # Write summary to log
        with open(self.resource_log, 'a') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("FINAL RESOURCE USAGE SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Wall Time: {report['total_wall_time_formatted']}\n")
            f.write(f"Total CPU Time: {report['total_cpu_time_formatted']}\n")
            f.write(f"Peak Memory Usage: {report['max_memory_gb']:.3f} GB\n")
            f.write(f"Commands Executed: {report['commands_executed']}\n")
            f.write(f"Resource Log: {self.resource_log}\n")
            f.write("=" * 80 + "\n")

        return report

    def _format_time(self, seconds):
        """Format seconds into human-readable time"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.1f}s"


class NSGTreeWorkflow:
    def __init__(self, config_file="config.yml", user_config_file=None):
        self.logger = self._setup_logging()
        self.config = self._load_config(config_file, user_config_file)
        self.workflow_log = None
        self.resource_monitor = None

    def _setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _load_config(self, config_file, user_config_file):
        """Load configuration from YAML files"""
        # Load default config
        default_config_path = Path(__file__).parent / "config" / "default_config.yml"
        if not default_config_path.exists():
            # Fallback to basic config
            config = {
                'tmethod': 'fasttree',
                'rfaadir': '',
                'hmmsearch_cutoff': '-E 1e-5',
                'hmmsearch_cpu': '8',
                'minmarker': '0.1',
                'maxsdup': '4',
                'maxdupl': '0.3',
                'extract_processes': '8',
                'tree_cpus': '8',
                'ft_proteintrees': '-spr 4 -mlacc 3 -slownni -lg',
                'ft_speciestree': '-spr 4 -mlacc 3 -slownni -lg',
                'iq_proteintrees': 'LG+F+I+G4',
                'iq_speciestree': 'LG+F+I+G4',
                'lengthfilter': '0.5',
                'mafft_thread': '--thread 4',
                'mafftv': '',
                'mafft': '',
                'trimal_gt': '-gt 0.1'
            }
        else:
            with open(default_config_path, 'r') as f:
                config = yaml.safe_load(f)

        # Override with user config if provided
        if user_config_file and os.path.exists(user_config_file):
            with open(user_config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                config.update(user_config)

        return config

    def _find_existing_analysis(self, base_output_dir, analysisname_base, force_new=False):
        """Find existing analysis directory that matches the current parameters"""
        if force_new or not base_output_dir.exists():
            return None

        # Look for directories that start with the analysis name base
        pattern = f"{analysisname_base}_*"
        matching_dirs = list(base_output_dir.glob(pattern))

        if not matching_dirs:
            return None

        # Filter to only resumable analyses and rank by progress
        resumable_analyses = []
        for analysis_dir in matching_dirs:
            if self._is_resumable_analysis(analysis_dir):
                progress_score = self._calculate_analysis_progress(analysis_dir)
                resumable_analyses.append((analysis_dir, progress_score))

        if not resumable_analyses:
            return None

        # Sort by progress score (highest first), then by modification time
        resumable_analyses.sort(key=lambda x: (x[1], x[0].stat().st_mtime), reverse=True)

        return resumable_analyses[0][0]

    def _calculate_analysis_progress(self, analysis_dir):
        """Calculate how much progress has been made in an analysis (0-100)"""
        progress = 0

        # Check each major step completion
        analyses_dir = analysis_dir / "analyses"
        if not analyses_dir.exists():
            return 0

        # Step 1: Reformatted FAA files (10 points)
        reformatted_dir = analyses_dir / "reformatted_faa"
        if reformatted_dir.exists() and list(reformatted_dir.glob("*.faa")):
            progress += 10

        # Step 2: Merged FAA (5 points)
        merged_faa = analyses_dir / "tmp" / "merged.faa"
        if merged_faa.exists() and merged_faa.stat().st_size > 0:
            progress += 5

        # Step 3: HMMsearch (15 points)
        hmmout_dir = analyses_dir / "hmmout"
        if hmmout_dir.exists():
            hmm_files = list(hmmout_dir.glob("*.out"))
            if hmm_files and any(f.stat().st_size > 0 for f in hmm_files):
                progress += 15

        # Step 4: Filtering (5 points)
        if hmmout_dir.exists():
            filter_files = list(hmmout_dir.glob("*.counts")) + list(hmmout_dir.glob("*.removedtaxa"))
            if filter_files and any(f.exists() for f in filter_files):
                progress += 5

        # Step 5: Hit extraction (10 points)
        hits_dir = analyses_dir / "hits_faa"
        if hits_dir.exists():
            hit_files = list(hits_dir.glob("*.faa"))
            if hit_files:
                progress += 10

        # Step 6: Alignments (15 points)
        aligned_t_dir = analyses_dir / "aligned_t"
        if aligned_t_dir.exists():
            aligned_files = list(aligned_t_dir.glob("*.mafft_t"))
            if aligned_files and any(f.stat().st_size > 0 for f in aligned_files):
                progress += 15

        # Step 7: Protein trees (15 points)
        proteintrees_dir = analysis_dir / "proteintrees"
        if proteintrees_dir.exists():
            tree_files = list(proteintrees_dir.glob("*.treefile"))
            if tree_files and any(f.stat().st_size > 0 for f in tree_files):
                progress += 15

        # Step 8: Concatenated alignment (20 points)
        analysisname = analysis_dir.name
        concat_file = analysis_dir / f"{analysisname}.mafft_t"
        if concat_file.exists() and concat_file.stat().st_size > 0:
            progress += 20

        # Step 9: Species tree (10 points) - if this exists, analysis shouldn't be resumable
        final_tree = analysis_dir / f"{analysisname}.treefile"
        if final_tree.exists() and final_tree.stat().st_size > 0:
            progress += 10

        return progress

    def _is_resumable_analysis(self, analysis_dir):
        """Check if an analysis directory can be resumed"""
        if not analysis_dir.is_dir():
            return False

        # Check if workflow.log exists (indicates it was started)
        workflow_log = analysis_dir / "workflow.log"
        if not workflow_log.exists():
            return False

        # Check if analysis is complete by looking for final tree and completion marker
        analysisname = analysis_dir.name
        final_tree = analysis_dir / f"{analysisname}.treefile"

        # If final tree exists and has content, analysis is complete - don't resume
        if final_tree.exists() and final_tree.stat().st_size > 0:
            return False

        # Check for species tree completion flag
        fasttree_complete = analysis_dir / "analyses" / "finaltree" / "fasttree" / f"{analysisname}.complete"
        iqtree_complete = analysis_dir / "analyses" / "finaltree" / "iqtree" / f"{analysisname}.complete"

        # If species tree is complete, analysis is done - don't resume
        if (fasttree_complete.exists() or iqtree_complete.exists()):
            return False

        # This is an incomplete analysis that can be resumed
        return True

    def run_workflow(self, qfaadir, models, rfaadir=None, output_dir=None, force_new=False):
        """Run the complete NSGTree workflow"""
        try:
            # Initialize paths and variables
            qfaadir = Path(qfaadir)
            qfaadir_base = os.path.basename(qfaadir)

            if rfaadir:
                rfaadir = Path(rfaadir)
                rfaadir_base = os.path.basename(rfaadir)
            else:
                rfaadir_base = ""

            modelscombined = Path(models)
            models_base = modelscombined.stem

            # Create analysis name WITHOUT timestamp for checkpoint detection
            analysisname_base = str(qfaadir_base +
                "-" + rfaadir_base +
                "-" + models_base +
                "-" + self.config["tmethod"] +
                "-perc" + str(int(float(self.config["minmarker"])*10))).replace(".", "")

            # Set up output directory and check for existing analysis
            if output_dir:
                base_output_dir = Path(output_dir)
            else:
                base_output_dir = Path.cwd() / "nsgt_out"

            # Look for existing analysis directories
            existing_analysis = self._find_existing_analysis(base_output_dir, analysisname_base, force_new)

            if existing_analysis:
                outdir = existing_analysis
                analysisname = existing_analysis.name
                self.logger.info(f"Found existing analysis, resuming: {analysisname}")
                self.logger.info(f"Resume directory: {outdir}")
            else:
                # Create new analysis with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                analysisname = analysisname_base + "_" + timestamp
                outdir = base_output_dir / analysisname
                outdir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Starting new NSGTree workflow: {analysisname}")
                self.logger.info(f"Output directory: {outdir}")

            # Set up workflow log
            self.workflow_log = outdir / "workflow.log"

            # Initialize resource monitor
            self.resource_monitor = ResourceMonitor(outdir)

            if existing_analysis:
                self.logger.info(f"Resuming NSGTree workflow: {analysisname}")
                self.logger.info(f"Resume directory: {outdir}")
            else:
                self.logger.info(f"Starting NSGTree workflow: {analysisname}")
                self.logger.info(f"Output directory: {outdir}")

            self.logger.info(f"Resource monitoring: {'enabled' if self.resource_monitor.time_available else 'disabled'}")

            # Write initial log (only if not resuming)
            if not existing_analysis:
                self._write_initial_log()
            else:
                # Append resume marker to existing log
                with open(str(self.workflow_log), 'a') as f:
                    f.write(f"\n################################\n")
                    f.write(f"Resuming analysis at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"################################\n")

            # Step 1: Reformat FAA files
            self.logger.info("Step 1: Reformatting FAA files")
            reformatted_faa_dir = self._reformat_faa_files(qfaadir, rfaadir, outdir)

            # Step 2: Merge FAA files
            self.logger.info("Step 2: Merging FAA files")
            merged_faa = self._merge_faa_files(reformatted_faa_dir, outdir)

            # Step 3: Run HMMsearch
            self.logger.info("Step 3: Running HMMsearch")
            hmmsearch_output = self._run_hmmsearch(merged_faa, modelscombined, outdir, models_base)

            # Step 4: Filter HMMsearch results
            self.logger.info("Step 4: Filtering HMMsearch results")
            taxa_removed = self._filter_hmmsearch_results(hmmsearch_output, reformatted_faa_dir,
                                                        modelscombined, outdir, models_base)

            # Step 5: Extract model names
            models_list = self._extract_model_names(modelscombined)

            # Step 6: Extract hits for each model
            self.logger.info("Step 6: Extracting hits for each model")
            self._extract_hits_parallel(models_list, hmmsearch_output, reformatted_faa_dir,
                                      taxa_removed, outdir)

            # Step 7: Align and trim sequences
            self.logger.info("Step 7: Aligning and trimming sequences")
            self._align_trim_parallel(models_list, outdir)

            # Step 8: Build individual protein trees
            self.logger.info("Step 8: Building protein trees")
            self._build_trees_parallel(models_list, outdir)

            # Step 9: Concatenate alignments
            self.logger.info("Step 9: Concatenating alignments")
            concat_aln = self._concatenate_alignments(models_list, outdir, analysisname)

            # Step 10: Build species tree
            self.logger.info("Step 10: Building species tree")
            self._build_species_tree(concat_aln, outdir, analysisname)

            # Step 11: Generate tree visualizations and analysis
            self.logger.info("Step 11: Generating tree visualizations and analysis")
            self._generate_tree_analysis(outdir, analysisname, qfaadir, rfaadir)

            # Step 12: Cleanup and compress
            self.logger.info("Step 12: Cleaning up and compressing results")
            self._cleanup_and_compress(outdir, analysisname)

            # Generate final resource usage report
            if self.resource_monitor:
                resource_report = self.resource_monitor.generate_final_report()
                self.logger.info("Resource Usage Summary:")
                self.logger.info(f"  Total Wall Time: {resource_report['total_wall_time_formatted']}")
                self.logger.info(f"  Total CPU Time: {resource_report['total_cpu_time_formatted']}")
                self.logger.info(f"  Peak Memory Usage: {resource_report['max_memory_gb']:.3f} GB")
                self.logger.info(f"  Commands Executed: {resource_report['commands_executed']}")
                self.logger.info(f"  Resource Log: {self.resource_monitor.resource_log}")

            self.logger.info("NSGTree workflow completed successfully!")
            return str(outdir)

        except Exception as e:
            self.logger.error(f"Workflow failed: {str(e)}")

            # Generate resource report even on failure
            if self.resource_monitor:
                resource_report = self.resource_monitor.generate_final_report()
                self.logger.error("Resource Usage Summary (at failure):")
                self.logger.error(f"  Wall Time Used: {resource_report['total_wall_time_formatted']}")
                self.logger.error(f"  CPU Time Used: {resource_report['total_cpu_time_formatted']}")
                self.logger.error(f"  Peak Memory Usage: {resource_report['max_memory_gb']:.3f} GB")
                self.logger.error(f"  Resource Log: {self.resource_monitor.resource_log}")

            raise

    def _write_initial_log(self):
        """Write initial information to workflow log"""
        with open(str(self.workflow_log), 'w') as f:
            f.write("NSGTree (New SGTree)\n")
            f.write("v0.5, March 2024\n")
            f.write("fschulz@lbl.gov\n")
            f.write("Build genome tree from concatenated alignment after hmmsearch using a set of user provided HMMs\n")
            f.write("No special characters in filename, no additional '.'\n")
            f.write("################################\n")

    def _reformat_faa_files(self, qfaadir, rfaadir, outdir):
        """Reformat FAA files"""
        reformatted_faa_dir = outdir / "analyses" / "reformatted_faa"
        reformatted_faa_dir.mkdir(parents=True, exist_ok=True)

        # Check if reformatting is already completed by looking for expected files
        expected_query_files = len(list(qfaadir.glob("*.faa")))
        existing_files = len(list(reformatted_faa_dir.glob("*.faa")))

        if rfaadir:
            expected_ref_files = len(list(rfaadir.glob("*.faa")))
            expected_total = expected_query_files + expected_ref_files
        else:
            expected_total = expected_query_files

        if existing_files >= expected_total and existing_files > 0:
            self.logger.info(f"Reformatted FAA files already exist ({existing_files} files), skipping reformat step")
            return reformatted_faa_dir

        # Reformat query files
        reformat.main([str(qfaadir), str(reformatted_faa_dir)])

        # Reformat reference files if provided
        if rfaadir:
            reformat.main([str(rfaadir), str(reformatted_faa_dir)])

            # Create ITOL files for queries
            itol_dir = outdir / "itol"
            itol_dir.mkdir(exist_ok=True)

            # This would need to be implemented based on the shell commands in Snakefile
            # For now, we'll skip the ITOL file generation

        return reformatted_faa_dir

    def _merge_faa_files(self, reformatted_faa_dir, outdir):
        """Merge all FAA files into one"""
        tmp_dir = outdir / "analyses" / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        merged_faa = tmp_dir / "merged.faa"

        # Check if merge is already completed
        if merged_faa.exists() and merged_faa.stat().st_size > 0:
            self.logger.info("Merged FAA file already exists, skipping merge step")
            return merged_faa

        # Concatenate all FAA files
        with open(merged_faa, 'w') as outfile:
            for faa_file in reformatted_faa_dir.glob("*.faa"):
                with open(faa_file, 'r') as infile:
                    outfile.write(infile.read())

        # Count genomes
        genome_count = len(list(reformatted_faa_dir.glob("*.faa")))
        with open(str(self.workflow_log), 'a') as f:
            f.write(f"Number of genomes in the analysis: {genome_count}\n")
            f.write("################################\n")

        return merged_faa

    def _run_hmmsearch(self, merged_faa, modelscombined, outdir, models_base):
        """Run HMMsearch"""
        hmmout_dir = outdir / "analyses" / "hmmout"
        hmmout_dir.mkdir(parents=True, exist_ok=True)

        log_dir = outdir / "analyses" / "log" / "hmmsearch"
        log_dir.mkdir(parents=True, exist_ok=True)

        hmmsearch_output = hmmout_dir / f"{models_base}.out"
        log_file = log_dir / "hmmsearch.log"

        # Check if HMMsearch is already completed
        if hmmsearch_output.exists() and hmmsearch_output.stat().st_size > 0:
            self.logger.info("HMMsearch output already exists, skipping HMMsearch step")
            return hmmsearch_output

        # Run hmmsearch
        cmd = [
            "hmmsearch",
            "--noali",
            self.config["hmmsearch_cutoff"],
            "--domtblout", str(hmmsearch_output),
            "--cpu", self.config["hmmsearch_cpu"],
            str(modelscombined),
            str(merged_faa)
        ]

        with open(log_file, 'w') as f:
            f.write(" ".join(cmd) + "\n")
            if self.resource_monitor:
                result = self.resource_monitor.run_with_monitoring(
                    cmd, "HMMsearch", stdout=f, stderr=subprocess.STDOUT
                )
            else:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)

        if result.returncode != 0:
            raise RuntimeError(f"HMMsearch failed with return code {result.returncode}")

        return hmmsearch_output

    def _filter_hmmsearch_results(self, hmmsearch_output, reformatted_faa_dir,
                                 modelscombined, outdir, models_base):
        """Filter HMMsearch results"""
        hmmout_dir = outdir / "analyses" / "hmmout"
        itol_dir = outdir / "itol"
        itol_dir.mkdir(exist_ok=True)

        hitcounts = hmmout_dir / f"{models_base}.counts"
        taxa_removed = hmmout_dir / f"{models_base}.removedtaxa"
        itolcounts = itol_dir / f"{models_base}.counts.itol.txt"

        # Check if filtering is already completed
        if (hitcounts.exists() and hitcounts.stat().st_size > 0 and
            taxa_removed.exists() and itolcounts.exists()):
            self.logger.info("HMMsearch filtering already completed, skipping filter step")
            return taxa_removed

        # Call the filtering script
        args = [
            str(reformatted_faa_dir),
            str(modelscombined),
            str(hmmsearch_output),
            str(hitcounts),
            str(taxa_removed),
            self.config["minmarker"],
            self.config["maxsdup"],
            self.config["maxdupl"],
            str(itolcounts)
        ]

        hmmsearch_count_filter.main(args)

        # Log removed taxa count
        if taxa_removed.exists():
            with open(taxa_removed, 'r') as f:
                removed_count = len(f.readlines())
            with open(str(self.workflow_log), 'a') as f:
                f.write(f"Number of genomes that were removed due to filtering thresholds: {removed_count}\n")

        return taxa_removed

    def _extract_model_names(self, modelscombined):
        """Extract model names from HMM file"""
        models = []
        with open(modelscombined, 'r') as f:
            for line in f:
                if line.startswith("NAME"):
                    models.append(line.strip().split()[-1])
        return models

    def _extract_hits_parallel(self, models_list, hmmsearch_output, reformatted_faa_dir,
                              taxa_removed, outdir):
        """Extract hits for each model in parallel"""
        hits_dir = outdir / "analyses" / "hits_faa"
        hits_dir.mkdir(parents=True, exist_ok=True)

        log_dir = outdir / "analyses" / "log" / "extraction"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Check if extraction is already completed for all models
        expected_files = [hits_dir / f"{model}.faa" for model in models_list]
        completed_files = [f for f in expected_files if f.exists()]

        if len(completed_files) == len(expected_files):
            self.logger.info(f"Hit extraction already completed for all {len(models_list)} models, skipping extraction step")
            return

        # Use single-threaded approach for simplicity
        for model in models_list:
            output_file = hits_dir / f"{model}.faa"
            log_file = log_dir / f"{model}.log"

            # Skip if this model is already extracted
            if output_file.exists():
                self.logger.info(f"Hits for {model} already extracted, skipping")
                continue

            args = [
                str(hmmsearch_output),
                str(reformatted_faa_dir),
                self.config["extract_processes"],
                str(taxa_removed),
                str(output_file),
                self.config["lengthfilter"]
            ]

            try:
                # Redirect stdout to log file
                with open(log_file, 'w') as f:
                    original_stdout = sys.stdout
                    sys.stdout = f
                    extract_qhits.main(args)
                    sys.stdout = original_stdout

                self.logger.info(f"Extracted hits for {model}")
            except Exception as e:
                self.logger.error(f"Failed to extract hits for {model}: {str(e)}")
                # Create empty file to continue pipeline
                output_file.touch()

    def _align_trim_parallel(self, models_list, outdir):
        """Align and trim sequences for each model"""
        hits_dir = outdir / "analyses" / "hits_faa"
        aligned_dir = outdir / "analyses" / "aligned"
        aligned_t_dir = outdir / "analyses" / "aligned_t"

        aligned_dir.mkdir(parents=True, exist_ok=True)
        aligned_t_dir.mkdir(parents=True, exist_ok=True)

        log_dir = outdir / "analyses" / "log" / "aln"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Check if all alignments are already completed
        expected_files = [aligned_t_dir / f"{model}.mafft_t" for model in models_list]
        completed_files = [f for f in expected_files if f.exists() and f.stat().st_size > 0]

        if len(completed_files) == len(expected_files):
            self.logger.info(f"Alignment and trimming already completed for all {len(models_list)} models, skipping alignment step")
            return

        for model in models_list:
            hits_file = hits_dir / f"{model}.faa"
            aligned_file = aligned_dir / f"{model}.mafft"
            trimmed_file = aligned_t_dir / f"{model}.mafft_t"
            log_file = log_dir / f"{model}.log"

            # Check if alignment and trimming is already completed
            if trimmed_file.exists() and trimmed_file.stat().st_size > 0:
                self.logger.info(f"Alignment and trimming for {model} already completed, skipping")
                continue

            try:
                with open(log_file, 'w') as f:
                    # Run MAFFT
                    mafft_cmd = ["mafft", "--quiet"]

                    # Add thread parameter if specified
                    if self.config["mafft_thread"]:
                        thread_param = self.config["mafft_thread"].strip()
                        if thread_param.startswith("--thread"):
                            mafft_cmd.extend(thread_param.split())

                    mafft_cmd.append(str(hits_file))

                    if hits_file.exists() and hits_file.stat().st_size > 0:
                        with open(aligned_file, 'w') as align_out:
                            if self.resource_monitor:
                                result = self.resource_monitor.run_with_monitoring(
                                    mafft_cmd, f"MAFFT-{model}", stdout=align_out, stderr=f
                                )
                            else:
                                result = subprocess.run(mafft_cmd, stdout=align_out, stderr=f)
                    else:
                        aligned_file.touch()

                    # Run trimal
                    trimal_cmd = ["trimal"]
                    if self.config["trimal_gt"]:
                        trimal_cmd.extend(self.config["trimal_gt"].split())
                    trimal_cmd.extend(["-in", str(aligned_file), "-out", str(trimmed_file)])

                    if aligned_file.exists() and aligned_file.stat().st_size > 0:
                        if self.resource_monitor:
                            result = self.resource_monitor.run_with_monitoring(
                                trimal_cmd, f"Trimal-{model}", stderr=f
                            )
                        else:
                            result = subprocess.run(trimal_cmd, stderr=f)
                    else:
                        trimmed_file.touch()

                self.logger.info(f"Aligned and trimmed {model}")
            except Exception as e:
                self.logger.error(f"Failed to align/trim {model}: {str(e)}")
                # Create empty files to continue pipeline
                aligned_file.touch()
                trimmed_file.touch()

    def _build_trees_parallel(self, models_list, outdir):
        """Build individual protein trees"""
        aligned_t_dir = outdir / "analyses" / "aligned_t"
        proteintrees_dir = outdir / "proteintrees"
        proteintrees_dir.mkdir(parents=True, exist_ok=True)

        if self.config["tmethod"] == "fasttree":
            analysis_dir = outdir / "analyses" / "proteintrees" / "fasttree"
        else:
            analysis_dir = outdir / "analyses" / "proteintrees" / "iqtree"

        analysis_dir.mkdir(parents=True, exist_ok=True)

        log_dir = outdir / "analyses" / "log" / "trees"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Check if all protein trees are already completed
        expected_flags = [analysis_dir / f"{model}.complete" for model in models_list]
        expected_trees = [proteintrees_dir / f"{model}.treefile" for model in models_list]
        completed_trees = [
            i for i, (flag, tree) in enumerate(zip(expected_flags, expected_trees))
            if flag.exists() and tree.exists() and tree.stat().st_size > 0
        ]

        if len(completed_trees) == len(models_list):
            self.logger.info(f"Protein trees already completed for all {len(models_list)} models, skipping tree building step")
            return

        for model in models_list:
            trimmed_file = aligned_t_dir / f"{model}.mafft_t"
            tree_file = proteintrees_dir / f"{model}.treefile"
            log_file = log_dir / f"{model}.log"
            complete_flag = analysis_dir / f"{model}.complete"

            # Check if tree is already completed
            if complete_flag.exists() and tree_file.exists() and tree_file.stat().st_size > 0:
                self.logger.info(f"Tree for {model} already exists, skipping")
                continue

            try:
                with open(log_file, 'w') as f:
                    if self.config["tmethod"] == "fasttree":
                        # FastTree
                        cmd = [
                            "fasttree",
                            "-threads", "1",  # Use 1 thread per process
                            str(trimmed_file)
                        ]

                        if trimmed_file.exists() and trimmed_file.stat().st_size > 0:
                            with open(tree_file, 'w') as tree_out:
                                if self.resource_monitor:
                                    result = self.resource_monitor.run_with_monitoring(
                                        cmd, f"FastTree-protein-{model}", stdout=tree_out, stderr=f
                                    )
                                else:
                                    result = subprocess.run(cmd, stdout=tree_out, stderr=f)
                        else:
                            tree_file.touch()

                    else:
                        # IQ-TREE
                        outpath = analysis_dir / model
                        cmd = [
                            "iqtree",
                            "--prefix", str(outpath),
                            "-m", self.config["iq_proteintrees"],
                            "-T", "1",
                            "-fast",
                            "-s", str(trimmed_file)
                        ]

                        if trimmed_file.exists() and trimmed_file.stat().st_size > 0:
                            if self.resource_monitor:
                                result = self.resource_monitor.run_with_monitoring(
                                    cmd, f"IQ-TREE-protein-{model}", stderr=f
                                )
                            else:
                                result = subprocess.run(cmd, stderr=f)
                            # Copy appropriate tree file
                            contree = f"{outpath}.contree"
                            treefile = f"{outpath}.treefile"
                            if os.path.exists(contree):
                                shutil.copy(contree, tree_file)
                            elif os.path.exists(treefile):
                                shutil.copy(treefile, tree_file)
                            else:
                                tree_file.touch()
                        else:
                            tree_file.touch()

                complete_flag.touch()
                self.logger.info(f"Built tree for {model}")
            except Exception as e:
                self.logger.error(f"Failed to build tree for {model}: {str(e)}")
                # Create empty files to continue pipeline
                tree_file.touch()
                complete_flag.touch()

    def _concatenate_alignments(self, models_list, outdir, analysisname):
        """Concatenate alignments"""
        aligned_t_dir = outdir / "analyses" / "aligned_t"
        concat_aln = outdir / f"{analysisname}.mafft_t"

        # Check if concatenation is already completed
        if concat_aln.exists() and concat_aln.stat().st_size > 0:
            self.logger.info(f"Concatenated alignment already exists, skipping concatenation")
        else:
            # Use the concat script
            concat.main([str(aligned_t_dir), str(concat_aln)])

        # Count genomes in final alignment
        if concat_aln.exists() and concat_aln.stat().st_size > 0:
            with open(concat_aln, 'r') as f:
                genome_count = sum(1 for line in f if line.startswith('>'))

            with open(str(self.workflow_log), 'a') as f:
                f.write("################################\n")
                f.write(f"Number of genomes in the final alignment: {genome_count}\n")

        return concat_aln

    def _build_species_tree(self, concat_aln, outdir, analysisname):
        """Build species tree from concatenated alignment"""
        if self.config["tmethod"] == "fasttree":
            finaltree_dir = outdir / "analyses" / "finaltree" / "fasttree"
        else:
            finaltree_dir = outdir / "analyses" / "finaltree" / "iqtree"

        finaltree_dir.mkdir(parents=True, exist_ok=True)

        species_tree = finaltree_dir / f"{analysisname}.treefile"
        concat_tree = outdir / f"{analysisname}.treefile"
        complete_flag = finaltree_dir / f"{analysisname}.complete"

        # Check if species tree is already completed
        if complete_flag.exists() and species_tree.exists() and species_tree.stat().st_size > 0:
            self.logger.info(f"Species tree already exists and is complete, skipping reconstruction")
            # Ensure the final tree is copied to the main output directory
            if not concat_tree.exists() or concat_tree.stat().st_size == 0:
                shutil.copy(species_tree, concat_tree)
            return

        log_file = outdir / "analyses" / "log" / "trees" / "speciestree.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if we have enough genomes
        if concat_aln.exists() and concat_aln.stat().st_size > 0:
            with open(concat_aln, 'r') as f:
                genome_count = sum(1 for line in f if line.startswith('>'))
        else:
            genome_count = 0

        if genome_count <= 3:
            error_msg = "Too few genomes in the supermatrix alignment. Check filtering thresholds to increase numbers of genomes to be retained."
            self.logger.error(error_msg)
            with open(str(self.workflow_log), 'a') as f:
                f.write(error_msg + "\n")
            raise RuntimeError(error_msg)

        with open(log_file, 'w') as f:
            if self.config["tmethod"] == "fasttree":
                # FastTree - simplified command (no threading support in this version)
                cmd = ["fasttree"]

                # Add other fasttree parameters (skip threading options)
                ft_params = self.config.get("ft_speciestree", "").strip()
                if ft_params:
                    # Split parameters and filter out threading options
                    for param in ft_params.split():
                        if param.strip() and not param.startswith("-thread"):
                            cmd.append(param.strip())

                # Add input file
                cmd.append(str(concat_aln))

                f.write(" ".join(cmd) + "\n")
                self.logger.info(f"Running FastTree: {' '.join(cmd)}")

                with open(species_tree, 'w') as tree_out:
                    if self.resource_monitor:
                        result = self.resource_monitor.run_with_monitoring(
                            cmd, "FastTree-species", stdout=tree_out, stderr=f
                        )
                    else:
                        result = subprocess.run(cmd, stdout=tree_out, stderr=f)
                    if result.returncode != 0:
                        self.logger.error(f"FastTree failed with return code {result.returncode}")

            else:
                # IQ-TREE
                outpath = finaltree_dir / analysisname
                cmd = [
                    "iqtree",
                    "--quiet",
                    "--prefix", str(outpath),
                    "-m", self.config["iq_speciestree"],
                    "-s", str(concat_aln)
                ]

                f.write(" ".join(cmd) + "\n")
                if self.resource_monitor:
                    result = self.resource_monitor.run_with_monitoring(
                        cmd, "IQ-TREE-species", stderr=f
                    )
                else:
                    result = subprocess.run(cmd, stderr=f)

                # Copy tree files
                shutil.copy(f"{outpath}.treefile", species_tree)
                if os.path.exists(f"{outpath}.contree"):
                    shutil.copy(f"{outpath}.contree", outdir / f"{analysisname}.contree")

        # Copy final tree
        if species_tree.exists() and species_tree.stat().st_size > 0:
            shutil.copy(species_tree, concat_tree)
        else:
            # Create empty file to indicate completion
            concat_tree.touch()

        complete_flag.touch()

    def _generate_tree_analysis(self, outdir, analysisname, qfaadir, rfaadir):
        """Generate tree visualizations and analysis using ete3"""
        species_tree = outdir / f"{analysisname}.treefile"
        itol_dir = outdir / "itol"
        itol_dir.mkdir(exist_ok=True)

        # Only proceed if we have a valid tree file
        if not species_tree.exists() or species_tree.stat().st_size == 0:
            self.logger.warning("No valid species tree found, skipping visualization")
            return

        try:
            # Generate query genome list
            query_genomes = []
            for faa_file in qfaadir.glob("*.faa"):
                genome_name = faa_file.stem
                query_genomes.append(genome_name)

            # Create query list file
            query_list_file = itol_dir / "query_genomes.txt"
            with open(query_list_file, 'w') as f:
                for genome in query_genomes:
                    f.write(f"{genome}\n")

            # Generate clade analysis for ITOL visualization
            self.logger.info("Generating clade analysis for ITOL")
            clade_output = itol_dir / f"{analysisname}_clades.itol"

            # Run ete3_clademembers
            ete3_clademembers.main([
                str(species_tree),
                str(query_list_file),
                "FF0000",  # Red color for query clades
                str(clade_output)
            ])

            # Generate nearest neighbor analysis
            self.logger.info("Generating nearest neighbor analysis")
            nn_output = itol_dir / f"{analysisname}_neighbors"

            # Run ete3_nntree
            ete3_nntree.main([
                str(species_tree),
                str(query_list_file),
                str(nn_output)
            ])

            # Create summary file
            summary_file = itol_dir / f"{analysisname}_analysis_summary.txt"
            with open(summary_file, 'w') as f:
                f.write("NSGTree Analysis Summary\n")
                f.write("========================\n\n")
                f.write(f"Analysis name: {analysisname}\n")
                f.write(f"Query genomes: {len(query_genomes)}\n")
                f.write(f"Species tree: {species_tree.name}\n\n")
                f.write("Generated files:\n")
                f.write(f"- ITOL clade annotations: {clade_output.name}\n")
                f.write(f"- Nearest neighbor analysis: {nn_output.name}.pairs\n")
                f.write(f"- Query genome list: {query_list_file.name}\n\n")
                f.write("Instructions:\n")
                f.write("1. Upload your tree file to https://itol.embl.de/\n")
                f.write("2. Use the ITOL annotation files to highlight query clades\n")
                f.write("3. Check the nearest neighbor file for phylogenetic relationships\n")

            self.logger.info(f"Tree analysis completed. Results in: {itol_dir}")

        except Exception as e:
            self.logger.warning(f"Tree analysis failed: {str(e)}. Core functionality unaffected.")

    def _cleanup_and_compress(self, outdir, analysisname):
        """Clean up and compress results"""
        analyses_dir = outdir / "analyses"

        # Remove temporary directories
        temp_dirs = ["reformatted_faa", "tmp"]
        for temp_dir in temp_dirs:
            temp_path = analyses_dir / temp_dir
            if temp_path.exists():
                shutil.rmtree(temp_path)

        # Remove empty files
        for root, dirs, files in os.walk(analyses_dir):
            for file in files:
                file_path = Path(root) / file
                try:
                    if file_path.stat().st_size == 0:
                        file_path.unlink()
                except:
                    pass  # Skip files that can't be accessed

        # Compress analyses directory
        output_archive = outdir / "analyses.tar.gz"
        cleanup.main([str(analyses_dir), str(output_archive)])


def main():
    """Main entry point for NSGTree"""
    parser = argparse.ArgumentParser(
        description="NSGTree: Build genome tree from concatenated alignment after hmmsearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  nsgtree --qfaadir example --models resources/models/rnapol.hmm
  nsgtree --qfaadir example_q --rfaadir example_r --models resources/models/UNI56.hmm --config user_config.yml
  nsgtree --qfaadir example --models resources/models/rnapol.hmm --interactive  # Enable confirmation prompts
        """
    )

    parser.add_argument('--qfaadir', required=True,
                       help='Directory containing query FAA files')
    parser.add_argument('--models', required=True,
                       help='Path to HMM models file')
    parser.add_argument('--rfaadir',
                       help='Directory containing reference FAA files (optional)')
    parser.add_argument('--config',
                       help='User configuration file (YAML format)')
    parser.add_argument('--cores', type=int, default=8,
                       help='Number of CPU cores to use (default: 8)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Enable interactive mode with confirmation prompts (default: False, runs automatically)')
    parser.add_argument('--force-new', action='store_true',
                       help='Force a new analysis instead of resuming existing incomplete analysis')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle interactive mode
    if args.interactive:
        print("\nNSGTree Analysis Configuration:")
        print(f"  Query directory: {args.qfaadir}")
        print(f"  Models file: {args.models}")
        if args.rfaadir:
            print(f"  Reference directory: {args.rfaadir}")
        print(f"  CPU cores: {args.cores}")
        if args.config:
            print(f"  Config file: {args.config}")

        response = input("\nProceed with analysis? [y/N]: ").lower()
        if response != 'y' and response != 'yes':
            print("Analysis cancelled.")
            sys.exit(0)

    # Update config with command line arguments
    workflow = NSGTreeWorkflow(user_config_file=args.config)

    # Override CPU settings if specified
    if args.cores:
        workflow.config['hmmsearch_cpu'] = str(args.cores)
        workflow.config['extract_processes'] = str(args.cores)
        workflow.config['tree_cpus'] = str(args.cores)

    try:
        result_dir = workflow.run_workflow(
            qfaadir=args.qfaadir,
            models=args.models,
            rfaadir=args.rfaadir,
            force_new=args.force_new
        )
        print(f"NSGTree analysis completed successfully!")
        print(f"Results saved to: {result_dir}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
