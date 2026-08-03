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
  local sign_key="${1:-${DEFAULT_KEY}}"

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
  local key_id="${1:-${DEFAULT_KEY}}"

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

cmd_diagnostics() {
  uv run "${SCRIPT_DIR}/image_diagnostics.py" "${IMAGE_NAME}" "${TAG}" "${ARCHIVE_PATH}"
}

cmd_help() {
  echo "Usage: $0 [COMMAND] [KEY_ID]"
  echo ""
  echo "Commands:"
  echo "  build [KEY_ID]      Build the container image and export OCI archive (default)"
  echo "  diagnostics         Display container image size breakdown, archive stats & GPG signature"
  echo "  sign [KEY_ID]       Sign the exported OCI archive using specified GPG key"
  echo "  verify              Verify the GPG signature of the exported OCI archive"
  echo "  help                Display this help message"
}

COMMAND="${1:-build}"
shift || true

case "${COMMAND}" in
  build)       cmd_build "$@" ;;
  diagnostics) cmd_diagnostics ;;
  sign)        cmd_sign "$@" ;;
  verify)      cmd_verify ;;
  help|-h|--help) cmd_help ;;
  *)           echo "Error: Unknown command '${COMMAND}'"; cmd_help; exit 1 ;;
esac