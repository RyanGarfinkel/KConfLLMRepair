Core:
- [x] Make sh script to build kernel
- [x] Make sh script to run klocalizer
- [x] Make sh script to run QEMU
- [x] Move signal code from src/scripts/sample.py to KernelRepo class
- [ ] Review ccache to speed up kernel builds
- [x] Configure JOBS property in settings
- [ ] Setup multithreading, taking into consideration memory available (worktree crash)

LLM:
- [ ] Make runner file with options: n, model-override, max-iterations
- [ ] Direct result output to summary.csv and/or JSON
- [ ] Create result extractor for agent run metadata
- [ ] Upate prompt to encoruage LLM to search for more than one string
- [ ] Cleanup console output
- [x] Update readme with llm how to use information
