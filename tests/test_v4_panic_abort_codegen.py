"""Pure adversarial controls for authored panic compiler/native oracles."""
import importlib.util
import ast
from pathlib import Path
import signal
from types import SimpleNamespace
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('panic_gate',Path(__file__).with_name('v4_panic_abort_codegen.py'))
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
class PanicAbortOracle(unittest.TestCase):
    def result(self,stdout='',stderr='',code=0):return SimpleNamespace(returncode=code,stdout=stdout,stderr=stderr)
    def test_fatal_exact_unicode_nul(self):
        case=gate.cases()[0];gate.assert_case(self.result(stderr='PANIC: '+case.message+'\n',code=-signal.SIGABRT),case,platform='linux')
    def test_wrong_signal_exit_and_error(self):
        case=gate.cases()[0]
        for code in (0,1,3,-11,85,86,87,88):
            with self.subTest(code=code),self.assertRaises(RuntimeError):gate.assert_case(self.result(stderr='PANIC: '+case.message+'\n',code=code),case,platform='linux')
        for stderr in ('PANIC: wrong\n','PANIC: '+case.message+'\nextra','AddressSanitizer\n','PANIC: '+case.message.replace('\0','')+'\n'):
            with self.subTest(stderr=stderr),self.assertRaises(RuntimeError):gate.assert_case(self.result(stderr=stderr,code=-signal.SIGABRT),case,platform='linux')
    def test_fatal_raw_crlf_never_normalized(self):
        case=gate.cases()[1]
        for platform,code in (('linux',-signal.SIGABRT),('darwin',-signal.SIGABRT),('win32',3)):
            with self.subTest(platform=platform),self.assertRaises(RuntimeError):gate.assert_case(self.result(stderr='PANIC: \r\n',code=code),case,platform=platform)
    def test_prior_effects_exact(self):
        case=gate.cases()[2]
        gate.assert_case(self.result('first\n','PANIC: binary\n',-signal.SIGABRT),case,platform='linux')
        for stdout in ('','first\nfirst\n','first\r\n','first\nsuppressed\n'):
            with self.subTest(stdout=stdout),self.assertRaises(RuntimeError):gate.assert_case(self.result(stdout,'PANIC: binary\n',-signal.SIGABRT),case,platform='linux')
    def test_happy_audit_sanitizer_and_extra_output_rejected(self):
        case=next(c for c in gate.cases() if c.name=='short-happy')
        gate.assert_case(self.result('owned\n'),case,platform='linux')
        for result in (self.result('owned\n',code=87),self.result('owned\n','audit\n'),self.result('owned\nextra\n'),self.result('owned\r\n')):
            with self.assertRaises(RuntimeError):gate.assert_case(result,case,platform='linux')
    def test_module_protocol_strict(self):
        text=gate.PREFIX+'@@LLVM-MODULE-BEGIN\ndefine void @x() { unreachable }\n@@LLVM-MODULE-END\n'
        self.assertTrue(gate.extract_module(self.result(text),platform='linux'))
        for bad in (text+'extra\n',text.replace('v9-restore=true','v9-restore=false'),text.replace('old-seal=true','old-seal=false'),text.replace('fresh-module=true','fresh-module=false'),text.replace('\n','\r\n'),text.replace('define void @x() { unreachable }','')):
            with self.subTest(bad=bad),self.assertRaises(RuntimeError):gate.extract_module(self.result(bad),platform='linux')
    def report(self):
        rows=[]
        for case in gate.cases():
            for opt in gate.OPTS:
                stderr='' if case.message is None else 'PANIC: '+case.message+'\n'
                rows.append({'name':case.name,'optimization':opt,'status':'pass','ownership_audits':['C','LLVM'],'policy':'abort','exit':0 if case.message is None else -signal.SIGABRT,'stdout_sha256':gate.hashlib.sha256(case.stdout.encode()).hexdigest(),'stderr_sha256':gate.hashlib.sha256(stderr.encode()).hexdigest()})
        controls=[{'name':f'audit-{kind}-O{opt}','status':'pass'} for kind in ('C','LLVM') for opt in gate.OPTS]+[{'name':'sanitizer-'+kind,'status':'pass'} for kind in ('address','undefined')]
        return {'platform':'linux','sanitizers':True,'programs':rows,'controls':controls}
    def test_complete_matrix_and_controls_required(self):
        report=self.report();gate.validate_report(report,sanitize=True)
        for key in ('programs','controls'):
            broken=self.report();broken[key].pop()
            with self.assertRaises(RuntimeError):gate.validate_report(broken,sanitize=True)
        broken=self.report();broken['programs'][-1]=broken['programs'][0]
        with self.assertRaises(RuntimeError):gate.validate_report(broken,sanitize=True)
    def test_report_wrong_policy_audit_output_or_mode_rejected(self):
        for key,value in (('policy','unwind'),('ownership_audits',['LLVM']),('exit',1),('stderr_sha256','wrong'),('status','skip')):
            report=self.report();report['programs'][0][key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):gate.validate_report(report,sanitize=True)
        report=self.report();report['sanitizers']=False
        with self.assertRaises(RuntimeError):gate.validate_report(report,sanitize=True)
    def test_assignment_and_method_order_oracles(self):
        table={case.name:case for case in gate.cases()}
        assignment=table['assignment-rhs-before-address']
        method=table['raw-write-receiver-before-value']
        gate.assert_case(self.result(assignment.stdout),assignment,platform='linux')
        gate.assert_case(self.result(method.stdout),method,platform='linux')
        for case,wrong in ((assignment,'address\n3\nrhs\n3\n'),(method,'consume\n3\naddress\n3\n7\n')):
            with self.subTest(case=case.name),self.assertRaises(RuntimeError):gate.assert_case(self.result(wrong),case,platform='linux')
            with self.subTest(case=case.name),self.assertRaises(RuntimeError):gate.assert_case(self.result(case.stdout,'FREAK: unavailable word\n',1),case,platform='linux')
    def test_native_link_uses_emitted_target_and_keeps_strict_guards(self):
        tree=ast.parse(Path(gate.__file__).read_text(encoding='utf-8'))
        run_gate=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='run_gate')
        calls=[node for node in ast.walk(run_gate) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='run' and len(node.args)>1 and isinstance(node.args[1],ast.JoinedStr) and any(isinstance(part,ast.Constant) and part.value=='panic link ' for part in node.args[1].values)]
        self.assertEqual(len(calls),1)
        command=compile(ast.Expression(calls[0].args[0]),gate.__file__,'eval')
        for target,libraries in (('x86_64-unknown-linux-gnu',['-lm']),('aarch64-apple-darwin',[]),('x86_64-pc-windows-msvc',['user32.lib'])):
            with self.subTest(target=target):
                flags=['-O3',*gate.AUDIT_FLAGS,*gate.SANITIZER_FLAGS]
                values={'args':SimpleNamespace(clang='clang'),'target':target,'flags':flags,'llvm':Path('module.ll'),'objects':{3:['runtime.O3.o']},'opt':3,'binary':Path('program.native'),'checks':SimpleNamespace(runtime_platform_final_link_args=lambda:libraries),'str':str}
                argv=eval(command,{'__builtins__':{}},values)
                self.assertEqual(argv,['clang','--target='+target,*flags,'module.ll','runtime.O3.o','-o','program.native',*libraries])
                self.assertFalse(any(value=='-w' or value.startswith('-Wno-') for value in argv))
        self.assertEqual({keyword.arg:ast.literal_eval(keyword.value) for keyword in calls[0].keywords},{'timeout':120,'memory':512})
        self.assertIn('require_native_link(result, target)',ast.get_source_segment(Path(gate.__file__).read_text(encoding='utf-8'),run_gate))

    def test_native_link_source_reads_ignore_default_encoding(self):
        read_text = Path.read_text
        def windows_read_text(path, encoding=None, errors=None):
            return read_text(path, encoding=encoding or 'cp1252', errors=errors)
        with patch.object(Path, 'read_text', windows_read_text):
            self.test_native_link_uses_emitted_target_and_keeps_strict_guards()

    def test_runtime_objects_and_controls_share_generated_module_target(self):
        tree = ast.parse(Path(gate.__file__).read_text(encoding='utf-8'))
        run_gate = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run_gate')
        calls = {}
        for node in ast.walk(run_gate):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'run' and len(node.args) > 1):
                continue
            label = node.args[1]
            if isinstance(label, ast.JoinedStr):
                label = label.values[0]
            if isinstance(label, ast.Constant) and label.value in ('panic runtime ', 'panic audit link O', 'panic sanitizer link', 'panic link '):
                self.assertNotIn(label.value, calls)
                calls[label.value] = node
        self.assertEqual(set(calls), {'panic runtime ', 'panic audit link O', 'panic sanitizer link', 'panic link '})
        for target, libraries in (('x86_64-w64-windows-gnu', ['-lws2_32', '-lshell32']),
                                  ('x86_64-unknown-linux-gnu', ['-lm']), ('aarch64-apple-darwin', [])):
            for sanitized in (False, True):
                for opt in gate.OPTS:
                    flags = ['-w', f'-O{opt}', '-Iruntime', *gate.AUDIT_FLAGS]
                    if sanitized: flags += list(gate.SANITIZER_FLAGS)
                    native_flags = [f'-O{opt}', *gate.AUDIT_FLAGS]
                    if sanitized: native_flags += list(gate.SANITIZER_FLAGS)
                    values = {'args': SimpleNamespace(clang='clang'), 'target': target, 'flags': flags,
                              'path': Path('runtime.c'), 'output': Path('runtime.obj'), 'audit': Path('audit.c'),
                              'probe': Path('sanitizer.c'), 'llvm': Path('module.ll'), 'objects': {opt: ['runtime.obj']},
                              'opt': opt, 'binary': Path('program.native'), 'str': str,
                              'SANITIZER_FLAGS': gate.SANITIZER_FLAGS,
                              'checks': SimpleNamespace(runtime_platform_final_link_args=lambda: libraries)}
                    expected = {
                        'panic runtime ': [*flags, '-c', 'runtime.c', '-o', 'runtime.obj'],
                        'panic audit link O': [*flags, 'audit.c', 'runtime.obj', '-o', 'program.native', *libraries],
                        'panic sanitizer link': ['-O0', *gate.SANITIZER_FLAGS, 'sanitizer.c', '-o', 'program.native'],
                        'panic link ': [*native_flags, 'module.ll', 'runtime.obj', '-o', 'program.native', *libraries],
                    }
                    for label, call in calls.items():
                        with self.subTest(target=target, sanitized=sanitized, opt=opt, stage=label):
                            values['flags'] = native_flags if label == 'panic link ' else flags
                            command = compile(ast.Expression(call.args[0]), gate.__file__, 'eval')
                            argv = eval(command, {'__builtins__': {}}, values)
                            self.assertEqual(argv, ['clang', '--target=' + target, *expected[label]])
                            self.assertEqual({keyword.arg: ast.literal_eval(keyword.value) for keyword in call.keywords}, {'timeout': 120, 'memory': 512})

    def test_corrupt_windows_link_directives_remain_fatal(self):
        warning = 'Warning: corrupt .drectve at end of def file\r\n'
        for target in ('x86_64-w64-windows-gnu', 'x86_64-pc-windows-msvc'):
            for stderr in (warning, warning * 3, warning.replace('\r\n', '\n')):
                with self.subTest(target=target, stderr=stderr), self.assertRaises(RuntimeError):
                    gate.require_native_link(self.result(stderr=stderr), target, platform='win32')

    def test_link_allows_only_same_architecture_darwin_canonicalization(self):
        warning = ('warning: overriding the module target triple with arm64-apple-macosx26.0.0 '
                   '[-Woverride-module]\n1 warning generated.\n')
        gate.require_native_link(self.result(), 'aarch64-apple-darwin', platform='darwin')
        gate.require_native_link(self.result(stderr=warning), 'aarch64-apple-darwin', platform='darwin')
        bad_results = [self.result(stderr=warning, code=1), self.result(stdout='extra', stderr=warning),
                       self.result(stderr=warning + 'extra\n'),
                       self.result(stderr=warning.replace('arm64-', 'x86_64-')),
                       self.result(stderr=warning.replace('macosx26.0.0', 'ios26.0.0')),
                       self.result(stderr=warning.replace('[-Woverride-module]', '[-Wother]')),
                       self.result(stderr=warning.replace('1 warning', '2 warnings')),
                       self.result(stderr='warning: unrelated\n'), self.result(stderr='runtime error: overflow\n')]
        for actual in bad_results:
            with self.subTest(actual=actual), self.assertRaises(RuntimeError):
                gate.require_native_link(actual, 'aarch64-apple-darwin', platform='darwin')
        for platform, target in (('linux', 'aarch64-apple-darwin'), ('win32', 'aarch64-apple-darwin'),
                                 ('darwin', 'x86_64-unknown-linux-gnu'), ('darwin', 'x86_64-pc-windows-msvc')):
            with self.subTest(platform=platform, target=target), self.assertRaises(RuntimeError):
                gate.require_native_link(self.result(stderr=warning), target, platform=platform)
if __name__=='__main__':unittest.main()
