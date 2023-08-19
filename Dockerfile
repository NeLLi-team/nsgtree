FROM --platform=linux/amd64 snakemake/snakemake:latest

LABEL maintainer="Juan C. Villada <jvillada@lbl.gov>"
LABEL version="0.4.2"

WORKDIR /tmp/nsgtree

COPY . /tmp/nsgtree

ENV PATH=${PATH}:$HOME/nsgtree

# Pre-create all conda environments and pre-install all conda packages
RUN snakemake \
    --use-conda \
    --conda-create-envs-only \
    -j 4 \
    --config \
    qfaadir="/tmp/nsgtree/example" \
    models="/tmp/nsgtree/resources/models/rnapol.hmm" \
    --configfile "/tmp/nsgtree/user_config.yml"





