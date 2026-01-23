Core:
- [x] Make sh script to build kernel
- [x] Make sh script to run klocalizer
- [x] Make sh script to run QEMU
- [x] Move signal code from src/scripts/sample.py to KernelRepo class
- [x] Review ccache to speed up kernel builds
- [x] Configure JOBS property in settings
- [x] Setup multithreading, taking into consideration memory available (worktree crash)
- [x] Add max threads option for multithreading
- [ ] Pipe logs to file for multithreading with more than 1 thread
- [x] Config refactoring to use nested options
- [ ] KernelRepo -> Worktree.
- [ ] Make src property in Kernel?
- [ ] Make src.scripts -> src.cli

Sample Generation:
- [x] Move base config to sample directory
- [x] Generate the base config from syz-kconf tool
- [ ] Incorporate dispatcher into repair_samples.py. Pipe terminal output to log file.
- [x] Make sampling end date a parameter.

LLM:
- [x] Make runner file with options: n, model-override, max-iterations
- [x] Direct result output to summary.csv and/or JSON
- [ ] Create result extractor for agent run metadata
- [x] Upate prompt to encoruage LLM to search for more than one string
- [ ] Cleanup console output
- [x] Update readme with llm how to use information
- [ ] Delete agent_response.json extra output (previously used for testing)
- [ ] Record token usage
- [x] Move final config to agent-repair-attempts directory.
- [ ] Create summary.json to summarize all attempts.
- [ ] Log info inbetween attempts in case of crash.
