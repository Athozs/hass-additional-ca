#!/usr/bin/env bash

set -xe

cd "$(dirname "$0")/.."

mkdir -p config/additional_ca

cp -rv custom_components config/

docker compose -f compose_dev.yml up --force-recreate --remove-orphans
