# OpenSandbox 沙箱环境镜像

中文 | [English](README.md)

本仓库包含 OpenSandbox 沙箱环境镜像的独立 Docker 构建文件、运行时脚本、测试套件以及 CI 与发布工作流。目前支持 Code Interpreter（`code-interpreter`）环境。该镜像基于 `Ubuntu 24.04`，预装了多种主流编程语言及其多版本环境，旨在提供一个开箱即用的多语言代码执行沙箱。

## 来源背景与上游追溯

- **上游来源**：从核心 [OpenSandbox](https://github.com/opensandbox-group/OpenSandbox) 单体仓库的 `sandboxes/code-interpreter` 目录独立拆分而来，对应提交为 [`4e69fc5fe478651b2e297d38a06d6ddeb805795e`](https://github.com/opensandbox-group/OpenSandbox/commit/4e69fc5fe478651b2e297d38a06d6ddeb805795e)（相关工作见 [Issue #1764](https://github.com/opensandbox-group/OpenSandbox/issues/1764)）。
- **历史保留**：完整保留了该模块的 Git 提交历史（根目录路径映射虽使提交 SHA 发生变化，但提交作者、提交信息及时间线完整保留）。
- **生态关联**：本仓库目前提供 `code-interpreter` 与 `code-interpreter-base` 镜像的独立构建、测试与发版，并与以下项目协同工作：
  - [OpenSandbox 主仓库](https://github.com/opensandbox-group/OpenSandbox)
  - [OpenSandbox API 规范](https://github.com/opensandbox-group/OpenSandbox/tree/main/specs)
  - [OpenSandbox SDKs](https://github.com/opensandbox-group/OpenSandbox/tree/main/sdks)
  - [OpenSandbox 官方文档](https://open-sandbox.ai)

## 特性

- **多语言支持**：预装 Python、Java、Node.js 和 Go 及其多个版本
- **版本切换**：无需重新构建，通过 `/opt/code-interpreter/code-interpreter-env.sh` 支持运行时快速切换环境版本
- **Jupyter 集成**：内置 Jupyter Notebook 服务并预配置各语言内核
- **多架构支持**：原生支持 `linux/amd64` 与 `linux/arm64` 架构
- **clone3-workaround（仅限 amd64）**：在 **linux/amd64** 镜像中预装 [AkihiroSuda/clone3-workaround](https://github.com/AkihiroSuda/clone3-workaround) v1.0.0 至 `/usr/local/bin/clone3-workaround`，并预装 `libseccomp2`，以便在极旧 Docker/containerd 宿主机上正常运行。
- **独立构建与发布**：支持无凭证的本地基础镜像与主镜像联调测试，支持多架构自动构建签名与发版。

## 支持的语言与版本

镜像内预置了以下语言和版本：

| 语言          | 支持版本                          | 安装路径                   | 备注                     |
|:------------|:------------------------------|:-----------------------|:-----------------------|
| **Python**  | 3.10, 3.11, 3.12, 3.13, 3.14* | `/opt/python/versions` | 使用 `uv` 安装；3.14 为实验性版本 |
| **Java**    | 8, 11, 17, 21                 | `/usr/lib/jvm`         | OpenJDK; 含 Maven 3.9.2 |
| **Node.js** | v18, v20, v22                 | `/opt/node`            | 官方 Linux 二进制包          |
| **Go**      | 1.23, 1.24, 1.25              | `/opt/go`              | 官方 Linux 二进制包          |

*> 注意: 版本号可能会随构建时间更新至小版本的最新版。*

## 快速开始

### 1. 本地构建镜像

使用 `build.sh` 脚本可顺序构建 `code-interpreter-base` 与 `code-interpreter`，并将镜像载入本地 Docker 守护进程：

```bash
# 依次构建基础镜像与主镜像（使用刚刚构建好的本地基础镜像）
./build.sh

# 或指定自定义标签
TAG=my-dev-build ./build.sh
```

也可以直接使用标准 `docker build` 构建主镜像，Dockerfile 支持 `BASE_IMAGE` 参数（默认值保持向下兼容）：

```bash
# 使用默认基础镜像构建
docker build -t opensandbox/code-interpreter:latest .

# 使用指定基础镜像构建
docker build --build-arg BASE_IMAGE=opensandbox/code-interpreter-base:my-dev-build \
  -t opensandbox/code-interpreter:my-dev-build .
```

### 2. 运行容器

**默认启动：**

```bash
docker run -d --name code-interpreter opensandbox/code-interpreter:latest
```

> **关于端口暴露的说明**：Jupyter Notebook 默认仅监听容器回环地址（`127.0.0.1:44771`），专供 OpenSandbox 和 `execd` 内部调用。宿主机 `-p` 端口映射无法直接访问该内部回环服务。请通过 OpenSandbox SDK 或 execd 运行时访问内核。独立启动的容器会生成随机令牌，服务信息和日志保存在仅属主可访问的 `/tmp/opensandbox-jupyter.*` 目录。

**指定运行时语言版本：**

```bash
docker run -it --rm \
  -e PYTHON_VERSION=3.11 \
  -e JAVA_VERSION=17 \
  -e NODE_VERSION=20 \
  -e GO_VERSION=1.24 \
  opensandbox/code-interpreter:latest
```

### `EXECD_CLONE3_COMPAT`（clone3-workaround）

若将 `EXECD_CLONE3_COMPAT` 设为 `1`、`true`、`yes`、`on` 或 `reexec`（与 [OpenSandbox execd](https://github.com/opensandbox-group/OpenSandbox/blob/main/components/execd/README.md#沙箱内的-linux-clone3-兼容) 行为一致），入口脚本会在启动 Jupyter/内核前使用 **`/usr/local/bin/clone3-workaround` 重新 `exec` 自身**。**linux/amd64** 镜像内置该二进制；**arm64** 构建会打印警告并跳过包装。包装成功后脚本会在当前进程树中 **`unset` `EXECD_CLONE3_COMPAT`**。设为 `0`、`false`、`off`、`no` 或不设置则关闭此功能。

## 如何切换版本

镜像内置了环境切换脚本 `/opt/code-interpreter/code-interpreter-env.sh`，使用 `source` 命令加载它以修改当前 Shell 的环境变量：

### 基本用法

```bash
source /opt/code-interpreter/code-interpreter-env.sh <language> <version>
```

### 示例

**切换 Python 版本：**

```bash
source /opt/code-interpreter/code-interpreter-env.sh python 3.11
python3 --version
```

**切换 Java 版本：**

```bash
source /opt/code-interpreter/code-interpreter-env.sh java 8
java -version
```

**切换 Node.js 版本：**

```bash
source /opt/code-interpreter/code-interpreter-env.sh node 22
node -v
```

**切换 Go 版本：**

```bash
source /opt/code-interpreter/code-interpreter-env.sh go 1.25
go version
```

### 查看可用版本

如果不指定版本号，脚本会列出当前镜像内已安装的所有可用版本：

```bash
source /opt/code-interpreter/code-interpreter-env.sh python
source /opt/code-interpreter/code-interpreter-env.sh java
source /opt/code-interpreter/code-interpreter-env.sh node
source /opt/code-interpreter/code-interpreter-env.sh go
```

## 默认版本

容器启动时的默认版本配置如下：

- **Python**: 3.14
- **Java**: 21
- **Node.js**: 22
- **Go**: 1.25

## Jupyter Notebook 集成

### 可用内核

镜像预配置了所有支持语言的 Jupyter 内核：

- **Python**：已安装 Python 版本的 ipykernel
- **Java**：IJava 内核
- **TypeScript/JavaScript**：tslab 内核（包含 `tslab` 和 `jslab`）
- **Go**：gonb 内核
- **Bash**：bash_kernel

### 启动 Jupyter

入口脚本会自动启动 Jupyter Notebook 服务：

```bash
/opt/code-interpreter/code-interpreter.sh
```

### 环境变量

- `JUPYTER_HOST`：Jupyter 服务监听地址（默认：`http://127.0.0.1:44771`）
- `JUPYTER_PORT`：Jupyter 服务端口（默认：`44771`）
- `JUPYTER_TOKEN`：与 `execd` 共享的可选访问令牌。未设置或为空时，独立启动的 Jupyter 会生成随机令牌。配置从环境变量读取令牌，并在启动内核前将其移除；令牌不再出现在启动参数中。服务信息和日志保存在仅属主可访问的 `/tmp/opensandbox-jupyter.*` 目录。

此镜像应搭配支持从 `/tmp/opensandbox-jupyter.*/jpserver-*.json` 自动发现独立启动令牌的 `execd` 使用。如果只升级镜像、仍使用不支持自动发现令牌的旧版 `execd`，请在创建沙箱时显式传入随机生成的 `JUPYTER_TOKEN`，否则无法完成鉴权。显式配置的令牌继续生效；派生镜像需要重新构建以去掉继承的固定令牌，若直接调用 `jupyter notebook` 请显式传入 `--config=/opt/code-interpreter/jupyter_notebook_config.py`。

这些措施用于防止其他 Unix 用户直接访问内部 Jupyter 服务。与服务使用相同身份的进程（包括 root 内核）仍处于同一信任边界内；互不信任的租户应使用独立沙箱。

## 独立构建流程与配置

`./build.sh` 脚本通过标准环境变量驱动基础镜像与主镜像的顺序构建。

### 构建模式

1. **本地单架构构建**（默认）：
   ```bash
   ./build.sh
   # 或指定自定义标签：
   TAG=my-tag ./build.sh
   ```
   使用默认 Docker 守护进程 buildx 驱动配合 `--load`，使主镜像能够直接解析本地刚构建出的基础镜像。

2. **多架构发版推送**：
   ```bash
   PUSH=true TAG=v1.0.0 ./build.sh
   ```
   为 `linux/amd64,linux/arm64` 构建 `code-interpreter-base` 并推送，从构建元数据中提取不可变摘要（Digest），随后构建 `code-interpreter` 显式引用该版本化基础镜像 `opensandbox/code-interpreter-base@<digest>` 并推送。

### 环境变量说明

| 环境变量 | 默认值 | 说明 |
|:---|:---|:---|
| `TAG` | `latest` | 构建镜像的标签 |
| `PUSH` | `false` | 显式设为 `true` 时执行发版推送 |
| `PLATFORMS` | 本地单架构为空（主机架构）；推送时为 `linux/amd64,linux/arm64` | 目标构建平台 |
| `GHCR_REPO` | `""` | 可选 GHCR 仓库前缀（例如 `ghcr.io/opensandbox-group/opensandbox`） |
| `BUILD_METADATA_FILE` | `build/code-interpreter-image-metadata.json` | 主镜像元数据 JSON 输出路径 |
| `BASE_BUILD_METADATA_FILE` | `build/code-interpreter-base-image-metadata.json` | 基础镜像元数据 JSON 输出路径 |

### 发布镜像坐标

发版时（`PUSH=true`），镜像将推送到以下三个官方镜像仓库：

- **主镜像（`code-interpreter`）**：
  - Docker Hub: `docker.io/opensandbox/code-interpreter:<tag>`
  - 阿里云 ACR: `sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:<tag>`
  - GitHub Packages (GHCR): `ghcr.io/opensandbox-group/opensandbox/code-interpreter:<tag>`
- **基础镜像（`code-interpreter-base`）**：
  - Docker Hub: `docker.io/opensandbox/code-interpreter-base:<tag>`
  - 阿里云 ACR: `sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter-base:<tag>`
  - GitHub Packages (GHCR): `ghcr.io/opensandbox-group/opensandbox/code-interpreter-base:<tag>`

## 验证与测试

### 本地测试执行

1. **Node 环境适配回归测试**：
   ```bash
   bash tests/test_code_interpreter_node_setup.sh
   ```

2. **Shell 语法检查与 Lint**：
   ```bash
   for f in build.sh scripts/*.sh tests/*.sh scripts/release/*.sh; do bash -n "$f"; done
   shellcheck build.sh tests/*.sh scripts/release/*.sh
   ```

3. **可复用镜像冒烟测试**：
   ```bash
   ./tests/smoke_test.sh opensandbox/code-interpreter:latest
   ```
   冒烟测试覆盖独立启动时的随机令牌和显式配置的令牌，验证普通 Unix 用户无法读取令牌及日志、无令牌或旧默认令牌的请求被拒绝、内核不继承 `JUPYTER_TOKEN`。测试还会校验 HTTP 服务和已注册的语言内核，并通过 WebSocket 实际执行 Python（含同内核状态复用）、Java、jslab、tslab、gonb 与 Bash 代码。

## 持续集成（CI）

本仓库的 CI 工作流（`.github/workflows/ci.yml`）在代码推送及 PR 时触发：

1. **静态检查与回归测试**：
   - 使用 `shellcheck` 进行静态代码规范检查
   - 逐文件执行 `bash -n` 语法校验
   - 使用 `python3 -m py_compile` 校验 Python 脚本语法
   - 执行 Node 环境安装回归测试（`tests/test_code_interpreter_node_setup.sh`）
2. **构建与内核冒烟测试**：
   - 运行在 GitHub Actions 原生 `amd64`（`ubuntu-latest`）和原生 `arm64`（`ubuntu-24.04-arm`）运行器上，双架构均须完全通过。
   - 从源码构建 `code-interpreter-base` 并以 `--load` 构建 `code-interpreter`。
   - 执行 `./tests/smoke_test.sh`，断言全部 6 种内核的实际 WebSocket 执行能力。
   - 全程无需任何凭证，不向任何外部仓库推送。

## 发布流程与安全配置

### 发版触发与语义化版本策略

- **明确版本标签**：发版必须推送符合 `vX.Y.Z` 格式的 Git 标签（例如 `v1.0.0`，可带预发布后缀如 `v1.0.0-rc.1`）或在 GitHub Actions 手动针对已有版本标签触发 `workflow_dispatch`。
- **禁止自动发布 `:latest`**：发版工作流仅发布显式语义化版本标签，迁移阶段绝不自动覆盖生产环境 `:latest` 可变标签。
- **标签校验与主分支祖先校验**：前置工作流（`.github/workflows/release-preflight.yml`）会在发版审批或构建前，严格校验 Ref 必须为语义化版本标签，并使用 `scripts/release/verify-release-ref.sh` 验证提交是否可从 `origin/main` 追溯。
- **并发控制**：锁定为 `group: release, cancel-in-progress: false`，防止并发冲突发版。

### 所需仓库凭证与环境配置

1. **Repository Secrets**：
   - `DOCKERHUB_USERNAME`, `DOCKERHUB_PASSWORD`: Docker Hub 账号与 Token
   - `ACR_USERNAME`, `ACR_PASSWORD`: 阿里云容器镜像服务账号与密码
2. **GHCR 权限**：
   - 使用 `GITHUB_TOKEN` 配合 `packages: write` 权限推送到 GitHub Container Registry。已存在的 GHCR 包还需要向本仓库授予 Actions 写入权限。
3. **受保护的环境（Protected Environment）**：
   - 仓库内配置名为 `release` 的 Environment，由指定审核人批准发版。

### Sigstore Keyless 签名与来源证明

发布镜像通过 Sigstore Cosign 使用基于 GitHub Actions OIDC 的免密密钥签名：

- **工作流身份（Workflow Identity）**：
  - Issuer: `https://token.actions.githubusercontent.com`
  - Workflow Ref: `https://github.com/opensandbox-group/sandbox-images/.github/workflows/release.yml@refs/tags/<version>`

- **Cosign 签名校验**：
  ```bash
  cosign verify \
    --certificate-identity-regexp '^https://github\.com/opensandbox-group/sandbox-images/\.github/workflows/release\.yml@refs/tags/v[0-9]+\.[0-9]+\.[0-9]+' \
    --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
    docker.io/opensandbox/code-interpreter:v1.0.0
  ```

- **GitHub 来源证明校验**：
  ```bash
  gh attestation verify oci://docker.io/opensandbox/code-interpreter:v1.0.0 \
    --repo opensandbox-group/sandbox-images
  ```

> **历史签名说明**：在仓库拆分前发布的历史镜像（如 `v1.1.0` 或更早版本）由上游单体仓库工作流身份（`opensandbox-group/OpenSandbox/.github/workflows/publish-components.yml`）签名。从本仓库起发布的新镜像均带有 `opensandbox-group/sandbox-images` 身份。

### 主仓库版本固定方式

核心 [OpenSandbox](https://github.com/opensandbox-group/OpenSandbox) 仓库通过在其配置、Kubernetes 清单或 Helm 变量中显式固定外部发布的具体版本标签（如 `v1.0.0`）或镜像 Digest 来使用该镜像，无需跨仓库同步逻辑。

## 仓库结构

```
.
├── .github/
│   └── workflows/
│       ├── ci.yml                      # CI 工作流：静态检查、回归测试、双架构原生构建与冒烟测试
│       ├── release-preflight.yml       # 发版前置工作流：语义化版本校验、主分支可达性与环境审批
│       └── release.yml                 # 发版工作流：多架构构建推送、Cosign 签名与来源证明
├── scripts/
│   ├── code-interpreter-env.sh         # 语言版本运行时切换脚本
│   ├── code-interpreter.sh             # 容器入口脚本与 Jupyter 启动
│   ├── jupyter_notebook_config.py      # Jupyter 服务配置
│   └── release/
│       └── verify-release-ref.sh       # 发版提交追溯校验脚本
├── tests/
│   ├── smoke_test.sh                   # 可复用容器冒烟测试脚本
│   ├── smoke_test_kernels.py           # 内核 HTTP 与 WebSocket 执行冒烟测试
│   └── test_code_interpreter_node_setup.sh # Node 环境安装与内核注册回归测试
├── build.sh                            # 独立构建脚本（基础镜像 + 主镜像）
├── Dockerfile                          # 主镜像 Dockerfile
├── Dockerfile.dockerignore             # 主镜像忽略规则
├── Dockerfile_base                     # 基础镜像 Dockerfile
├── Dockerfile_base.dockerignore        # 基础镜像忽略规则
├── LICENSE                             # Apache 2.0 许可证
├── README.md                           # 英文文档
└── README_zh.md                        # 中文文档
```

## 许可证

本项目遵循 [Apache License, Version 2.0](LICENSE) 许可证。

## 支持与参与

- **Issue 与讨论**：[sandbox-images Issues](https://github.com/opensandbox-group/sandbox-images/issues)
- **核心主仓库**：[opensandbox-group/OpenSandbox](https://github.com/opensandbox-group/OpenSandbox)
