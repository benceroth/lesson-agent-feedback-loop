# Security

## Scope

This is a teaching lab. It **executes code written by a model** (or by scripted scenarios) in local subprocesses with your user's privileges, and it can send task code to an HTTP endpoint you configure.

## Guidance

- Use the scripted provider (default) for CI and demos. It runs only code committed in this repo.
- For real models, run inside a container or VM without secrets, network access beyond the model endpoint, or mounted home directories.
- Keys come only from environment variables (`LOOP_API_KEY`). Never commit them. Provider errors never include the key or response bodies.
- `LOOP_BASE_URL` must be https, except for localhost. Prompts include task code; do not point the lab at endpoints you do not trust.
- The guard (allow-list, protected files, diff scope) prevents *reward hacking*, not malicious code. It is not a sandbox.

## Reporting

Report vulnerabilities privately through GitHub's "Report a vulnerability" (private security advisory) on this repository. Please do not open public issues for them.
