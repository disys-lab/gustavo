#!/bin/bash

platform=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        platform="linux";
elif [[ "$OSTYPE" == "darwin"* ]]; then
        platform="macosx";
else
  echo "Platform $platform unsupported"
  exit
fi

version=$1
if [ -n "${version}" ]; then

  rm -rf build
  yes| pip uninstall gustavo
  python setup.py bdist_wheel $version

  # Find files containing "gustavo" and "linux" in the name, sorted by modification time.
  latest_file=$(find ./dist/ -type f -iname "*gustavo*$platform*" | sort -n | tail -1 | cut -d' ' -f2-)

  # Check if a file was found
  if [ -z "$latest_file" ]; then
    echo "No file found containing 'gustavo' and '$platform' in the name."
  else
    echo "The latest file is: $latest_file"
  fi

  pip install $latest_file

else
  echo "Version unspecified"
fi