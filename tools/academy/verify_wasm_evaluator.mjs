#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import process from "node:process";
import {
  createAcademyWasmEvaluator,
  handleAcademyWorkerEnvelope,
} from "../../learning/wasm/academy-worker.mjs";
import { buildAcademyPackage } from "./academy_package_loader.mjs";

async function main(argv) {
  const wasmPath = argv[2];
  if (!wasmPath) {
    console.error("Usage: node tools/academy/verify_wasm_evaluator.mjs <academy-wasm-evaluator.wasm>");
    return 1;
  }

  const bytes = await readFile(wasmPath);
  const wasm = await WebAssembly.instantiate(bytes, {});
  const evaluator = createAcademyWasmEvaluator(wasm.instance);

  assert(evaluator.supportsLesson("hello-freak"), "WASM evaluator must support hello-freak");

  const passing = evaluator.runHelloFreak('-- comment allowed\nsay "Hello, FREAK Academy!"\n');
  assert(passing.ok, `passing hello source should run: ${passing.message}`);
  assert(passing.stdout === "Hello, FREAK Academy!\n", `unexpected stdout: ${JSON.stringify(passing.stdout)}`);

  const wrongOutput = evaluator.runHelloFreak('say "Wrong"\n');
  assert(wrongOutput.ok, `wrong-output source should still run: ${wrongOutput.message}`);
  assert(wrongOutput.stdout === "Wrong\n", `unexpected wrong-output stdout: ${JSON.stringify(wrongOutput.stdout)}`);

  const parseFailure = evaluator.runHelloFreak('pilot greeting = "Hello"\n');
  assert(!parseFailure.ok, "non-say source should fail the hello evaluator");
  assert(parseFailure.message === "expected say statement", `unexpected parse message: ${parseFailure.message}`);

  const academyPackage = await buildAcademyPackage(process.cwd());
  const evaluateResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-evaluate-hello",
      method: "evaluateExercise",
      params: {
        lessonId: "hello-freak",
        exerciseId: "hello-exercise",
        source: '-- comment allowed\nsay "Hello, FREAK Academy!"\n',
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(evaluateResponse.ok, JSON.stringify(evaluateResponse));
  assert(evaluateResponse.result?.passed === true, "hello exercise should pass through WASM-backed worker");

  const runResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-run-hello",
      method: "run",
      params: {
        fileId: "hello-freak.fk",
        source: 'say "Hello, FREAK Academy!"\n',
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(runResponse.ok, JSON.stringify(runResponse));
  assert(runResponse.result?.stdout === "Hello, FREAK Academy!\n", "hello run stdout should match");

  console.log("Academy WASM evaluator verified: hello-freak evaluation passes through worker protocol");
  return 0;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

main(process.argv)
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
