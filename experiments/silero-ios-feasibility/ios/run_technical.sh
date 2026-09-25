#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash ios/run_preprocessing.sh "${1:?Usage: bash ios/run_technical.sh SIMULATOR_UDID}" --technical
