#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

IMAGE="${1:-opensandbox/code-interpreter:latest}"
CONTAINER_NAME="code-interpreter-smoke-${$}-${RANDOM}"

cleanup() {
  echo "==> Cleaning up smoke test container ${CONTAINER_NAME}..."
  docker logs "${CONTAINER_NAME}" >/tmp/smoke-test-container.log 2>&1 || true
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for mode in standalone configured; do
  echo "==> Starting ${mode} container ${CONTAINER_NAME} using image ${IMAGE}..."
  if [ "${mode}" = configured ]; then
    JUPYTER_TOKEN=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    export JUPYTER_TOKEN
    docker run -d --name "${CONTAINER_NAME}" -e JUPYTER_TOKEN "${IMAGE}" >/dev/null
    unset JUPYTER_TOKEN
  else
    docker run -d --name "${CONTAINER_NAME}" "${IMAGE}" >/dev/null
  fi
  docker cp "${REPO_ROOT}/tests/smoke_test_kernels.py" "${CONTAINER_NAME}:/tmp/smoke_test_kernels.py"
  docker exec "${CONTAINER_NAME}" bash -c \
    'source /opt/code-interpreter/code-interpreter-env.sh python "${PYTHON_VERSION}" && python3 /tmp/smoke_test_kernels.py'
  cleanup
done
trap - EXIT

echo "==> Reusable image smoke test completed successfully!"
