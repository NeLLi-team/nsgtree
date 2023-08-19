FROM --platform=linux/amd64 snakemake/snakemake:latest

LABEL maintainer="Juan C. Villada <jvillada@lbl.gov>"
LABEL version="0.4.2"
LABEL description="Container for nsgtree 🌲"
LABEL license="GPLv3"

WORKDIR /nsgtree

COPY . /nsgtree

ENV PATH=${PATH}:/nsgtree

# Pre-create all conda environments and pre-install all conda packages
RUN snakemake \
    --use-conda \
    --conda-create-envs-only \
    -j 4 \
    --config \
    qfaadir="/nsgtree/example" \
    models="/nsgtree/resources/models/rnapol.hmm" \
    --configfile "/nsgtree/user_config.yml"





