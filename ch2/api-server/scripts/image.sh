#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

TAG=$(uv version --short)
PYTHON_VERSION=$(tr -d '[:space:]' < .python-version)
IMAGE_NAME="api-server"
OUTPUT_DIR="out"
ARCHIVE_PATH="${OUTPUT_DIR}/${IMAGE_NAME}-${TAG}.tar.zst"
SIG_PATH="${ARCHIVE_PATH}.asc"
DEFAULT_KEY="${GPG_KEY:-${SIGN_KEY:-}}"

cmd_build() {
  local sign_key=""
  if [[ $# -gt 0 && "$1" != -* ]]; then
    sign_key="$1"
  else
    sign_key="${DEFAULT_KEY}"
  fi

  echo "Relabeling SELinux context for bind mounts..."
  chcon -t container_file_t uv.lock pyproject.toml 2>/dev/null || true

  echo "Building container image ${IMAGE_NAME}:${TAG} using Python ${PYTHON_VERSION}..."

  local build_opts=(--layers --build-arg PYTHON_VERSION="${PYTHON_VERSION}" -t "${IMAGE_NAME}:${TAG}")
  if [[ -n "${sign_key}" ]]; then
    echo "Signing container build commit with GPG key: ${sign_key}"
    build_opts+=(--sign-by "${sign_key}")
  fi

  buildah build "${build_opts[@]}" .

  echo "Successfully built ${IMAGE_NAME}:${TAG} and tagged as ${IMAGE_NAME}:latest"

  mkdir -p "${OUTPUT_DIR}"

  echo "Pushing image to OCI archive with zstd compression: ${ARCHIVE_PATH}..."

  buildah push \
    --compression-format zstd \
    "${IMAGE_NAME}:${TAG}" \
    "oci-archive:${ARCHIVE_PATH}"

  echo "Successfully exported OCI archive with zstd compression to ${ARCHIVE_PATH}"

  if [[ -n "${sign_key}" ]]; then
    cmd_sign "${sign_key}"
  fi
}

cmd_sign() {
  local key_id=""
  if [[ $# -gt 0 && "$1" != -* ]]; then
    key_id="$1"
  else
    key_id="${DEFAULT_KEY}"
  fi

  if [[ -z "${key_id}" ]]; then
    echo "No GPG key provided; skipping signing."
    echo "To sign the archive, pass your GPG key ID: $0 sign <KEY_ID>"
    return 0
  fi

  if [[ ! -f "${ARCHIVE_PATH}" ]]; then
    echo "Archive ${ARCHIVE_PATH} not found. Building image first..."
    cmd_build "${key_id}"
    return 0
  fi

  local gpg_opts=(--batch --yes --detach-sign --armor --default-key "${key_id}" --output "${SIG_PATH}")
  echo "Signing archive ${ARCHIVE_PATH} with GPG key ${key_id}..."

  gpg "${gpg_opts[@]}" "${ARCHIVE_PATH}"
  echo "Successfully generated GPG signature file: ${SIG_PATH}"
}

cmd_verify() {
  if [[ ! -f "${SIG_PATH}" ]]; then
    echo "Error: Signature file ${SIG_PATH} does not exist."
    echo "Run '$0 sign <KEY_ID>' to generate a GPG signature for ${ARCHIVE_PATH}."
    exit 1
  fi

  echo "Verifying GPG signature for ${ARCHIVE_PATH}..."
  gpg --verify "${SIG_PATH}" "${ARCHIVE_PATH}"
}

cmd_e2e_challenge2_help() {
  echo "Usage: ./e2e_challenge2.sh [OPTIONS]"
  echo "       $0 e2e_challenge2 [OPTIONS]"
  echo ""
  echo "End-to-End Containerized Test Pipeline for API Server"
  echo ""
  echo "Pipeline Steps:"
  echo "  1. Build container image (api-server:TAG) via buildah & export zstd archive"
  echo "  2. Display image size & layer breakdown diagnostics (scripts/image_diagnostics.py)"
  echo "  3. Start containerized application on a free port (podman/docker) with .env"
  echo "  4. Wait for /health endpoint readiness"
  echo "  5. Execute Amazon Reviews test suite (scripts/test_amazon_reviews.py)"
  echo "  6. Automatically clean up test container on exit"
  echo ""
  echo "Options (passed to test_amazon_reviews.py):"
  echo "  -s, --samples-per-star INT  Samples to evaluate per star rating 1-5 (default: 2)"
  echo "  -b, --base-url TEXT         Base URL of API server"
  echo "  -h, --help                  Display this help message"
  echo ""
  echo "Environment Variables:"
  echo "  PORT                        Preferred host port to bind container (default: 8000)"
  echo "  CONTAINER_RUNNER            Container engine to use: podman or docker (auto-detected)"
}

cmd_e2e_challenge2() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    cmd_e2e_challenge2_help
    return 0
  fi

  local engine="${CONTAINER_RUNNER:-}"
  if [[ -z "${engine}" ]]; then
    if command -v podman >/dev/null 2>&1; then
      engine="podman"
    elif command -v docker >/dev/null 2>&1; then
      engine="docker"
    else
      echo "Error: Neither podman nor docker is installed."
      exit 1
    fi
  fi

  local base_port="${PORT:-8000}"
  local port="${base_port}"
  while ! python3 -c "import socket; s = socket.socket(); s.bind(('127.0.0.1', ${port}))" 2>/dev/null; do
    port=$((port + 1))
  done

  CONTAINER_ENGINE="${engine}"
  TEST_CONTAINER_NAME="api-server-test-${TAG}-${port}"

  cleanup() {
    if [[ -n "${TEST_CONTAINER_NAME:-}" && -n "${CONTAINER_ENGINE:-}" ]]; then
      echo -e "\n=== Step 5: Cleaning up test container '${TEST_CONTAINER_NAME}' ==="
      "${CONTAINER_ENGINE}" stop "${TEST_CONTAINER_NAME}" >/dev/null 2>&1 || true
      "${CONTAINER_ENGINE}" rm -f "${TEST_CONTAINER_NAME}" >/dev/null 2>&1 || true
      echo "Cleanup complete."
    fi
  }
  trap cleanup EXIT SIGINT SIGTERM

  echo "=== Step 1: Building container image ==="
  cmd_build

  echo -e "\n=== Step 2: Displaying Container Image Diagnostics ==="
  cmd_diagnostics

  local env_opts=()
  if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    env_opts+=(--env-file "${PROJECT_ROOT}/.env")
  fi

  echo -e "\n=== Step 3: Starting container '${TEST_CONTAINER_NAME}' on port ${port} ==="
  "${engine}" run -d \
    "${env_opts[@]}" \
    --name "${TEST_CONTAINER_NAME}" \
    -p "${port}:8000" \
    "${IMAGE_NAME}:${TAG}"

  echo "Waiting for API server to become ready at http://127.0.0.1:${port}/health..."
  local max_retries=30
  local retry_count=0
  until curl -s -f "http://127.0.0.1:${port}/health" >/dev/null 2>&1; do
    retry_count=$((retry_count + 1))
    if [[ "${retry_count}" -ge "${max_retries}" ]]; then
      echo "Error: API server failed to become ready after ${max_retries} seconds."
      "${engine}" logs "${TEST_CONTAINER_NAME}"
      exit 1
    fi
    sleep 1
  done
  echo "API server healthcheck passed!"

  echo -e "\n=== Step 4: Running Amazon Reviews Test Suite ==="
  uv run "${SCRIPT_DIR}/test_amazon_reviews.py" --base-url "http://127.0.0.1:${port}" "$@"
}

cmd_help() {
  echo "Usage: $0 [COMMAND] [ARGS...]"
  echo ""
  echo "Commands:"
  echo "  build [KEY_ID]      Build the container image and export OCI archive (default)"
  echo "  diagnostics         Display container image size breakdown, archive stats & GPG signature"
  echo "  e2e_challenge2      Build, display diagnostics, run container, and execute Amazon Reviews tests"
  echo "  sign [KEY_ID]       Sign the exported OCI archive using specified GPG key"
  echo "  verify              Verify the GPG signature of the exported OCI archive"
  echo "  help                Display this help message"
}

COMMAND="${1:-build}"
shift || true

case "${COMMAND}" in
  build)          cmd_build "$@" ;;
  diagnostics)    cmd_diagnostics ;;
  e2e_challenge2) cmd_e2e_challenge2 "$@" ;;
  sign)           cmd_sign "$@" ;;
  verify)         cmd_verify ;;
  help|-h|--help) cmd_help ;;
  *)              echo "Error: Unknown command '${COMMAND}'"; cmd_help; exit 1 ;;
esac