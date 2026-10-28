# OpenSandbox Sandbox Environment Images

English | [中文](README_zh.md)

This repository contains the standalone Docker build files, runtime scripts, test suites, and CI/release workflows for OpenSandbox sandbox environment images. Currently, the Code Interpreter (`code-interpreter`) environment is supported. The image is based on `Ubuntu 24.04` and comes pre-installed with multiple mainstream programming languages and multi-version environments, designed to provide an out-of-the-box multi-language code execution sandbox.

## Provenance & Upstream Origin

- **Upstream Origin**: Extracted from the `sandboxes/code-interpreter` directory of the core [OpenSandbox](https://github.com/opensandbox-group/OpenSandbox) monorepo at commit [`4e69fc5fe478651b2e297d38a06d6ddeb805795e`](https://github.com/opensandbox-group/OpenSandbox/commit/4e69fc5fe478651b2e297d38a06d6ddeb805795e) (tracked in [issue #1764](https://github.com/opensandbox-group/OpenSandbox/issues/1764)).
- **History Preservation**: Full commit history has been preserved (commit SHAs were rewritten during root extraction, but original author metadata, commit messages, and change chronology are preserved).
- **Ecosystem Links**: Currently, this repository builds, tests, and publishes the `code-interpreter` and `code-interpreter-base` images. It works alongside:
  - [OpenSandbox Core Repository](https://github.com/opensandbox-group/OpenSandbox)
  - [OpenSandbox API Specifications](https://github.com/opensandbox-group/OpenSandbox/tree/main/specs)
  - [OpenSandbox SDKs](https://github.com/opensandbox-group/OpenSandbox/tree/main/sdks)
  - [OpenSandbox Documentation](https://open-sandbox.ai)

## Features

- **Multi-Language Support**: Pre-installed Python, Java, Node.js, and Go with multiple versions
- **Version Switching**: Easy runtime version switching without rebuilding via `/opt/code-interpreter/code-interpreter-env.sh`
- **Jupyter Integration**: Built-in Jupyter Notebook server with pre-configured multi-language kernels
- **Multi-Architecture**: Native support for both `linux/amd64` and `linux/arm64`
- **clone3-workaround (amd64)**: Pre-installs [AkihiroSuda/clone3-workaround](https://github.com/AkihiroSuda/clone3-workaround) v1.0.0 as `/usr/local/bin/clone3-workaround` on **linux/amd64** only, along with `libseccomp2`. Useful on legacy Docker/containerd hosts.
- **Independent Build & Release**: Can independently build base and main images, test locally without credentials, and publish signed multiarch images.

## Supported Languages & Versions

The image comes pre-installed with the following languages and versions:

| Language    | Supported Versions            | Installation Path      | Notes                                    |
|:------------|:------------------------------|:-----------------------|:-----------------------------------------|
| **Python**  | 3.10, 3.11, 3.12, 3.13, 3.14* | `/opt/python/versions` | Installed via `uv`; 3.14 is experimental |
| **Java**    | 8, 11, 17, 21                 | `/usr/lib/jvm`         | OpenJDK; includes Maven 3.9.2            |
| **Node.js** | v18, v20, v22                 | `/opt/node`            | Official Linux binaries                  |
| **Go**      | 1.23, 1.24, 1.25              | `/opt/go`              | Official Linux binaries                  |

*> Note: Version numbers may be updated to latest patch releases at build time.*

## Quick Start

### 1. Build the Images Locally

Use `build.sh` to build both `code-interpreter-base` and `code-interpreter` locally and load them into your Docker daemon:

```bash
# Build base image, then main image using that newly built base (loaded into local Docker)
./build.sh

# Or specify a custom tag
TAG=my-dev-build ./build.sh
```

You can also build the main `Dockerfile` directly with standard `docker build`. The `BASE_IMAGE` build argument defaults to `opensandbox/code-interpreter-base:latest`:

```bash
# Build using default base image
docker build -t opensandbox/code-interpreter:latest .

# Build with a custom or local base image
docker build --build-arg BASE_IMAGE=opensandbox/code-interpreter-base:my-dev-build \
  -t opensandbox/code-interpreter:my-dev-build .
```

### 2. Run the Container

**Default startup:**

```bash
docker run -d --name code-interpreter opensandbox/code-interpreter:latest
```

> **Note on Port Exposure**: By default, Jupyter Notebook listens on container loopback (`127.0.0.1:44771`) as an internal service for OpenSandbox and `execd`. Host `-p` port mapping does not expose loopback services to the host. Access kernels through OpenSandbox/execd. A standalone container generates a fresh token on startup; server information and logs are stored in an owner-only `/tmp/opensandbox-jupyter.*` directory.

**With Custom Language Version Selection:**

```bash
docker run -it --rm \
  -e PYTHON_VERSION=3.11 \
  -e JAVA_VERSION=17 \
  -e NODE_VERSION=20 \
  -e GO_VERSION=1.24 \
  opensandbox/code-interpreter:latest
```

### `EXECD_CLONE3_COMPAT` (clone3-workaround)

If you set `EXECD_CLONE3_COMPAT` to `1`, `true`, `yes`, `on`, or `reexec` (compatible with [OpenSandbox execd](https://github.com/opensandbox-group/OpenSandbox/blob/main/components/execd/README.md#linux-clone3-compatibility-inside-sandboxes)), the entrypoint script **re-executes itself** under `/usr/local/bin/clone3-workaround` before Jupyter and kernel setup. That binary is included on **linux/amd64** only; on **arm64** builds the script prints a warning and continues without wrapping. After a successful wrap, the script **unsets** `EXECD_CLONE3_COMPAT` in the running process tree. Use `0`, `false`, `off`, `no`, or leave unset to disable.

## Version Switching

The image includes a built-in version switching script `/opt/code-interpreter/code-interpreter-env.sh`. Use the `source` command to load it into the current shell:

### Basic Usage

```bash
source /opt/code-interpreter/code-interpreter-env.sh <language> <version>
```

### Examples

**Switch Python Version:**

```bash
source /opt/code-interpreter/code-interpreter-env.sh python 3.11
python3 --version
```

**Switch Java Version:**

```bash
source /opt/code-interpreter/code-interpreter-env.sh java 8
java -version
```

**Switch Node.js Version:**

```bash
source /opt/code-interpreter/code-interpreter-env.sh node 22
node -v
```

**Switch Go Version:**

```bash
source /opt/code-interpreter/code-interpreter-env.sh go 1.25
go version
```

### List Available Versions

If you don't specify a version number, the script will list all available versions installed in the current image:

```bash
source /opt/code-interpreter/code-interpreter-env.sh python
source /opt/code-interpreter/code-interpreter-env.sh java
source /opt/code-interpreter/code-interpreter-env.sh node
source /opt/code-interpreter/code-interpreter-env.sh go
```

## Default Versions

The default versions when the container starts:

- **Python**: 3.14
- **Java**: 21
- **Node.js**: 22
- **Go**: 1.25

## Jupyter Notebook Integration

### Available Kernels

The image comes with pre-configured Jupyter kernels for all supported languages:

- **Python**: ipykernel for installed Python versions
- **Java**: IJava kernel
- **TypeScript/JavaScript**: tslab kernel (`tslab` and `jslab`)
- **Go**: gonb kernel
- **Bash**: bash_kernel

### Starting Jupyter

The entrypoint automatically starts Jupyter:

```bash
/opt/code-interpreter/code-interpreter.sh
```

### Environment Variables

- `JUPYTER_HOST`: Jupyter server host (default: `http://127.0.0.1:44771`)
- `JUPYTER_PORT`: Jupyter server port (default: `44771`)
- `JUPYTER_TOKEN`: Optional access token shared with `execd`. When absent or empty, standalone Jupyter generates a fresh random token. The token is loaded from the environment, removed before kernels are started, and never passed on the command line.

Use this image with an `execd` release that discovers the standalone token from `/tmp/opensandbox-jupyter.*/jpserver-*.json`. When upgrading the image while keeping an older `execd` that does not discover runtime tokens, explicitly supply a randomly generated `JUPYTER_TOKEN` at sandbox creation; otherwise they cannot authenticate to each other. Existing explicitly configured tokens continue to work. Rebuild derived images to remove any inherited fixed token, and pass `--config=/opt/code-interpreter/jupyter_notebook_config.py` if invoking `jupyter notebook` directly.

These credentials protect the internal Jupyter service from other Unix users. Processes running as the service owner, including root kernels, are still inside the same trust boundary; use separate sandboxes for mutually untrusted tenants.

## Build Workflow & Configuration

The `./build.sh` script automates building both base and main images sequentially using standard environment variables.

### Build Modes

1. **Local Single-Platform Build** (default):
   ```bash
   ./build.sh
   # or with custom tag:
   TAG=my-tag ./build.sh
   ```
   Uses the default Docker daemon buildx driver with `--load` so the main image immediately resolves the newly built base image locally.

2. **Multi-Architecture Release Publishing**:
   ```bash
   PUSH=true TAG=v1.0.0 ./build.sh
   ```
   Builds `code-interpreter-base` for `linux/amd64,linux/arm64`, pushes it to registries, extracts its immutable digest from build metadata, and builds `code-interpreter` referencing `opensandbox/code-interpreter-base@<digest>` with multiarch `--push`.

### Environment Variables

| Variable | Default | Description |
|:---|:---|:---|
| `TAG` | `latest` | Tag for the built images |
| `PUSH` | `false` | Explicitly set to `true` for release publishing |
| `PLATFORMS` | Empty (host) on local; `linux/amd64,linux/arm64` on publish | Target platform(s) |
| `GHCR_REPO` | `""` | Optional GHCR prefix (e.g. `ghcr.io/opensandbox-group/opensandbox`) |
| `BUILD_METADATA_FILE` | `build/code-interpreter-image-metadata.json` | Main image metadata JSON destination |
| `BASE_BUILD_METADATA_FILE` | `build/code-interpreter-base-image-metadata.json` | Base image metadata JSON destination |

### Published Image Coordinates

When publishing releases (`PUSH=true`), images are tagged and pushed to:

- **Main Image (`code-interpreter`)**:
  - Docker Hub: `docker.io/opensandbox/code-interpreter:<tag>`
  - Alibaba Cloud ACR: `sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:<tag>`
  - GitHub Packages (GHCR): `ghcr.io/opensandbox-group/opensandbox/code-interpreter:<tag>`
- **Base Image (`code-interpreter-base`)**:
  - Docker Hub: `docker.io/opensandbox/code-interpreter-base:<tag>`
  - Alibaba Cloud ACR: `sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter-base:<tag>`
  - GitHub Packages (GHCR): `ghcr.io/opensandbox-group/opensandbox/code-interpreter-base:<tag>`

## Verification & Testing

### Running Tests Locally

1. **Node Setup Regression Test**:
   ```bash
   bash tests/test_code_interpreter_node_setup.sh
   ```

2. **Shell Syntax & Linting**:
   ```bash
   for f in build.sh scripts/*.sh tests/*.sh scripts/release/*.sh; do bash -n "$f"; done
   shellcheck build.sh tests/*.sh scripts/release/*.sh
   ```

3. **Reusable Image Smoke Test**:
   ```bash
   ./tests/smoke_test.sh opensandbox/code-interpreter:latest
   ```
   The smoke test covers standalone random credentials and an explicitly configured token. It checks that another Unix user cannot read the token or log, that missing and former default tokens are rejected, and that kernels do not inherit `JUPYTER_TOKEN`. It also checks HTTP availability, installed kernelspecs, and real WebSocket execution for Python (including state persistence), Java, jslab, tslab, gonb, and Bash.

## Continuous Integration (CI)

The repository CI workflow (`.github/workflows/ci.yml`) runs on pushes and pull requests:

1. **Lint & Regression Tests**:
   - `shellcheck` static analysis
   - Per-file `bash -n` syntax check across all scripts
   - `python3 -m py_compile` check on Python files
   - Node setup regression test (`tests/test_code_interpreter_node_setup.sh`)
2. **Build & Kernel Smoke Test**:
   - Runs on native `amd64` (`ubuntu-latest`) and native `arm64` (`ubuntu-24.04-arm`) GitHub runners. Both architectures must pass.
   - Builds `code-interpreter-base` then `code-interpreter` locally from source with `--load`.
   - Runs `./tests/smoke_test.sh` asserting real WebSocket execution across all 6 kernel types.
   - Requires zero secrets and performs no registry push.

## Release Process & Security

### Release Triggering & Semver Policy

- **Explicit Tags**: Releases are published by pushing a tag matching `vX.Y.Z` (e.g. `v1.0.0`, with optional prerelease suffix `v1.0.0-rc.1`) or manually triggering `workflow_dispatch` on an existing version tag.
- **No Automatic `:latest`**: Release workflows publish only the explicit semantic version tag. No mutable public `:latest` tags are overwritten as part of the migration.
- **Tag Validation & Preflight**: Preflight validates that the git ref is a semantic version tag and verifies commit reachability from `origin/main` (`scripts/release/verify-release-ref.sh`) before release approval or build.
- **Concurrency**: Concurrency is locked to `group: release, cancel-in-progress: false` to prevent overlapping deployments.

### Required Repository Secrets & Environment

1. **Repository Secrets**:
   - `DOCKERHUB_USERNAME`, `DOCKERHUB_PASSWORD`: Docker Hub credentials
   - `ACR_USERNAME`, `ACR_PASSWORD`: Alibaba Cloud Container Registry credentials
2. **GHCR Permissions**:
   - Uses `GITHUB_TOKEN` with `packages: write` permission. Existing GHCR packages must also grant this repository Actions write access.
3. **Protected Environment**:
   - A GitHub Environment named `release` must be configured with required reviewers to approve releases.

### Sigstore Keyless Signing & Provenance

Release images are signed with Sigstore Cosign using GitHub Actions OIDC identity:

- **Signer Workflow Identity**:
  - Issuer: `https://token.actions.githubusercontent.com`
  - Workflow Ref: `https://github.com/opensandbox-group/sandbox-images/.github/workflows/release.yml@refs/tags/<version>`

- **Cosign Verification**:
  ```bash
  cosign verify \
    --certificate-identity-regexp '^https://github\.com/opensandbox-group/sandbox-images/\.github/workflows/release\.yml@refs/tags/v[0-9]+\.[0-9]+\.[0-9]+' \
    --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
    docker.io/opensandbox/code-interpreter:v1.0.0
  ```

- **GitHub Attestation Verification**:
  ```bash
  gh attestation verify oci://docker.io/opensandbox/code-interpreter:v1.0.0 \
    --repo opensandbox-group/sandbox-images
  ```

> **Historical Note**: Images published prior to repository extraction (e.g., `v1.1.0` or earlier) were signed under the upstream monorepo workflow identity (`opensandbox-group/OpenSandbox/.github/workflows/publish-components.yml`). Releases from this repository onward carry the `opensandbox-group/sandbox-images` identity.

### Monorepo Consumption & Version Pinning

The core OpenSandbox repository consumes `code-interpreter` releases by updating component image references (in server configs, Kubernetes manifests, or Helm charts) to point to specific released tags or image digests.

## Repository Structure

```
.
├── .github/
│   └── workflows/
│       ├── ci.yml                      # CI: lint, regression, native dual-arch build & smoke test
│       ├── release-preflight.yml       # Release semver validation, preflight & approval gate
│       └── release.yml                 # Multiarch build, push, cosign sign & attest
├── scripts/
│   ├── code-interpreter-env.sh         # Language runtime version switching script
│   ├── code-interpreter.sh             # Container entrypoint and Jupyter startup
│   ├── jupyter_notebook_config.py      # Jupyter server configuration
│   └── release/
│       └── verify-release-ref.sh       # Preflight script verifying main ancestry
├── tests/
│   ├── smoke_test.sh                   # Reusable container smoke test runner
│   ├── smoke_test_kernels.py           # Kernel HTTP & WebSocket execution smoke test
│   └── test_code_interpreter_node_setup.sh # Node setup regression test
├── build.sh                            # Standalone build script (base + main)
├── Dockerfile                          # Main image Dockerfile
├── Dockerfile.dockerignore             # Dockerignore for main image
├── Dockerfile_base                     # Base image Dockerfile
├── Dockerfile_base.dockerignore        # Dockerignore for base image
├── LICENSE                             # Apache 2.0 License
├── README.md                           # English documentation
└── README_zh.md                        # Chinese documentation
```

## License

This project is licensed under the [Apache License, Version 2.0](LICENSE).

## Support & Contributing

- **Issues & Discussions**: [sandbox-images Issues](https://github.com/opensandbox-group/sandbox-images/issues)
- **Core Repository**: [opensandbox-group/OpenSandbox](https://github.com/opensandbox-group/OpenSandbox)
