#!/usr/bin/env bash
# Rebuild the local Aseprite CLI used by this harness on Apple Silicon macOS.
set -euo pipefail

readonly tool_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly project_dir="$(cd "${tool_dir}/../.." && pwd)"
readonly source_dir="${project_dir}/vendor/aseprite"
readonly build_dir="${source_dir}/build"
readonly log_dir="${tool_dir}/logs"

readonly aseprite_repo="https://github.com/aseprite/aseprite.git"
readonly aseprite_revision="56757b5fc5f00cf5833fb68d5e864ba7f91059a3"
readonly skia_tag="m124-08a5439a6b"
readonly skia_dir="${source_dir}/.deps/skia-m124"
readonly skia_archive="Skia-macOS-Release-arm64.zip"
readonly skia_url="https://github.com/aseprite/skia/releases/download/${skia_tag}/${skia_archive}"
readonly skia_sha256="22663000967fc2c3f1a78190082228474955de02ffd13a352b39a48b204dac9a"

if [[ "$(uname)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  printf '%s\n' 'This script supports Apple Silicon macOS only.' >&2
  exit 1
fi

for command in git cmake ninja curl unzip shasum xcrun; do
  command -v "${command}" >/dev/null || {
    printf 'Missing required command: %s\n' "${command}" >&2
    exit 1
  }
done

mkdir -p "${project_dir}/vendor" "${log_dir}"

if [[ ! -d "${source_dir}/.git" ]]; then
  git clone --recursive "${aseprite_repo}" "${source_dir}"
fi

git -C "${source_dir}" fetch --tags origin
git -C "${source_dir}" checkout --detach "${aseprite_revision}"
git -C "${source_dir}" submodule update --init --recursive

if [[ ! -f "${skia_dir}/${skia_archive}" ]]; then
  mkdir -p "${skia_dir}"
  curl --fail --location --retry 3 --output "${skia_dir}/${skia_archive}.partial" "${skia_url}"
  mv "${skia_dir}/${skia_archive}.partial" "${skia_dir}/${skia_archive}"
fi

actual_sha256="$(shasum -a 256 "${skia_dir}/${skia_archive}" | awk '{print $1}')"
if [[ "${actual_sha256}" != "${skia_sha256}" ]]; then
  printf 'Skia SHA-256 mismatch: expected %s, got %s\n' "${skia_sha256}" "${actual_sha256}" >&2
  exit 1
fi

if [[ ! -f "${skia_dir}/out/Release-arm64/libskia.a" ]]; then
  unzip -q -n "${skia_dir}/${skia_archive}" -d "${skia_dir}"
fi

sdk_path="$(xcrun --sdk macosx --show-sdk-path)"
cmake -S "${source_dir}" -B "${build_dir}" -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
  -DCMAKE_OSX_SYSROOT="${sdk_path}" \
  -DLAF_BACKEND=skia \
  -DSKIA_DIR="${skia_dir}" \
  -DSKIA_LIBRARY_DIR="${skia_dir}/out/Release-arm64" \
  | tee "${log_dir}/configure.log"
cmake --build "${build_dir}" --target aseprite | tee "${log_dir}/build.log"

printf 'Built: %s\n' "${build_dir}/bin/aseprite"
