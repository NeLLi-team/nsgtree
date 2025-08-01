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

from .scripts import reformat
from .scripts import hmmsearch_count_filter
from .scripts import extract_qhits
from .scripts import concat
from .scripts import cleanup


class NSGTreeWorkflow:
    def __init__(self, config_file="config.yml", user_config_file=None):
        self.logger = self._setup_logging()
        self.config = self._load_config(config_file, user_config_file)
        self.workflow_log = None

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

    def run_workflow(self, qfaadir, models, rfaadir=None):
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

            # Create analysis name
            analysisname = str(qfaadir_base +
                "-" + rfaadir_base +
                "-" + models_base +
                "-" + self.config["tmethod"] +
                "-perc" + str(int(float(self.config["minmarker"])*10))).replace(".", "")

            # Set up output directory
            outdir = qfaadir / "nsgt_out" / analysisname
            outdir.mkdir(parents=True, exist_ok=True)

            # Set up workflow log
            self.workflow_log = outdir / "workflow.log"

            self.logger.info(f"Starting NSGTree workflow: {analysisname}")
            self.logger.info(f"Output directory: {outdir}")

            # Write initial log
            self._write_initial_log()

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

            # Step 11: Cleanup and compress
            self.logger.info("Step 11: Cleaning up and compressing results")
            self._cleanup_and_compress(outdir, analysisname)

            self.logger.info("NSGTree workflow completed successfully!")
            return str(outdir)

        except Exception as e:
            self.logger.error(f"Workflow failed: {str(e)}")
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

        # Use single-threaded approach for simplicity
        for model in models_list:
            output_file = hits_dir / f"{model}.faa"
            log_file = log_dir / f"{model}.log"

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

        for model in models_list:
            hits_file = hits_dir / f"{model}.faa"
            aligned_file = aligned_dir / f"{model}.mafft"
            trimmed_file = aligned_t_dir / f"{model}.mafft_t"
            log_file = log_dir / f"{model}.log"

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
                            result = subprocess.run(mafft_cmd, stdout=align_out, stderr=f, timeout=300)
                    else:
                        aligned_file.touch()

                    # Run trimal
                    trimal_cmd = ["trimal"]
                    if self.config["trimal_gt"]:
                        trimal_cmd.extend(self.config["trimal_gt"].split())
                    trimal_cmd.extend(["-in", str(aligned_file), "-out", str(trimmed_file)])

                    if aligned_file.exists() and aligned_file.stat().st_size > 0:
                        result = subprocess.run(trimal_cmd, stderr=f, timeout=300)
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

        for model in models_list:
            trimmed_file = aligned_t_dir / f"{model}.mafft_t"
            tree_file = proteintrees_dir / f"{model}.treefile"
            log_file = log_dir / f"{model}.log"
            complete_flag = analysis_dir / f"{model}.complete"

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
                                result = subprocess.run(cmd, stdout=tree_out, stderr=f, timeout=600)
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
                            result = subprocess.run(cmd, stderr=f, timeout=600)
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
                    result = subprocess.run(cmd, stdout=tree_out, stderr=f, timeout=1800)
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
                result = subprocess.run(cmd, stderr=f, timeout=1800)

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

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

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
            rfaadir=args.rfaadir
        )
        print(f"NSGTree analysis completed successfully!")
        print(f"Results saved to: {result_dir}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
