#!/bin/sh

FILES=../sample_configs/nxos/*
for file in $FILES
do
echo "Processing ${file##*/}"
ncs_cli -u admin <<EOF
ntool verify type nexus file ../sample_configs/nxos/${file##*/} | save ../sample_configs_processed/nxos/${file##*/}
EOF
done
