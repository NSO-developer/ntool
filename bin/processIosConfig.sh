#!/bin/sh

FILES=../sample_configs/ios/*
for file in $FILES
do
echo "Processing ${file##*/}"
ncs_cli -u admin <<EOF
ntool verify type ios file ../sample_configs/ios/${file##*/} | save ../sample_configs_processed/ios/${file##*/}
EOF
done
