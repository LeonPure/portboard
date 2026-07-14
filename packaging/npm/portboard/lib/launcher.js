"use strict";

const path = require("node:path");
const { spawnSync } = require("node:child_process");

const PLATFORM_PACKAGES = Object.freeze({
  "darwin-arm64": "@leonpure/portboard-darwin-arm64",
  "darwin-x64": "@leonpure/portboard-darwin-x64",
  "linux-arm64": "@leonpure/portboard-linux-arm64",
  "linux-x64": "@leonpure/portboard-linux-x64",
});

function packageFor(platform = process.platform, arch = process.arch) {
  const target = `${platform}-${arch}`;
  const packageName = PLATFORM_PACKAGES[target];
  if (packageName === undefined) {
    throw new Error(
      `PortBoard does not provide a standalone binary for ${target}. ` +
        "Supported targets are macOS and Linux on arm64 or x64."
    );
  }
  return packageName;
}

function resolveBinary(options = {}) {
  const platform = options.platform ?? process.platform;
  const arch = options.arch ?? process.arch;
  const resolvePackage = options.resolvePackage ?? require.resolve;
  const packageName = packageFor(platform, arch);

  let manifest;
  try {
    manifest = resolvePackage(`${packageName}/package.json`);
  } catch (error) {
    const message =
      `The optional package ${packageName} is missing. ` +
      "Reinstall @leonpure/portboard with optional dependencies enabled.";
    const missingPackage = new Error(message);
    missingPackage.cause = error;
    throw missingPackage;
  }

  return path.join(path.dirname(manifest), "bin", "portboard");
}

function main(options = {}) {
  const argv = options.argv ?? process.argv.slice(2);
  const spawn = options.spawn ?? spawnSync;
  const stderr = options.stderr ?? process.stderr;

  try {
    const binary = resolveBinary(options);
    const result = spawn(binary, argv, { stdio: "inherit" });
    if (result.error !== undefined) {
      throw result.error;
    }
    if (result.signal !== null && result.signal !== undefined) {
      stderr.write(`portboard: terminated by ${result.signal}\n`);
      return 1;
    }
    return result.status ?? 1;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    stderr.write(`portboard: ${message}\n`);
    return 1;
  }
}

module.exports = { main, packageFor, resolveBinary };
