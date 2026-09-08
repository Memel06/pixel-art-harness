#!/usr/bin/env bash
# Validate the local CLI without changing the user's Aseprite preferences.
set -euo pipefail

readonly tool_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly project_dir="$(cd "${tool_dir}/../.." && pwd)"
readonly binary="${ASEPRITE_BIN:-${project_dir}/vendor/aseprite/build/bin/aseprite}"
readonly user_dir="${tool_dir}/.aseprite-user"
readonly log_dir="${tool_dir}/logs"

if [[ ! -x "${binary}" ]]; then
  printf 'Aseprite binary is not executable: %s\n' "${binary}" >&2
  exit 1
fi

mkdir -p "${user_dir}" "${log_dir}"
scratch_dir="$(mktemp -d "${tool_dir}/smoke.XXXXXX")"
trap 'rm -rf "${scratch_dir}"' EXIT

ase_path="${scratch_dir}/smoke.aseprite"
png_path="${scratch_dir}/smoke.png"

ASEPRITE_USER_FOLDER="${user_dir}" "${binary}" --batch \
  --script-param "ase=${ase_path}" \
  --script-param "png=${png_path}" \
  --script "${tool_dir}/smoke-test.lua" \
  | tee "${log_dir}/smoke.log"

test -s "${ase_path}"
test -s "${png_path}"

layer_listing="$(ASEPRITE_USER_FOLDER="${user_dir}" "${binary}" --batch --list-layers "${ase_path}")"
printf '%s\n' "${layer_listing}" | tee -a "${log_dir}/smoke.log"
expected_layers=$'Base\nAccent'
if [[ "${layer_listing}" != "${expected_layers}" ]]; then
  printf 'Unexpected reopened layer listing: %s\n' "${layer_listing}" \
    | tee -a "${log_dir}/smoke.log" >&2
  exit 1
fi

png_file_info="$(file "${png_path}")"
printf '%s\n' "${png_file_info}" | tee -a "${log_dir}/smoke.log"
if [[ "${png_file_info}" != *': PNG image data,'* ]]; then
  printf 'Export is not recognized as PNG image data.\n' \
    | tee -a "${log_dir}/smoke.log" >&2
  exit 1
fi

png_properties="$(sips -g format -g pixelWidth -g pixelHeight "${png_path}")"
printf '%s\n' "${png_properties}" | tee -a "${log_dir}/smoke.log"
png_format="$(printf '%s\n' "${png_properties}" | awk '/format:/ { print $2; exit }')"
png_width="$(printf '%s\n' "${png_properties}" | awk '/pixelWidth:/ { print $2; exit }')"
png_height="$(printf '%s\n' "${png_properties}" | awk '/pixelHeight:/ { print $2; exit }')"
if [[ "${png_format}" != "png" || "${png_width}" != "8" || "${png_height}" != "8" ]]; then
  printf 'Unexpected PNG properties: format=%s width=%s height=%s\n' \
    "${png_format}" "${png_width}" "${png_height}" \
    | tee -a "${log_dir}/smoke.log" >&2
  exit 1
fi

printf 'Smoke test passed: editable two-layer .aseprite and 8x8 PNG export.\n' | tee -a "${log_dir}/smoke.log"
