#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import process from "node:process";
import { handleAcademyWorkerEnvelope } from "../../learning/wasm/academy-worker.mjs";
import { buildAcademyPackage } from "./academy_package_loader.mjs";

async function main(argv) {
  const requestPath = argv[2];
  const raw = requestPath ? await readFile(requestPath, "utf8") : await readStdin();
  const academyPackage = await buildAcademyPackage(process.cwd());

  let response;
  try {
    const envelope = JSON.parse(stripBom(raw));
    if (typeof envelope !== "object" || envelope === null || Array.isArray(envelope)) {
      throw new Error("request JSON must be an object");
    }
    response = handleAcademyWorkerEnvelope(envelope, academyPackage);
  } catch (error) {
    response = {
      protocolVersion: 1,
      requestId: "",
      ok: false,
      error: {
        code: "bad_json",
        message: error.message,
      },
    };
  }

  process.stdout.write(`${JSON.stringify(response, null, 2)}\n`);
  return response.ok ? 0 : 1;
}

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

function stripBom(raw) {
  return raw.replace(/^\uFEFF/, "").replace(/^\u00EF\u00BB\u00BF/, "");
}

main(process.argv)
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
