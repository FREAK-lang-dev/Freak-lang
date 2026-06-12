#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { readdirSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { handleAcademyWorkerEnvelope } from "../../learning/wasm/academy-worker.mjs";
import { buildAcademyPackage } from "./academy_package_loader.mjs";

async function main(argv) {
  const root = process.cwd();
  const fixturesDir = argv[2] ? path.resolve(argv[2]) : path.join(root, "learning", "wasm", "fixtures");
  const academyPackage = await buildAcademyPackage(root);
  const failures = [];

  for (const name of requestFixtureNames(fixturesDir)) {
    const request = await readJson(path.join(fixturesDir, name));
    const expected = await readJson(path.join(fixturesDir, name.replace(".request.json", ".response.json")));
    const actual = handleAcademyWorkerEnvelope(request, academyPackage);
    const diff = compareJson(actual, expected);
    if (diff) {
      failures.push(`${name}: ${diff}`);
      continue;
    }
    console.log(`${name}: OK`);
  }

  for (const check of await runDemonstrationChecks(academyPackage)) {
    if (!check.ok) {
      failures.push(`${check.label}: expected ${JSON.stringify(check.expected)}, got ${JSON.stringify(check.actual)}`);
      continue;
    }
    console.log(`${check.label}: OK`);
  }

  if (failures.length > 0) {
    console.error("Browser worker fixture verification failed:");
    for (const failure of failures) {
      console.error(`  - ${failure}`);
    }
    return 1;
  }
  return 0;
}

function requestFixtureNames(fixturesDir) {
  return readdirSync(fixturesDir)
    .filter((name) => name.endsWith(".request.json"))
    .sort((a, b) => a.localeCompare(b));
}

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

async function runDemonstrationChecks(academyPackage) {
  const checks = [];
  for (const course of academyPackage.courses ?? []) {
    for (const lesson of course.lessonData ?? []) {
      for (const section of lesson.sections ?? []) {
        if (section.type !== "demonstration" || typeof section.source !== "string") {
          continue;
        }
        const request = {
          protocolVersion: 1,
          requestId: `demo-${lesson.id}-${section.id}`,
          method: "run",
          params: {
            fileId: `${lesson.id}.fk`,
            source: section.source,
          },
        };
        const response = handleAcademyWorkerEnvelope(request, academyPackage);
        checks.push({
          label: `demo ${lesson.id}/${section.id}`,
          ok: response.ok === true && response.result?.ok === true && response.result?.stdout === section.expectedOutput,
          expected: section.expectedOutput,
          actual: response.result?.stdout ?? response.error?.message,
        });
      }
    }
  }
  return checks;
}

function compareJson(actual, expected, trail = "$") {
  if (Object.is(actual, expected)) {
    return "";
  }
  if (Array.isArray(actual) || Array.isArray(expected)) {
    if (!Array.isArray(actual) || !Array.isArray(expected)) {
      return `${trail}: expected ${typeName(expected)}, got ${typeName(actual)}`;
    }
    if (actual.length !== expected.length) {
      return `${trail}: expected ${expected.length} item(s), got ${actual.length}`;
    }
    for (let i = 0; i < actual.length; i += 1) {
      const diff = compareJson(actual[i], expected[i], `${trail}[${i}]`);
      if (diff) {
        return diff;
      }
    }
    return "";
  }
  if (isObject(actual) || isObject(expected)) {
    if (!isObject(actual) || !isObject(expected)) {
      return `${trail}: expected ${typeName(expected)}, got ${typeName(actual)}`;
    }
    const actualKeys = Object.keys(actual).sort();
    const expectedKeys = Object.keys(expected).sort();
    if (actualKeys.join("\0") !== expectedKeys.join("\0")) {
      return `${trail}: expected keys ${expectedKeys.join(", ")}, got ${actualKeys.join(", ")}`;
    }
    for (const key of expectedKeys) {
      const diff = compareJson(actual[key], expected[key], `${trail}.${key}`);
      if (diff) {
        return diff;
      }
    }
    return "";
  }
  return `${trail}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`;
}

function isObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function typeName(value) {
  if (Array.isArray(value)) {
    return "array";
  }
  if (value === null) {
    return "null";
  }
  return typeof value;
}

main(process.argv)
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
