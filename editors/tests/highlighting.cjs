const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { Registry, parseRawGrammar } = require('vscode-textmate');
const oniguruma = require('vscode-oniguruma');

(async () => {
  await oniguruma.loadWASM(fs.readFileSync(require.resolve('vscode-oniguruma/release/onig.wasm')).buffer);
  const file = path.join(__dirname, '../vscode/freak-lang/syntaxes/freak.tmLanguage.json');
  const registry = new Registry({
    onigLib: Promise.resolve({
      createOnigScanner: patterns => new oniguruma.OnigScanner(patterns),
      createOnigString: text => new oniguruma.OnigString(text),
    }),
    loadGrammar: async () => parseRawGrammar(fs.readFileSync(file, 'utf8'), file),
  });
  const grammar = await registry.loadGrammar('source.freak');
  const cases = [
    ['pilot answer: int = 42', 'pilot', 'keyword.declaration.freak'],
    ['pilot answer: int = 42', 'int', 'storage.type.freak'],
    ['pilot answer: int = 42', '42', 'constant.numeric.integer.freak'],
    ['task greet(name: word) -> void {', 'greet', 'entity.name.function.freak'],
    ['-- pilot answer = 42', 'pilot', 'comment.line.freak'],
    ['say "Hello, {name}!"', 'Hello', 'string.quoted.double.freak'],
    ['say "Hello, {name}!"', '{name}', 'variable.other.freak'],
    ['pilot ready = hai', 'hai', 'constant.language.boolean.freak'],
    ['give back answer', 'give back', 'keyword.control.freak'],
  ];
  for (const [line, text, scope] of cases) {
    const offset = line.indexOf(text);
    const token = grammar.tokenizeLine(line).tokens.find(t => t.startIndex <= offset && t.endIndex > offset);
    assert(token?.scopes.includes(scope), `${text}: expected ${scope}, got ${JSON.stringify(token)}`);
  }
  registry.dispose();
  console.log(`VS Code: ${cases.length} TextMate token checks passed`);
})().catch(error => { console.error(error); process.exitCode = 1; });
