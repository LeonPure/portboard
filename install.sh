#!/bin/sh

set -eu

repository="LeonPure/portboard"
program="portboard"
requested_version="${PORTBOARD_VERSION:-}"
install_dir="${PORTBOARD_INSTALL_DIR:-}"
release_base_url="${PORTBOARD_RELEASE_BASE_URL:-https://github.com/${repository}/releases/download}"
releases_api="${PORTBOARD_RELEASES_API:-https://api.github.com/repos/${repository}/releases}"

usage() {
  cat <<'EOF'
Install PortBoard from an official GitHub Release.

Usage:
  install.sh [--version VERSION] [--install-dir DIRECTORY]

Options:
  --version VERSION        Install an exact version, such as 0.1.0a2.
  --install-dir DIRECTORY  Install into DIRECTORY instead of ~/.local/bin.
  -h, --help               Show this help.

Environment variables:
  PORTBOARD_VERSION
  PORTBOARD_INSTALL_DIR
EOF
}

fail() {
  printf 'portboard installer: %s\n' "$*" >&2
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --version)
      [ "$#" -ge 2 ] || fail "--version requires a value"
      requested_version="$2"
      shift 2
      ;;
    --install-dir)
      [ "$#" -ge 2 ] || fail "--install-dir requires a value"
      install_dir="$2"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
done

for command_name in curl tar awk grep mktemp mkdir install; do
  command -v "$command_name" >/dev/null 2>&1 || fail "required command not found: $command_name"
done

if [ -z "$install_dir" ]; then
  [ -n "${HOME:-}" ] || fail "HOME is not set; pass --install-dir"
  install_dir="${HOME}/.local/bin"
fi

curl_text() {
  curl --proto '=https' --tlsv1.2 --fail --location --silent --show-error "$1"
}

curl_file() {
  curl --proto '=https' --tlsv1.2 --fail --location --silent --show-error \
    --output "$2" "$1"
}

extract_tag() {
  awk -F '"' '/"tag_name"[[:space:]]*:/ { print $4; exit }'
}

if [ -n "$requested_version" ]; then
  case "$requested_version" in
    v*) tag="$requested_version" ;;
    *) tag="v${requested_version}" ;;
  esac
else
  tag=""
  if stable_metadata=$(curl_text "${releases_api}/latest" 2>/dev/null); then
    tag=$(printf '%s\n' "$stable_metadata" | extract_tag)
  fi
  if [ -z "$tag" ]; then
    release_metadata=$(curl_text "${releases_api}?per_page=1")
    tag=$(printf '%s\n' "$release_metadata" | extract_tag)
  fi
fi

[ -n "$tag" ] || fail "no published PortBoard release was found"
printf '%s\n' "$tag" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+((a|b|rc)[0-9]+)?$' || \
  fail "unsupported release tag: $tag"
version=${tag#v}

detected_os="${PORTBOARD_OS:-$(uname -s)}"
case "$detected_os" in
  Darwin | darwin) os="darwin" ;;
  Linux | linux) os="linux" ;;
  *) fail "unsupported operating system: $detected_os" ;;
esac

detected_arch="${PORTBOARD_ARCH:-$(uname -m)}"
case "$detected_arch" in
  arm64 | aarch64) arch="arm64" ;;
  x86_64 | amd64) arch="x64" ;;
  *) fail "unsupported architecture: $detected_arch" ;;
esac

target="${os}-${arch}"
archive="${program}-${target}.tar.gz"
tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/portboard.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM

printf 'Downloading PortBoard %s for %s...\n' "$version" "$target"
curl_file "${release_base_url}/${tag}/${archive}" "${tmp_dir}/${archive}"
curl_file "${release_base_url}/${tag}/SHA256SUMS" "${tmp_dir}/SHA256SUMS"

expected_checksum=$(
  awk -v filename="$archive" \
    '$2 == filename || $2 == "*" filename { print $1; exit }' \
    "${tmp_dir}/SHA256SUMS"
)
[ -n "$expected_checksum" ] || fail "SHA256SUMS does not contain $archive"
printf '%s\n' "$expected_checksum" | grep -Eq '^[0-9a-f]{64}$' || \
  fail "invalid SHA-256 value for $archive"

if command -v sha256sum >/dev/null 2>&1; then
  actual_checksum=$(sha256sum "${tmp_dir}/${archive}" | awk '{ print $1 }')
elif command -v shasum >/dev/null 2>&1; then
  actual_checksum=$(shasum -a 256 "${tmp_dir}/${archive}" | awk '{ print $1 }')
else
  fail "sha256sum or shasum is required"
fi

[ "$actual_checksum" = "$expected_checksum" ] || fail "checksum verification failed for $archive"

tar -xzf "${tmp_dir}/${archive}" -C "$tmp_dir"
binary="${tmp_dir}/${program}-${target}"
[ -f "$binary" ] || fail "release archive does not contain ${program}-${target}"

mkdir -p "$install_dir"
destination="${install_dir}/${program}"
install -m 755 "$binary" "$destination"

installed_version=$("$destination" --version 2>&1) || fail "installed binary did not start"
[ "$installed_version" = "portboard $version" ] || \
  fail "installed binary reported an unexpected version: $installed_version"

printf 'Installed %s to %s\n' "$installed_version" "$destination"
case ":${PATH}:" in
  *":${install_dir}:"*) ;;
  *) printf 'Add %s to PATH to run portboard directly.\n' "$install_dir" ;;
esac
