"use strict";

const assert = require("node:assert/strict");
const path = require("node:path");
const test = require("node:test");

const { main, packageFor, resolveBinary } = require("../lib/launcher");

test("selects the package for every supported platform", () => {
  assert.equal(packageFor("darwin", "arm64"), "@leonpure/portboard-darwin-arm64");
  assert.equal(packageFor("darwin", "x64"), "@leonpure/portboard-darwin-x64");
  assert.equal(packageFor("linux", "arm64"), "@leonpure/portboard-linux-arm64");
  assert.equal(packageFor("linux", "x64"), "@leonpure/portboard-linux-x64");
  assert.equal(packageFor("win32", "arm64"), "@leonpure/portboard-win32-arm64");
  assert.equal(packageFor("win32", "x64"), "@leonpure/portboard-win32-x64");
});

test("rejects unsupported platforms with an actionable message", () => {
  assert.throws(
    () => packageFor("win32", "ia32"),
    /does not provide a standalone binary for win32-ia32/
  );
});

test("resolves the native executable beside the platform manifest", () => {
  const binary = resolveBinary({
    platform: "darwin",
    arch: "arm64",
    resolvePackage: (request) => {
      assert.equal(request, "@leonpure/portboard-darwin-arm64/package.json");
      return path.join("", "packages", "darwin-arm64", "package.json");
    },
  });

  assert.equal(binary, path.join("packages", "darwin-arm64", "bin", "portboard"));
});

test("resolves the executable suffix for Windows", () => {
  const binary = resolveBinary({
    platform: "win32",
    arch: "x64",
    resolvePackage: (request) => {
      assert.equal(request, "@leonpure/portboard-win32-x64/package.json");
      return path.join("", "packages", "win32-x64", "package.json");
    },
  });

  assert.equal(binary, path.join("packages", "win32-x64", "bin", "portboard.exe"));
});

test("passes arguments and terminal streams to the native executable", () => {
  const calls = [];
  const status = main({
    platform: "linux",
    arch: "x64",
    argv: ["--json"],
    resolvePackage: () => path.join("", "platform", "package.json"),
    spawn: (...args) => {
      calls.push(args);
      return { status: 7, signal: null };
    },
  });

  assert.equal(status, 7);
  assert.deepEqual(calls, [
    [path.join("platform", "bin", "portboard"), ["--json"], { stdio: "inherit" }],
  ]);
});

test("reports a missing optional platform package", () => {
  let output = "";
  const status = main({
    platform: "linux",
    arch: "arm64",
    resolvePackage: () => {
      throw new Error("not installed");
    },
    stderr: { write: (text) => (output += text) },
  });

  assert.equal(status, 1);
  assert.match(output, /optional package @leonpure\/portboard-linux-arm64 is missing/);
});
