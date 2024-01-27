#!/usr/bin/env bash

set -xe

cd "$(dirname "$0")/.."

mkdir -p config/additional_ca

rsync -ac --delete --exclude="__pycache__" custom_components config/

docker compose up --force-recreate --remove-orphans
