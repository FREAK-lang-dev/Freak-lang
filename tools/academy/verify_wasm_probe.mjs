#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import process from "node:process";

async function main(argv) {
  const wasmPath = argv[2];
  if (!wasmPath) {
    console.error("Usage: node tools/academy/verify_wasm_probe.mjs <academy-wasm-probe.wasm>");
    return 1;
  }

  const bytes = await readFile(wasmPath);
  const module = await WebAssembly.instantiate(bytes, {});
  const exports = module.instance.exports;

  const required = [
    "academy_protocol_version",
    "academy_wasm_probe_version",
    "academy_supported_lesson_count",
  ];
  for (const name of required) {
    if (typeof exports[name] !== "function") {
      console.error(`Missing WASM export: ${name}`);
      return 1;
    }
  }

  const protocolVersion = exports.academy_protocol_version();
  const probeVersion = exports.academy_wasm_probe_version();
  const lessonCount = exports.academy_supported_lesson_count();

  if (protocolVersion !== 1) {
    console.error(`Unexpected worker protocol version: ${protocolVersion}`);
    return 1;
  }
  if (probeVersion !== 1) {
    console.error(`Unexpected WASM probe version: ${probeVersion}`);
    return 1;
  }
  if (lessonCount !== 0) {
    console.error(`Probe must not claim lesson support yet: ${lessonCount}`);
    return 1;
  }

  console.log(`Academy WASM probe verified: protocol=${protocolVersion}, probe=${probeVersion}`);
  return 0;
}

main(process.argv)
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
