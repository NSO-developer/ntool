#!/bin/sh

FILES=../sample_configs/iosxr/*
for file in $FILES
do
echo "Processing ${file##*/}"
ncs_cli -u admin <<EOF
ntool verify type iosxr file ../sample_configs/iosxr/${file##*/} | save ../sample_configs_processed/iosxr/${file##*/}
EOF
done
