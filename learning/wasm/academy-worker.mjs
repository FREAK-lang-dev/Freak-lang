export const PROTOCOL_VERSION = 1;

const DEFAULT_LIMITS = Object.freeze({
  maxSteps: 10000,
  maxLoopIterations: 1000,
});

const WASM_STATUS_PARSES = 1;
const WASM_STATUS_COMPILES = 2;
const WASM_STATUS_RUNS = 4;
const WASM_STATUS_OUTPUT_MATCHES = 8;
const TEXT_ENCODER = new TextEncoder();
const TEXT_DECODER = new TextDecoder();

class WorkerProtocolError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

class FreakSubsetError extends Error {}

class ReturnSignal {
  constructor(value) {
    this.value = value;
  }
}

class Environment {
  constructor(parent = null) {
    this.parent = parent;
    this.values = new Map();
  }

  define(name, value) {
    this.values.set(name, value);
  }

  get(name) {
    if (this.values.has(name)) {
      return this.values.get(name);
    }
    if (this.parent !== null) {
      return this.parent.get(name);
    }
    throw new FreakSubsetError(`unknown symbol: ${name}`);
  }
}

class Lexer {
  constructor(source) {
    this.source = source;
    this.index = 0;
    this.tokens = [];
  }

  tokenize() {
    while (!this.isAtEnd()) {
      const ch = this.peekChar();
      if (/\s/.test(ch)) {
        this.index += 1;
        continue;
      }
      if (this.source.startsWith("--", this.index)) {
        this.skipLineComment();
        continue;
      }
      if (ch === '"') {
        this.readString();
        continue;
      }
      if (/[0-9]/.test(ch)) {
        this.readNumber();
        continue;
      }
      if (/[A-Za-z_]/.test(ch)) {
        this.readIdentifier();
        continue;
      }

      const two = this.source.slice(this.index, this.index + 2);
      if (["->", ">=", "<=", "==", "!="].includes(two)) {
        this.tokens.push({ type: "symbol", value: two, offset: this.index });
        this.index += 2;
        continue;
      }
      if ("{}():,+-*/><=".includes(ch)) {
        this.tokens.push({ type: "symbol", value: ch, offset: this.index });
        this.index += 1;
        continue;
      }
      throw new FreakSubsetError(`unexpected character ${JSON.stringify(ch)} at offset ${this.index}`);
    }
    this.tokens.push({ type: "eof", value: "", offset: this.index });
    return this.tokens;
  }

  isAtEnd() {
    return this.index >= this.source.length;
  }

  peekChar() {
    return this.source[this.index];
  }

  skipLineComment() {
    while (!this.isAtEnd() && this.peekChar() !== "\n") {
      this.index += 1;
    }
  }

  readString() {
    const start = this.index;
    this.index += 1;
    let value = "";
    while (!this.isAtEnd()) {
      const ch = this.peekChar();
      if (ch === '"') {
        this.index += 1;
        this.tokens.push({ type: "string", value, offset: start });
        return;
      }
      if (ch === "\\") {
        this.index += 1;
        if (this.isAtEnd()) {
          break;
        }
        const escaped = this.peekChar();
        const escapes = { n: "\n", r: "\r", t: "\t", '"': '"', "\\": "\\" };
        value += Object.hasOwn(escapes, escaped) ? escapes[escaped] : escaped;
        this.index += 1;
        continue;
      }
      value += ch;
      this.index += 1;
    }
    throw new FreakSubsetError(`unterminated word literal at offset ${start}`);
  }

  readNumber() {
    const start = this.index;
    while (!this.isAtEnd() && /[0-9]/.test(this.peekChar())) {
      this.index += 1;
    }
    this.tokens.push({
      type: "number",
      value: Number(this.source.slice(start, this.index)),
      offset: start,
    });
  }

  readIdentifier() {
    const start = this.index;
    while (!this.isAtEnd() && /[A-Za-z0-9_]/.test(this.peekChar())) {
      this.index += 1;
    }
    this.tokens.push({
      type: "identifier",
      value: this.source.slice(start, this.index),
      offset: start,
    });
  }
}

class Parser {
  constructor(tokens) {
    this.tokens = tokens;
    this.current = 0;
  }

  parseProgram() {
    const statements = [];
    while (!this.check("eof") && !this.checkSymbol("}")) {
      statements.push(this.parseStatement());
    }
    this.consume("eof", "expected end of source");
    return { kind: "Program", statements };
  }

  parseBlock() {
    this.consumeSymbol("{", "expected `{` to start block");
    const statements = [];
    while (!this.check("eof") && !this.checkSymbol("}")) {
      statements.push(this.parseStatement());
    }
    this.consumeSymbol("}", "expected `}` to close block");
    return statements;
  }

  parseStatement() {
    if (this.matchKeyword("pilot")) {
      return this.parsePilotDeclaration();
    }
    if (this.matchKeyword("say")) {
      return { kind: "Say", expression: this.parseExpression() };
    }
    if (this.matchKeyword("repeat")) {
      const count = this.parseExpression();
      this.consumeKeyword("times", "expected `times` after repeat count");
      return { kind: "Repeat", count, body: this.parseBlock() };
    }
    if (this.matchKeyword("if")) {
      const condition = this.parseExpression();
      const thenBranch = this.parseBlock();
      let elseBranch = [];
      if (this.matchKeyword("else")) {
        elseBranch = this.parseBlock();
      }
      return { kind: "If", condition, thenBranch, elseBranch };
    }
    if (this.matchKeyword("task")) {
      return this.parseTaskDeclaration();
    }
    if (this.matchKeyword("give")) {
      this.consumeKeyword("back", "expected `back` after `give`");
      return { kind: "GiveBack", expression: this.parseExpression() };
    }
    const token = this.peek();
    throw new FreakSubsetError(`expected statement at offset ${token.offset}`);
  }

  parsePilotDeclaration() {
    const name = this.consume("identifier", "expected pilot name").value;
    let typeName = null;
    if (this.matchSymbol(":")) {
      typeName = this.consume("identifier", "expected type annotation").value;
    }
    this.consumeSymbol("=", "expected `=` in pilot declaration");
    return { kind: "Pilot", name, typeName, initializer: this.parseExpression() };
  }

  parseTaskDeclaration() {
    const name = this.consume("identifier", "expected task name").value;
    this.consumeSymbol("(", "expected `(` after task name");
    const params = [];
    if (!this.checkSymbol(")")) {
      do {
        const paramName = this.consume("identifier", "expected parameter name").value;
        let typeName = null;
        if (this.matchSymbol(":")) {
          typeName = this.consume("identifier", "expected parameter type").value;
        }
        params.push({ name: paramName, typeName });
      } while (this.matchSymbol(","));
    }
    this.consumeSymbol(")", "expected `)` after parameters");
    let returnType = null;
    if (this.matchSymbol("->")) {
      returnType = this.consume("identifier", "expected return type").value;
    }
    return { kind: "Task", name, params, returnType, body: this.parseBlock() };
  }

  parseExpression() {
    return this.parseEquality();
  }

  parseEquality() {
    let expr = this.parseComparison();
    while (this.matchSymbol("==") || this.matchSymbol("!=")) {
      const operator = this.previous().value;
      const right = this.parseComparison();
      expr = { kind: "Binary", operator, left: expr, right };
    }
    return expr;
  }

  parseComparison() {
    let expr = this.parseTerm();
    while (
      this.matchSymbol(">") ||
      this.matchSymbol(">=") ||
      this.matchSymbol("<") ||
      this.matchSymbol("<=")
    ) {
      const operator = this.previous().value;
      const right = this.parseTerm();
      expr = { kind: "Binary", operator, left: expr, right };
    }
    return expr;
  }

  parseTerm() {
    let expr = this.parseFactor();
    while (this.matchSymbol("+") || this.matchSymbol("-")) {
      const operator = this.previous().value;
      const right = this.parseFactor();
      expr = { kind: "Binary", operator, left: expr, right };
    }
    return expr;
  }

  parseFactor() {
    let expr = this.parseUnary();
    while (this.matchSymbol("*") || this.matchSymbol("/")) {
      const operator = this.previous().value;
      const right = this.parseUnary();
      expr = { kind: "Binary", operator, left: expr, right };
    }
    return expr;
  }

  parseUnary() {
    if (this.matchSymbol("-")) {
      return { kind: "Unary", operator: "-", expression: this.parseUnary() };
    }
    return this.parseCall();
  }

  parseCall() {
    let expr = this.parsePrimary();
    while (this.matchSymbol("(")) {
      const args = [];
      if (!this.checkSymbol(")")) {
        do {
          args.push(this.parseExpression());
        } while (this.matchSymbol(","));
      }
      this.consumeSymbol(")", "expected `)` after arguments");
      expr = { kind: "Call", callee: expr, args };
    }
    return expr;
  }

  parsePrimary() {
    if (this.match("number")) {
      return { kind: "Literal", value: this.previous().value };
    }
    if (this.match("string")) {
      return { kind: "Literal", value: this.previous().value };
    }
    if (this.matchKeyword("true") || this.matchKeyword("yes") || this.matchKeyword("hai")) {
      return { kind: "Literal", value: true };
    }
    if (this.matchKeyword("false") || this.matchKeyword("no") || this.matchKeyword("iie")) {
      return { kind: "Literal", value: false };
    }
    if (this.match("identifier")) {
      return { kind: "Variable", name: this.previous().value };
    }
    if (this.matchSymbol("(")) {
      const expr = this.parseExpression();
      this.consumeSymbol(")", "expected `)` after expression");
      return expr;
    }
    const token = this.peek();
    throw new FreakSubsetError(`expected expression at offset ${token.offset}`);
  }

  match(type) {
    if (!this.check(type)) {
      return false;
    }
    this.advance();
    return true;
  }

  matchKeyword(value) {
    if (!this.checkKeyword(value)) {
      return false;
    }
    this.advance();
    return true;
  }

  matchSymbol(value) {
    if (!this.checkSymbol(value)) {
      return false;
    }
    this.advance();
    return true;
  }

  consume(type, message) {
    if (this.check(type)) {
      return this.advance();
    }
    throw new FreakSubsetError(`${message} at offset ${this.peek().offset}`);
  }

  consumeKeyword(value, message) {
    if (this.checkKeyword(value)) {
      return this.advance();
    }
    throw new FreakSubsetError(`${message} at offset ${this.peek().offset}`);
  }

  consumeSymbol(value, message) {
    if (this.checkSymbol(value)) {
      return this.advance();
    }
    throw new FreakSubsetError(`${message} at offset ${this.peek().offset}`);
  }

  check(type) {
    return this.peek().type === type;
  }

  checkKeyword(value) {
    const token = this.peek();
    return token.type === "identifier" && token.value === value;
  }

  checkSymbol(value) {
    const token = this.peek();
    return token.type === "symbol" && token.value === value;
  }

  advance() {
    if (!this.check("eof")) {
      this.current += 1;
    }
    return this.previous();
  }

  peek() {
    return this.tokens[this.current];
  }

  previous() {
    return this.tokens[this.current - 1];
  }
}

export function createAcademyWorker(academyPackage, options = {}) {
  return {
    handleEnvelope(envelope) {
      return handleAcademyWorkerEnvelope(envelope, academyPackage, options);
    },
  };
}

export function createAcademyWasmEvaluator(wasmInstanceOrExports) {
  const exports = wasmInstanceOrExports?.exports ?? wasmInstanceOrExports?.instance?.exports ?? wasmInstanceOrExports;
  if (!isAcademyWasmEvaluatorExports(exports)) {
    throw new WorkerProtocolError("bad_request", "invalid Academy WASM evaluator exports");
  }
  if (exports.academy_protocol_version() !== PROTOCOL_VERSION) {
    throw new WorkerProtocolError("bad_protocol", "unsupported Academy WASM evaluator protocol version");
  }

  return {
    supportsLesson(lessonId) {
      return lessonId === "hello-freak" && exports.academy_supported_lesson_count() >= 1;
    },
    runHelloFreak(source) {
      return runHelloFreakWasm(exports, source);
    },
  };
}

export function handleAcademyWorkerEnvelope(envelope, academyPackage, options = {}) {
  const requestId = String(envelope?.requestId ?? "");
  if (envelope?.protocolVersion !== PROTOCOL_VERSION) {
    return responseError(requestId, "bad_protocol", "unsupported protocolVersion");
  }
  if (!requestId) {
    return responseError("", "bad_request", "requestId is required");
  }

  try {
    let result;
    switch (envelope.method) {
      case "package.info":
        requireParams(envelope);
        result = handlePackageInfo(academyPackage);
        break;
      case "check":
        result = handleCheck(requireParams(envelope), options);
        break;
      case "run":
        result = handleRun(requireParams(envelope), options);
        break;
      case "evaluateExercise":
        result = handleEvaluateExercise(requireParams(envelope), academyPackage, options);
        break;
      case "cancel":
        requireParams(envelope);
        result = { cancelled: true };
        break;
      default:
        throw new WorkerProtocolError("unknown_method", `unknown method: ${envelope.method}`);
    }
    return responseOk(requestId, result);
  } catch (error) {
    if (error instanceof WorkerProtocolError) {
      return responseError(requestId, error.code, error.message);
    }
    return responseError(requestId, "academy_error", error.message);
  }
}

export function parseFreakSubset(source) {
  try {
    const tokens = new Lexer(source).tokenize();
    const ast = new Parser(tokens).parseProgram();
    return { ok: true, ast, messages: [] };
  } catch (error) {
    return { ok: false, ast: null, messages: [error.message] };
  }
}

export function runFreakSubset(source, options = {}) {
  const parsed = parseFreakSubset(source);
  if (!parsed.ok) {
    return {
      ok: false,
      stdout: "",
      stderr: parsed.messages.join("\n"),
      returncode: 1,
      messages: parsed.messages,
    };
  }

  try {
    const state = {
      output: [],
      steps: 0,
      limits: { ...DEFAULT_LIMITS, ...(options.limits ?? {}) },
    };
    executeStatements(parsed.ast.statements, new Environment(), state);
    return {
      ok: true,
      stdout: state.output.join(""),
      stderr: "",
      returncode: 0,
      messages: [],
    };
  } catch (error) {
    return {
      ok: false,
      stdout: "",
      stderr: error.message,
      returncode: 1,
      messages: [error.message],
    };
  }
}

function responseOk(requestId, result) {
  return {
    protocolVersion: PROTOCOL_VERSION,
    requestId,
    ok: true,
    result,
  };
}

function responseError(requestId, code, message) {
  return {
    protocolVersion: PROTOCOL_VERSION,
    requestId,
    ok: false,
    error: { code, message },
  };
}

function requireParams(envelope) {
  if (typeof envelope?.params !== "object" || envelope.params === null || Array.isArray(envelope.params)) {
    throw new WorkerProtocolError("bad_request", "params must be an object");
  }
  return envelope.params;
}

function handlePackageInfo(academyPackage) {
  if (typeof academyPackage !== "object" || academyPackage === null) {
    throw new WorkerProtocolError("bad_request", "academy package is required");
  }
  return {
    packageId: academyPackage.packageId,
    languageVersion: academyPackage.languageVersion,
    compilerTrack: academyPackage.compilerTrack,
    workerProtocolVersion: academyPackage.workerProtocolVersion,
    courseCount: Array.isArray(academyPackage.courses) ? academyPackage.courses.length : 0,
  };
}

function handleCheck(params, options) {
  const source = requireString(params.source, "check requires string source");
  const wasmResult = maybeRunHelloFreakWasm(source, options, String(params.fileId ?? ""));
  if (wasmResult !== null) {
    return {
      ok: wasmResult.ok,
      messages: wasmResult.ok ? [] : wasmResult.messages,
    };
  }
  const result = runFreakSubset(source, options);
  return {
    ok: result.ok,
    messages: result.ok ? [] : result.messages,
  };
}

function handleRun(params, options) {
  const source = requireString(params.source, "run requires string source");
  const wasmResult = maybeRunHelloFreakWasm(source, options, String(params.fileId ?? ""));
  if (wasmResult !== null) {
    return wasmResult;
  }
  return runFreakSubset(source, options);
}

function handleEvaluateExercise(params, academyPackage, options) {
  const source = requireString(params.source, "evaluateExercise requires string source");
  const lessonId = requireString(params.lessonId, "evaluateExercise requires string lessonId");
  const lesson = findLesson(academyPackage, lessonId);
  const exercise = typeof params.exerciseId === "string" && params.exerciseId
    ? sectionById(lesson, params.exerciseId)
    : firstExercise(lesson);

  const results = evaluateRequirements(lesson, exercise, source, options);
  return {
    lessonId: lesson.id,
    exerciseId: exercise.id,
    passed: results.every((item) => item.passed),
    requirements: results,
  };
}

function requireString(value, message) {
  if (typeof value !== "string") {
    throw new WorkerProtocolError("bad_request", message);
  }
  return value;
}

function findLesson(academyPackage, lessonId) {
  for (const course of academyPackage?.courses ?? []) {
    for (const lesson of course.lessonData ?? []) {
      if (lesson.id === lessonId) {
        return lesson;
      }
    }
  }
  throw new WorkerProtocolError("academy_error", `Unknown Academy lesson: ${lessonId}`);
}

function lessonSections(lesson, type = null) {
  const sections = Array.isArray(lesson.sections) ? lesson.sections : [];
  return type === null ? sections : sections.filter((section) => section.type === type);
}

function firstExercise(lesson) {
  const exercises = lessonSections(lesson, "exercise");
  if (exercises.length === 0) {
    throw new WorkerProtocolError("academy_error", `Lesson \`${lesson.id}\` has no exercise section`);
  }
  return exercises[0];
}

function sectionById(lesson, sectionId) {
  const section = lessonSections(lesson).find((candidate) => candidate.id === sectionId);
  if (!section) {
    throw new WorkerProtocolError("academy_error", `Unknown section \`${sectionId}\` in lesson \`${lesson.id}\``);
  }
  return section;
}

function evaluateRequirements(lesson, exercise, source, options) {
  const requirements = Array.isArray(exercise.requirements) ? exercise.requirements : [];
  const wasmResult = maybeEvaluateHelloFreakWasm(lesson, exercise, source, options, requirements);
  if (wasmResult !== null) {
    return wasmResult;
  }

  const parsed = parseFreakSubset(source);
  let runResult = null;
  const ensureRun = () => {
    if (runResult === null) {
      runResult = runFreakSubset(source, options);
    }
    return runResult;
  };

  return requirements.map((requirement) => {
    const kind = requirement.kind;
    const id = requirement.id ?? kind;
    if (kind === "parses") {
      return {
        id,
        kind,
        passed: parsed.ok,
        message: parsed.ok ? "source parses" : parsed.messages.join("\n"),
      };
    }
    if (kind === "compiles") {
      const compiled = ensureRun();
      return {
        id,
        kind,
        passed: compiled.ok,
        message: compiled.ok ? "source compiles" : compiled.messages.join("\n"),
      };
    }
    if (kind === "expected_output") {
      const ran = ensureRun();
      const expected = String(requirement.expected ?? "");
      const actual = String(ran.stdout ?? "");
      const passed = ran.ok && actual === expected;
      let message;
      if (passed) {
        message = "output matches";
      } else if (!ran.ok) {
        message = ran.messages.join("\n");
      } else {
        message = `expected output ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`;
        message = message.replaceAll('"', "'");
      }
      return { id, kind, passed, message };
    }
    return {
      id,
      kind,
      passed: false,
      message: `requirement \`${kind}\` is not implemented in the browser-safe learner yet`,
    };
  });
}

function maybeEvaluateHelloFreakWasm(lesson, exercise, source, options, requirements) {
  if (lesson?.id !== "hello-freak" || exercise?.id !== "hello-exercise") {
    return null;
  }
  const evaluator = academyWasmEvaluatorFromOptions(options);
  if (evaluator === null || !evaluator.supportsLesson("hello-freak")) {
    return null;
  }

  const result = evaluator.runHelloFreak(source);
  return requirements.map((requirement) => {
    const kind = requirement.kind;
    const id = requirement.id ?? kind;
    if (kind === "parses") {
      return {
        id,
        kind,
        passed: result.parsed,
        message: result.parsed ? "source parses" : result.message,
      };
    }
    if (kind === "compiles") {
      return {
        id,
        kind,
        passed: result.compiled,
        message: result.compiled ? "source compiles" : result.message,
      };
    }
    if (kind === "expected_output") {
      const expected = String(requirement.expected ?? "");
      const passed = result.ok && result.stdout === expected;
      let message;
      if (passed) {
        message = "output matches";
      } else if (!result.ok && !result.ran) {
        message = result.message;
      } else {
        message = `expected output ${JSON.stringify(expected)}, got ${JSON.stringify(result.stdout)}`;
        message = message.replaceAll('"', "'");
      }
      return { id, kind, passed, message };
    }
    return {
      id,
      kind,
      passed: false,
      message: `requirement \`${kind}\` is not implemented in the WASM learner yet`,
    };
  });
}

function maybeRunHelloFreakWasm(source, options, fileId) {
  if (fileId !== "hello-freak.fk") {
    return null;
  }
  const evaluator = academyWasmEvaluatorFromOptions(options);
  if (evaluator === null || !evaluator.supportsLesson("hello-freak")) {
    return null;
  }

  const result = evaluator.runHelloFreak(source);
  return {
    ok: result.ok,
    stdout: result.stdout,
    stderr: result.ok ? "" : result.message,
    returncode: result.ok ? 0 : 1,
    messages: result.ok ? [] : [result.message],
  };
}

function academyWasmEvaluatorFromOptions(options) {
  if (!options?.wasmEvaluator) {
    return null;
  }
  if (typeof options.wasmEvaluator.runHelloFreak === "function") {
    return options.wasmEvaluator;
  }
  return createAcademyWasmEvaluator(options.wasmEvaluator);
}

function isAcademyWasmEvaluatorExports(exports) {
  return Boolean(
    exports &&
    exports.memory instanceof WebAssembly.Memory &&
    typeof exports.academy_protocol_version === "function" &&
    typeof exports.academy_supported_lesson_count === "function" &&
    typeof exports.academy_input_offset === "function" &&
    typeof exports.academy_input_capacity === "function" &&
    typeof exports.academy_last_stdout_offset === "function" &&
    typeof exports.academy_last_stdout_length === "function" &&
    typeof exports.academy_last_message_offset === "function" &&
    typeof exports.academy_last_message_length === "function" &&
    typeof exports.academy_evaluate_hello_freak === "function"
  );
}

function runHelloFreakWasm(exports, source) {
  const encoded = TEXT_ENCODER.encode(source);
  const inputOffset = exports.academy_input_offset();
  const inputCapacity = exports.academy_input_capacity();
  if (encoded.length > inputCapacity) {
    return {
      ok: false,
      parsed: false,
      compiled: false,
      ran: false,
      outputMatched: false,
      stdout: "",
      message: "source exceeds WASM input capacity",
    };
  }

  new Uint8Array(exports.memory.buffer, inputOffset, inputCapacity).fill(0);
  new Uint8Array(exports.memory.buffer, inputOffset, encoded.length).set(encoded);

  const status = exports.academy_evaluate_hello_freak(encoded.length);
  const stdout = readWasmString(
    exports.memory,
    exports.academy_last_stdout_offset(),
    exports.academy_last_stdout_length(),
  );
  const message = readWasmString(
    exports.memory,
    exports.academy_last_message_offset(),
    exports.academy_last_message_length(),
  );
  const parsed = (status & WASM_STATUS_PARSES) !== 0;
  const compiled = (status & WASM_STATUS_COMPILES) !== 0;
  const ran = (status & WASM_STATUS_RUNS) !== 0;
  const outputMatched = (status & WASM_STATUS_OUTPUT_MATCHES) !== 0;

  return {
    ok: parsed && compiled && ran,
    parsed,
    compiled,
    ran,
    outputMatched,
    stdout,
    message,
  };
}

function readWasmString(memory, offset, length) {
  if (length <= 0) {
    return "";
  }
  return TEXT_DECODER.decode(new Uint8Array(memory.buffer, offset, length));
}

function executeStatements(statements, env, state) {
  for (const statement of statements) {
    executeStatement(statement, env, state);
  }
}

function executeStatement(statement, env, state) {
  tick(state);
  switch (statement.kind) {
    case "Pilot": {
      const value = evaluateExpression(statement.initializer, env, state);
      enforceType(statement.typeName, value);
      env.define(statement.name, value);
      return;
    }
    case "Say": {
      state.output.push(`${formatValue(evaluateExpression(statement.expression, env, state))}\n`);
      return;
    }
    case "Repeat": {
      const count = evaluateExpression(statement.count, env, state);
      if (!Number.isInteger(count) || count < 0) {
        throw new FreakSubsetError("repeat count must be a non-negative int");
      }
      if (count > state.limits.maxLoopIterations) {
        throw new FreakSubsetError(`repeat count exceeds browser-safe limit: ${count}`);
      }
      for (let i = 0; i < count; i += 1) {
        executeStatements(statement.body, new Environment(env), state);
      }
      return;
    }
    case "If": {
      const condition = evaluateExpression(statement.condition, env, state);
      if (typeof condition !== "boolean") {
        throw new FreakSubsetError("if condition must be bool");
      }
      executeStatements(condition ? statement.thenBranch : statement.elseBranch, new Environment(env), state);
      return;
    }
    case "Task": {
      env.define(statement.name, { kind: "UserFunction", declaration: statement, closure: env });
      return;
    }
    case "GiveBack": {
      throw new ReturnSignal(evaluateExpression(statement.expression, env, state));
    }
    default:
      throw new FreakSubsetError(`unsupported statement kind: ${statement.kind}`);
  }
}

function evaluateExpression(expression, env, state) {
  tick(state);
  switch (expression.kind) {
    case "Literal":
      return expression.value;
    case "Variable":
      return env.get(expression.name);
    case "Unary": {
      const value = evaluateExpression(expression.expression, env, state);
      if (expression.operator === "-" && typeof value === "number") {
        return -value;
      }
      throw new FreakSubsetError(`unsupported unary operator: ${expression.operator}`);
    }
    case "Binary":
      return evaluateBinary(
        expression.operator,
        evaluateExpression(expression.left, env, state),
        evaluateExpression(expression.right, env, state),
      );
    case "Call":
      return evaluateCall(expression, env, state);
    default:
      throw new FreakSubsetError(`unsupported expression kind: ${expression.kind}`);
  }
}

function evaluateBinary(operator, left, right) {
  switch (operator) {
    case "+":
      if (typeof left === "string" || typeof right === "string") {
        return `${formatValue(left)}${formatValue(right)}`;
      }
      requireNumbers(operator, left, right);
      return left + right;
    case "-":
      requireNumbers(operator, left, right);
      return left - right;
    case "*":
      requireNumbers(operator, left, right);
      return left * right;
    case "/":
      requireNumbers(operator, left, right);
      return left / right;
    case ">":
      requireNumbers(operator, left, right);
      return left > right;
    case ">=":
      requireNumbers(operator, left, right);
      return left >= right;
    case "<":
      requireNumbers(operator, left, right);
      return left < right;
    case "<=":
      requireNumbers(operator, left, right);
      return left <= right;
    case "==":
      return left === right;
    case "!=":
      return left !== right;
    default:
      throw new FreakSubsetError(`unsupported binary operator: ${operator}`);
  }
}

function evaluateCall(expression, env, state) {
  if (expression.callee.kind !== "Variable") {
    throw new FreakSubsetError("only direct task calls are supported");
  }
  const fn = env.get(expression.callee.name);
  if (fn?.kind !== "UserFunction") {
    throw new FreakSubsetError(`not a task: ${expression.callee.name}`);
  }
  const declaration = fn.declaration;
  if (expression.args.length !== declaration.params.length) {
    throw new FreakSubsetError(
      `task ${declaration.name} expected ${declaration.params.length} argument(s), got ${expression.args.length}`,
    );
  }
  const callEnv = new Environment(fn.closure);
  for (let i = 0; i < declaration.params.length; i += 1) {
    const value = evaluateExpression(expression.args[i], env, state);
    enforceType(declaration.params[i].typeName, value);
    callEnv.define(declaration.params[i].name, value);
  }

  try {
    executeStatements(declaration.body, callEnv, state);
  } catch (signal) {
    if (signal instanceof ReturnSignal) {
      enforceType(declaration.returnType, signal.value);
      return signal.value;
    }
    throw signal;
  }
  if (declaration.returnType && declaration.returnType !== "void") {
    throw new FreakSubsetError(`task ${declaration.name} did not give back a value`);
  }
  return null;
}

function enforceType(typeName, value) {
  if (!typeName) {
    return;
  }
  if (typeName === "int" && Number.isInteger(value)) {
    return;
  }
  if (typeName === "word" && typeof value === "string") {
    return;
  }
  if (typeName === "bool" && typeof value === "boolean") {
    return;
  }
  if (typeName === "num" && typeof value === "number") {
    return;
  }
  if (typeName === "void" && value === null) {
    return;
  }
  throw new FreakSubsetError(`value does not match type ${typeName}`);
}

function requireNumbers(operator, left, right) {
  if (typeof left !== "number" || typeof right !== "number") {
    throw new FreakSubsetError(`operator ${operator} requires numbers`);
  }
}

function formatValue(value) {
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "number" && Number.isInteger(value)) {
    return String(value);
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

function tick(state) {
  state.steps += 1;
  if (state.steps > state.limits.maxSteps) {
    throw new FreakSubsetError("browser-safe execution step limit exceeded");
  }
}
