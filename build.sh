#!/usr/bin/env sh

echo "Setting VERSION='${CI_COMMIT_REF_NAME}-${CI_COMMIT_SHORT_SHA}' in src/constants.py"
sed -i '' -e "s/^VERSION.*/VERSION = '${CI_COMMIT_REF_NAME}-${CI_COMMIT_SHORT_SHA}'/g" src/constants.py
