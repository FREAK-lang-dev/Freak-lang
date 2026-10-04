"""Pure strict-oracle controls; these tests launch no compiler/native processes."""
import ast
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('sum_gate', Path(__file__).with_name('v4_scalar_sum_codegen.py'))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ScalarSumOracle(unittest.TestCase):
    def result(self, stdout='', stderr='', code=0):
        return SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)

    def test_all_ten_cases_require_exact_output_exit_and_audits(self):
        self.assertEqual(len(gate.cases()), 10)
        self.assertEqual(len({c.name for c in gate.cases()}), 10)
        for case in gate.cases():
            gate.assert_case(self.result(case.stdout), case, platform='linux')
            for bad in (self.result(case.stdout, code=86), self.result(case.stdout, code=87),
                        self.result(case.stdout, code=-11), self.result(case.stdout, 'audit\n'),
                        self.result(case.stdout+'extra\n')):
                with self.subTest(case=case.name), self.assertRaises(RuntimeError):
                    gate.assert_case(bad, case, platform='linux')

    def test_nul_empty_and_unicode_are_preserved(self):
        case = next(c for c in gate.cases() if c.name=='result-empty-unicode-nul')
        self.assertTrue(case.stdout.startswith('\n'))
        self.assertIn('\0', case.stdout)
        for bad in (case.stdout.replace('\0',''), case.stdout[1:], case.stdout.replace('𐐀','?')):
            with self.assertRaises(RuntimeError):
                gate.assert_case(self.result(bad), case, platform='linux')

    def test_crlf_is_platform_specific(self):
        case = gate.cases()[0]
        for platform in ('linux','darwin'):
            with self.subTest(platform=platform), self.assertRaises(RuntimeError):
                gate.assert_case(self.result(case.stdout.replace('\n','\r\n')), case, platform=platform)
        gate.assert_case(self.result(case.stdout.replace('\n','\r\n')), case, platform='win32')

    def test_module_protocol_has_one_frame_and_exact_restore_facts(self):
        text = gate.PREFIX+'@@LLVM-MODULE-BEGIN\ndefine i64 @x() { ret i64 0 }\n@@LLVM-MODULE-END\n'
        self.assertIn('define', gate.extract_module(self.result(text), platform='linux'))
        for bad in (text+'extra\n', text.replace('v9-restore=true','v9-restore=false'),
                    text.replace('old-seal=true','old-seal=false'), text.replace('fresh-module=true','fresh-module=false'),
                    text.replace('\n','\r\n'), text.replace('define i64 @x() { ret i64 0 }','')):
            with self.assertRaises(RuntimeError):
                gate.extract_module(self.result(bad), platform='linux')
        for result in (self.result(text, 'frontend\n'), self.result(text, code=1)):
            with self.assertRaises(RuntimeError): gate.extract_module(result, platform='linux')

    def report(self):
        rows = [{'name':case.name,'optimization':opt,'status':'pass','ownership_audits':['C','LLVM'],
                 'policy':'abort','exit':0,'stdout_sha256':gate.hashlib.sha256(case.stdout.encode()).hexdigest(),
                 'stderr_sha256':gate.hashlib.sha256(b'').hexdigest()}
                for case in gate.cases() for opt in gate.OPTS]
        controls = [{'name':f'audit-{kind}-O{opt}','status':'pass'} for kind in ('C','LLVM') for opt in gate.OPTS]
        controls += [{'name':'sanitizer-'+kind,'status':'pass'} for kind in ('address','undefined')]
        return {'platform':'linux','sanitizers':True,'programs':rows,'controls':controls}

    def test_30_program_matrix_and_eight_capability_controls_are_mandatory(self):
        report=self.report()
        gate.validate_report(report,sanitize=True)
        self.assertEqual(len(report['programs']),30)
        self.assertEqual(len(report['controls']),8)
        for key in ('programs','controls'):
            bad=copy.deepcopy(report);bad[key].pop()
            with self.assertRaises(RuntimeError): gate.validate_report(bad,sanitize=True)
        bad=copy.deepcopy(report);bad['programs'][-1]=bad['programs'][0]
        with self.assertRaises(RuntimeError): gate.validate_report(bad,sanitize=True)

    def test_no_wrong_status_policy_output_audit_or_sanitizer_mode(self):
        for key,value in (('exit',86),('status','skip'),('policy','unwind'),
                          ('ownership_audits',['LLVM']),('stdout_sha256','wrong'),('stderr_sha256','wrong')):
            report=self.report();report['programs'][0][key]=value
            with self.subTest(key=key), self.assertRaises(RuntimeError): gate.validate_report(report,sanitize=True)
        report=self.report();report['sanitizers']=False
        with self.assertRaises(RuntimeError): gate.validate_report(report,sanitize=True)

    def test_native_link_matches_emitted_target_and_strict_caps(self):
        source=Path(gate.__file__).read_text()
        run=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='run_gate')
        call=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                  and n.func.attr=='run' and len(n.args)>1 and isinstance(n.args[1],ast.JoinedStr)
                  and any(isinstance(p,ast.Constant) and p.value=='scalar Sum link ' for p in n.args[1].values))
        argv=compile(ast.Expression(call.args[0]),gate.__file__,'eval')
        for target,libraries in (('x86_64-unknown-linux-gnu',['-lm']),('aarch64-apple-darwin',[]),('x86_64-pc-windows-msvc',['user32.lib'])):
            flags=['-O3',*gate.AUDIT_FLAGS,*gate.SANITIZER_FLAGS]
            values={'args':SimpleNamespace(clang='clang'),'target':target,'flags':flags,'llvm':Path('module.ll'),
                    'objects':{3:['runtime.o']},'opt':3,'binary':Path('program'),
                    'checks':SimpleNamespace(runtime_platform_final_link_args=lambda:libraries),'str':str}
            self.assertEqual(eval(argv,{'__builtins__':{}},values),['clang','--target='+target,*flags,'module.ll','runtime.o','-o','program',*libraries])
        self.assertEqual({k.arg:ast.literal_eval(k.value) for k in call.keywords},{'timeout':120,'memory':512})
        self.assertIn('if result.returncode!=0 or result.stdout or result.stderr',ast.get_source_segment(source,run))

    def test_bootstrap_forwarder_preserves_original_options_and_restores(self):
        calls=[]
        def original(*args, **kwargs): calls.append((args,kwargs));return 'original-result'
        checks=SimpleNamespace(run_with_heartbeat=original)
        command=['clang','-O0','-DFREAK_ARRAY_LIVE_LIMIT=1024','compiler.c']
        with gate.bounded_bootstrap_compile(checks):
            self.assertEqual(checks.run_with_heartbeat(command, 'description', memory_limit_mb=1024, output_limit_mb=8), 'original-result')
        self.assertIs(checks.run_with_heartbeat,original)
        self.assertEqual(calls,[((command,'description'),{'memory_limit_mb':1024,'output_limit_mb':8,'timeout_seconds':120})])
        with self.assertRaises(KeyboardInterrupt):
            with gate.bounded_bootstrap_compile(checks): raise KeyboardInterrupt()
        self.assertIs(checks.run_with_heartbeat,original)

    def test_bootstrap_forwarder_rejects_changed_caps_before_forwarding(self):
        def forbidden(*args, **kwargs): raise AssertionError('unexpected original call')
        checks=SimpleNamespace(run_with_heartbeat=forbidden)
        for command,options in ((['clang'],{'memory_limit_mb':1024}),
                                (['clang','-DFREAK_ARRAY_LIVE_LIMIT=1024'],{'memory_limit_mb':2048}),
                                (['clang','-DFREAK_ARRAY_LIVE_LIMIT=1024'],{'memory_limit_mb':1024,'timeout_seconds':180})):
            with self.assertRaises(RuntimeError):
                with gate.bounded_bootstrap_compile(checks): checks.run_with_heartbeat(command,**options)
            self.assertIs(checks.run_with_heartbeat,forbidden)

    def test_primary_failure_survives_report_publication_failure(self):
        for original in (RuntimeError('primary'), KeyboardInterrupt('primary'), MemoryError('primary')):
            with patch.object(gate,'run_gate',side_effect=original), patch.object(Path,'mkdir'), patch.object(Path,'write_text',side_effect=OSError('secondary')):
                with self.assertRaises(type(original)) as caught:
                    gate.main(['--clang','unused-clang','--work','unused-work'])
                self.assertIs(caught.exception,original)
        with patch.object(gate,'run_gate'), patch.object(Path,'mkdir'), patch.object(Path,'write_text',side_effect=OSError('publication')):
            with self.assertRaises(OSError): gate.main(['--clang','unused-clang','--work','unused-work'])

    def test_operator_target_forwarding_matches_real_word_interfaces(self):
        from freakc.parser import Parser
        root = Path(gate.__file__).resolve().parents[1]
        fixture = Parser.from_source((root/'src/compiler/v4/tests/scalar_sum_operator_smoke.fk').read_text())
        target = Parser.from_source((root/'src/compiler/v4/crates/freak_target/src/lib.fk').read_text())
        llvm = Parser.from_source((root/'src/compiler/v4/crates/freak_codegen_llvm/src/lib.fk').read_text())
        def task(program, name):
            return next(node for node in program.statements if type(node).__name__=='TaskDecl' and node.name==name)
        make_target=task(target,'v4_target_spec_new')
        module_text=task(llvm,'v4_codegen_llvm_module_text')
        helper=task(fixture,'v4_sum_operator_rejected')
        caller=task(fixture,'v4_sum_operator_run')
        def walk(node):
            yield node
            if isinstance(node,(list,tuple)):
                for child in node: yield from walk(child)
            elif hasattr(node,'__dict__'):
                for child in vars(node).values(): yield from walk(child)
        def consistent(candidate):
            declared=candidate.params[1].type_ann.name
            if declared != make_target.return_type.name or declared != module_text.params[1].type_ann.name:
                raise RuntimeError('operator target forwarding disagrees with real target/module interfaces')
        consistent(helper)
        forwarding=[node for node in walk(helper.body) if type(node).__name__=='Call' and type(node.func).__name__=='Ident' and node.func.name=='v4_codegen_llvm_module_text']
        self.assertEqual(len(forwarding),1)
        self.assertEqual(forwarding[0].args[1].name,helper.params[1].name)
        binding=next(node for node in walk(caller.body) if type(node).__name__=='PilotDecl' and node.name=='target')
        self.assertEqual(binding.value.func.name,'v4_target_spec_new')
        calls=[node for node in walk(caller.body) if type(node).__name__=='Call' and type(node.func).__name__=='Ident' and node.func.name==helper.name]
        self.assertTrue(calls)
        self.assertTrue(all(node.args[1].name=='target' for node in calls))
        old=copy.deepcopy(helper);old.params[1].type_ann.name='int'
        with self.assertRaises(RuntimeError): consistent(old)


if __name__=='__main__': unittest.main()
