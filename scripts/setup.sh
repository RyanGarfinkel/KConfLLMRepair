# Cloning Repositories
echo "Cloning repositories..."

# Z3
git clone --branch z3-4.8.17 --depth 1 https://github.com/Z3Prover/z3.git

# Linux Kernel
git clone git://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git kernel

# Syzkaller
git clone https://github.com/google/syzkaller.git

echo "Cloning completed."

# Build Docker container
echo "Building docker container..."

docker build -t kconf-llm-repair .

echo "Docker container built successfully."
