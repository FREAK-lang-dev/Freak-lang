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
  assert(evaluator.supportsLesson("variables"), "WASM evaluator must support variables");
  assert(evaluator.supportsLesson("primitive-types"), "WASM evaluator must support primitive-types");
  assert(evaluator.supportsLesson("arithmetic"), "WASM evaluator must support arithmetic");
  assert(evaluator.supportsLesson("conditions"), "WASM evaluator must support conditions");
  assert(evaluator.supportsLesson("loops"), "WASM evaluator must support loops");

  const passing = evaluator.runHelloFreak('-- comment allowed\nsay "Hello, FREAK Academy!"\n');
  assert(passing.ok, `passing hello source should run: ${passing.message}`);
  assert(passing.stdout === "Hello, FREAK Academy!\n", `unexpected stdout: ${JSON.stringify(passing.stdout)}`);

  const wrongOutput = evaluator.runHelloFreak('say "Wrong"\n');
  assert(wrongOutput.ok, `wrong-output source should still run: ${wrongOutput.message}`);
  assert(wrongOutput.stdout === "Wrong\n", `unexpected wrong-output stdout: ${JSON.stringify(wrongOutput.stdout)}`);

  const parseFailure = evaluator.runHelloFreak('pilot greeting = "Hello"\n');
  assert(!parseFailure.ok, "non-say source should fail the hello evaluator");
  assert(parseFailure.message === "expected say statement", `unexpected parse message: ${parseFailure.message}`);

  const variablesPassing = evaluator.runVariables("pilot score = 100\nsay score\n");
  assert(variablesPassing.ok, `passing variables source should run: ${variablesPassing.message}`);
  assert(variablesPassing.stdout === "100\n", `unexpected variables stdout: ${JSON.stringify(variablesPassing.stdout)}`);

  const variablesExpression = evaluator.runVariables("pilot score: int = 50 + 50\nsay score\n");
  assert(variablesExpression.ok, `typed variables expression should run: ${variablesExpression.message}`);
  assert(variablesExpression.stdout === "100\n", `unexpected expression stdout: ${JSON.stringify(variablesExpression.stdout)}`);

  const variablesDirectOutput = evaluator.runVariables("say 100\n");
  assert(variablesDirectOutput.ok, `direct output source should run: ${variablesDirectOutput.message}`);
  assert(variablesDirectOutput.stdout === "100\n", `unexpected direct stdout: ${JSON.stringify(variablesDirectOutput.stdout)}`);

  const variablesUnknown = evaluator.runVariables("say score\n");
  assert(!variablesUnknown.ok, "unknown variable should fail the variables evaluator");
  assert(variablesUnknown.message === "unknown symbol in WASM evaluator", `unexpected variables error: ${variablesUnknown.message}`);

  const primitivePassing = evaluator.runPrimitiveTypes(
    'pilot callsign: word = "Shiranui"\npilot power: int = 9001\nsay callsign\nsay power\n',
  );
  assert(primitivePassing.ok, `primitive-types source should run: ${primitivePassing.message}`);
  assert(primitivePassing.stdout === "Shiranui\n9001\n", `unexpected primitive stdout: ${JSON.stringify(primitivePassing.stdout)}`);

  const arithmeticPassing = evaluator.runArithmetic("pilot width = 8\npilot height = 4\nsay width * height\n");
  assert(arithmeticPassing.ok, `arithmetic source should run: ${arithmeticPassing.message}`);
  assert(arithmeticPassing.stdout === "32\n", `unexpected arithmetic stdout: ${JSON.stringify(arithmeticPassing.stdout)}`);

  const arithmeticExpression = evaluator.runArithmetic("pilot width = 10 - 2\npilot height = 2 + 2\nsay width * height\n");
  assert(arithmeticExpression.ok, `arithmetic expression source should run: ${arithmeticExpression.message}`);
  assert(arithmeticExpression.stdout === "32\n", `unexpected arithmetic expression stdout: ${JSON.stringify(arithmeticExpression.stdout)}`);

  const conditionsPassing = evaluator.runConditions(
    'pilot power = 9001\nif power > 9000 {\n    say "over"\n} else {\n    say "normal"\n}\n',
  );
  assert(conditionsPassing.ok, `conditions source should run: ${conditionsPassing.message}`);
  assert(conditionsPassing.stdout === "over\n", `unexpected conditions stdout: ${JSON.stringify(conditionsPassing.stdout)}`);

  const conditionsElseBranch = evaluator.runConditions(
    'pilot power = 20\nif power > 9000 {\n    say "over"\n} else {\n    say "normal"\n}\n',
  );
  assert(conditionsElseBranch.ok, `conditions else source should run: ${conditionsElseBranch.message}`);
  assert(conditionsElseBranch.stdout === "normal\n", `unexpected conditions else stdout: ${JSON.stringify(conditionsElseBranch.stdout)}`);

  const loopsPassing = evaluator.runLoops('repeat 3 times {\n    say "FREAK"\n}\n');
  assert(loopsPassing.ok, `loops source should run: ${loopsPassing.message}`);
  assert(loopsPassing.stdout === "FREAK\nFREAK\nFREAK\n", `unexpected loops stdout: ${JSON.stringify(loopsPassing.stdout)}`);

  const loopsExpression = evaluator.runLoops('pilot count = 1 + 2\nrepeat count times {\n    say "FREAK"\n}\n');
  assert(loopsExpression.ok, `loops expression source should run: ${loopsExpression.message}`);
  assert(loopsExpression.stdout === "FREAK\nFREAK\nFREAK\n", `unexpected loops expression stdout: ${JSON.stringify(loopsExpression.stdout)}`);

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

  const variablesResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-evaluate-variables",
      method: "evaluateExercise",
      params: {
        lessonId: "variables",
        exerciseId: "score-exercise",
        source: "pilot score = 100\nsay score\n",
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(variablesResponse.ok, JSON.stringify(variablesResponse));
  assert(variablesResponse.result?.passed === true, "variables exercise should pass through WASM-backed worker");

  const variablesRunResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-run-variables",
      method: "run",
      params: {
        fileId: "variables.fk",
        source: "pilot score = 100\nsay score\n",
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(variablesRunResponse.ok, JSON.stringify(variablesRunResponse));
  assert(variablesRunResponse.result?.stdout === "100\n", "variables run stdout should match");

  const primitiveResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-evaluate-primitive-types",
      method: "evaluateExercise",
      params: {
        lessonId: "primitive-types",
        exerciseId: "types-exercise",
        source: 'pilot callsign: word = "Shiranui"\npilot power: int = 9001\nsay callsign\nsay power\n',
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(primitiveResponse.ok, JSON.stringify(primitiveResponse));
  assert(primitiveResponse.result?.passed === true, "primitive-types exercise should pass through WASM-backed worker");

  const arithmeticResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-evaluate-arithmetic",
      method: "evaluateExercise",
      params: {
        lessonId: "arithmetic",
        exerciseId: "area-exercise",
        source: "pilot width = 8\npilot height = 4\nsay width * height\n",
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(arithmeticResponse.ok, JSON.stringify(arithmeticResponse));
  assert(arithmeticResponse.result?.passed === true, "arithmetic exercise should pass through WASM-backed worker");

  const conditionsResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-evaluate-conditions",
      method: "evaluateExercise",
      params: {
        lessonId: "conditions",
        exerciseId: "power-exercise",
        source: 'pilot power = 9001\nif power > 9000 {\n    say "over"\n} else {\n    say "normal"\n}\n',
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(conditionsResponse.ok, JSON.stringify(conditionsResponse));
  assert(conditionsResponse.result?.passed === true, "conditions exercise should pass through WASM-backed worker");

  const conditionsRunResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-run-conditions",
      method: "run",
      params: {
        fileId: "conditions.fk",
        source: 'pilot power = 9001\nif power > 9000 {\n    say "over"\n} else {\n    say "normal"\n}\n',
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(conditionsRunResponse.ok, JSON.stringify(conditionsRunResponse));
  assert(conditionsRunResponse.result?.stdout === "over\n", "conditions run stdout should match");

  const loopsResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-evaluate-loops",
      method: "evaluateExercise",
      params: {
        lessonId: "loops",
        exerciseId: "repeat-exercise",
        source: 'repeat 3 times {\n    say "FREAK"\n}\n',
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(loopsResponse.ok, JSON.stringify(loopsResponse));
  assert(loopsResponse.result?.passed === true, "loops exercise should pass through WASM-backed worker");

  const loopsRunResponse = handleAcademyWorkerEnvelope(
    {
      protocolVersion: 1,
      requestId: "wasm-run-loops",
      method: "run",
      params: {
        fileId: "loops.fk",
        source: 'repeat 3 times {\n    say "FREAK"\n}\n',
      },
    },
    academyPackage,
    { wasmEvaluator: evaluator },
  );
  assert(loopsRunResponse.ok, JSON.stringify(loopsRunResponse));
  assert(loopsRunResponse.result?.stdout === "FREAK\nFREAK\nFREAK\n", "loops run stdout should match");

  console.log("Academy WASM evaluator verified: first six basics lessons pass through worker protocol");
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
