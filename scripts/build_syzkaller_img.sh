#!/bin/bash

set -e

# Build Syzkaller image
echo "Building Syzkaller image..."

sudo apt-get update
sudo apt-get install -y debootstrap

cd $SYZKALLER_SRC/tools
sudo ./create-image.sh

sudo chown $USER:$USER trixie.img

echo 'export TRIXIE_IMG=$SYZKALLER_SRC/tools/trixie.img' >> ~/.bashrc
export TRIXIE_IMG=$SYZKALLER_SRC/tools/trixie.img

echo "Syzkaller image built successfully at $TRIXIE_IMG"
echo""
echo "Run the following command to run the kmax tools:"
echo "source ~/.bashrc"
