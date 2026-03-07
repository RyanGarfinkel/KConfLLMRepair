Core:
- [x] Make sh script to build kernel
- [x] Make sh script to run klocalizer
- [x] Make sh script to run QEMU
- [x] Move signal code from src/scripts/sample.py to KernelRepo class
- [x] Review ccache to speed up kernel builds
- [x] Configure JOBS property in settings
- [x] Setup multithreading, taking into consideration memory available (worktree crash)
- [x] Add max threads option for multithreading
- [x] Pipe logs to file for multithreading with more than 1 thread
- [x] Config refactoring to use nested options
- [x] KernelRepo -> Worktree.
- [x] Make src property in Kernel?
- [x] Make src.scripts -> src.cli
- [ ] Reintroduce repair with patch files (original + patch + modified -> KBootRepair)
- [ ] Cross compile

Sample Generation/Repair:
- [x] Move base config to sample directory
- [x] Generate the base config from syz-kconf tool
- [x] Make sampling end date a parameter.
- [ ] Pipe terminal output for > 1 samples in terminal log.
- [ ] Auto upload results to google drive (for experiment.py).
- [ ] Experiment --skip-generation bug fix.

Agent:
- [x] Make runner file with options: n, model-override, max-iterations.
- [x] Direct result output to summary.csv and/or JSON.
- [x] Create result extractor for agent run metadata.
- [x] Upate prompt to encoruage LLM to search for more than one string.
- [x] Update readme with llm how to use information.
- [x] Delete agent_response.json extra output (previously used for testing).
- [x] Record token usage.
- [x] Move final config to agent-repair-attempts directory.
- [x] Create summary.json to summarize all attempts.
- [x] Log info inbetween attempts in case of crash.
- [ ] AgentResponse define/undefine should be renamed to include/exclude.
- [ ] Cleanup console output.
- [ ] Adjust tool call limit.
