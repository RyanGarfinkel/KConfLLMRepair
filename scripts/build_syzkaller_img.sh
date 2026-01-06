#!/bin/bash

set -e

# Build Syzkaller image
echo "Building Syzkaller image..."

sudo apt-get update
sudo apt-get install -y debootstrap

cd $SYZKALLER_SRC/tools
sudo ./create-image.sh

mv bullseye.img ~/bullseye.img

sudo chown $USER:$USER ~/bullseye.img

sudo rm -rf bullseye

echo 'export BULLSEYE_IMG=~/bullseye.img' >> ~/.bashrc
export BULLSEYE_IMG=~/bullseye.img

echo "Syzkaller image built successfully at $BULLSEYE_IMG"
echo ""
echo "Run the following command to run the kmax tools:"
echo "source ~/.bashrc"
