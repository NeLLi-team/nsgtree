FROM --platform=linux/amd64 snakemake/snakemake:latest

LABEL maintainer="Juan C. Villada <jvillada@lbl.gov>"

WORKDIR /app/nsgtree

COPY . /app/nsgtree

ENV PATH=${PATH}:/app/nsgtree

# Pre-create all conda environments and pre-install all conda packages
RUN snakemake \
    --use-conda \
    --conda-create-envs-only \
    -j 4 \
    --config \
    qfaadir="/app/nsgtree/example" \
    models="/app/nsgtree/resources/models/rnapol.hmm" \
    --configfile "/app/nsgtree/user_config.yml"





