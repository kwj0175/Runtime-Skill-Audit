# Skill Corpus

This directory now keeps a single self-contained experiment set:

- `balanced_200/`
- `balanced_100/`

`balanced_200` contains:

- `150` likely benign OpenClaw skills
- `50` malicious OpenClaw skills
- no symlinks; every skill directory is stored locally in place
- local manifests under `balanced_200/manifests/`

`balanced_100` contains:

- `50` likely benign OpenClaw skills
- `50` malicious OpenClaw skills
- no symlinks; every skill directory is stored locally in place
- local manifests under `balanced_100/manifests/`

The earlier staging directories used for downloading, sampling, and filtering upstream sources were removed after materializing the final corpora. Use the `balanced_100` or `balanced_200` subdirectory directly depending on which benchmark slice you want to run.
