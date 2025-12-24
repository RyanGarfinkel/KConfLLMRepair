# Cloning Repositories
echo "Cloning repositories..."

# SuperC
git clone https://github.com/appleseedlab/superc.git

# Z3
git clone https://github.com/Z3Prover/z3.git
cd z3
git checkout d95805b6311b357ce37417db24c9fc948dc8f772
cd ..

# Kmax
git clone https://github.com/paulgazz/kmax.git

# Linux Kernel
git clone git://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git kernel

# Syzkaller
# git clone https://github.com/google/syzkaller.git

echo "Cloning completed."

# Build Docker container
echo "Building docker container..."

docker build -t kconf-llm-repair .

echo "Docker container built successfully."
