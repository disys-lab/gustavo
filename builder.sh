#!/usr/bin/env bash

VERSION=0.3.1

platform=""

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        platform="linux";
elif [[ "$OSTYPE" == "darwin"* ]]; then
        platform="osx";
elif [[ "$OSTYPE" == "cygwin" ]]; then
        platform="cygwin";
elif [[ "$OSTYPE" == "msys"* ]]; then
        platform="msys";
elif [[ "$OSTYPE" == "win32" ]]; then
        platform="win32";
elif [[ "$OSTYPE" == "freebsd"* ]]; then
        platform="freebsd";
else

  echo "Error: The OSTYPE could not be detected. Enter platform name to build (linux/osx/win32...)"
  read platform
fi

if [[ ! -d "dist" ]]; then
  echo "dist directory does not exist...creating"
  mkdir -p "dist"
fi

if [[ ! -d "dist/$platform" ]]; then
  echo "dist/$platform directory does not exist...creating"
  mkdir -p "dist/$platform"
fi

pyinstaller --exclude-module numpy \
            --exclude-module scipy \
            --exclude-module pandas \
            --exclude-module Tree \
            --exclude-module matplotlib \
            --exclude-module tkinter \
            --distpath "dist/$platform" \
            --onefile --clean gustavo.py
