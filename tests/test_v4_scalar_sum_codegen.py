"""Pure strict-oracle controls; these tests launch no compiler/native processes."""
import ast
import copy
import importlib.util
import io
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import SimpleNamespace
from tempfile import TemporaryDirectory
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
        source=Path(gate.__file__).read_text(encoding='utf-8')
        run=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='run_gate')
        call=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                  and n.func.attr=='run' and len(n.args)>1 and isinstance(n.args[1],ast.JoinedStr)
                  and any(isinstance(p,ast.Constant) and p.value=='scalar Sum link ' for p in n.args[1].values))
        argv=compile(ast.Expression(call.args[0]),gate.__file__,'eval')
        for target,libraries in (('x86_64-unknown-linux-gnu',['-lm']),('aarch64-unknown-linux-gnu',['-lm']),
                                 ('aarch64-apple-darwin',[]),('x86_64-w64-windows-gnu',['-luser32'])):
            flags=['-O3',*gate.AUDIT_FLAGS,*gate.SANITIZER_FLAGS]
            values={'args':SimpleNamespace(clang='clang'),'target':target,'flags':flags,'llvm':Path('module.ll'),
                    'objects':{3:['runtime.o']},'opt':3,'binary':Path('program'),
                    'link_target':'arm64-apple-macosx15.0.0' if target=='aarch64-apple-darwin' else target,
                    'link_llvm':Path('module.link.ll') if target=='aarch64-apple-darwin' else Path('module.ll'),
                    'checks':SimpleNamespace(runtime_platform_final_link_args=lambda:libraries),'str':str}
            expected=['clang','--target='+values['link_target'],*flags,str(values['link_llvm']),'runtime.o','-o','program',*libraries]
            self.assertEqual(eval(argv,{'__builtins__':{}},values),expected)
            self.assertNotIn('-Xclang',expected)
            if target=='aarch64-apple-darwin':
                old=['clang','--target='+target,'-Xclang','-triple','-Xclang',target,*flags,'module.ll','runtime.o','-o','program',*libraries]
                self.assertNotEqual(old,expected)
        self.assertEqual({k.arg:ast.literal_eval(k.value) for k in call.keywords},{'timeout':120,'memory':512})
        self.assertIn('if result.returncode!=0 or result.stdout or result.stderr',ast.get_source_segment(source,run))

    def test_darwin_probe_validates_initialized_versioned_target(self):
        for target in ('arm64-apple-macosx11.0.0','aarch64-apple-macosx15.2','arm64-apple-macosx26.0.0'):
            module='target triple = "'+target+'"\n'
            self.assertEqual(gate.darwin_deployment_target(module),target)
        for bad in ('aarch64-apple-darwin','arm64-apple-macosx0.0.0','arm64-apple-macosx',
                    'x86_64-apple-macosx15.0.0','arm64-apple-ios15.0.0','arm64-unknown-macosx15.0.0',
                    'arm64-apple-macosx15.0.0-simulator','arm64-apple-macosx15.0.0 extra',
                    'arm64-apple-macosx15.0.0\n'):
            with self.subTest(target=bad), self.assertRaises(RuntimeError):
                gate.darwin_deployment_target('target triple = "'+bad+'"\n')
        header='target triple = "arm64-apple-macosx15.0.0"\n'
        for bad in ('',header.replace('\n','\r\n'),header+header,header+'  '+header,header+'target\ttriple = "other"\n'):
            with self.assertRaises(RuntimeError): gate.darwin_deployment_target(bad)

    def test_deployment_probe_is_one_bounded_darwin_only_job(self):
        target='aarch64-apple-darwin';selected='arm64-apple-macosx15.0.0'
        module='target triple = "'+selected+'"\n'
        calls=[]
        def run(command,label,**caps):
            calls.append((command,label,caps))
            Path(command[-1]).write_bytes(module.encode('utf-8'))
            return self.result()
        with TemporaryDirectory() as directory:
            work=Path(directory);report={};runner=SimpleNamespace(run=run)
            for ordinary in ('x86_64-unknown-linux-gnu','aarch64-unknown-linux-gnu','x86_64-w64-windows-gnu'):
                self.assertEqual(gate.native_link_target('clang',runner,work,ordinary,report),ordinary)
                self.assertEqual(calls,[]);self.assertEqual(report,{})
            self.assertEqual(gate.native_link_target('clang',runner,work,target,report),selected)
            probe=work/'darwin-deployment-probe.c';llvm=work/'darwin-deployment-probe.ll'
            self.assertEqual(calls,[(['clang','--target='+target,'-S','-emit-llvm','-x','c',str(probe),'-o',str(llvm)],
                                     'scalar Sum Darwin deployment probe',{'timeout':120,'memory':512})])
            self.assertEqual(report['darwin_deployment_probe'],{'source_sha256':gate.sha(probe),
                             'module_sha256':gate.sha(llvm),'target':selected})
            for result in (self.result(code=1),self.result('extra'),self.result(stderr='warning')):
                report={}
                with self.assertRaises(RuntimeError):
                    gate.native_link_target('clang',SimpleNamespace(run=lambda *a,**k:result),work,target,report)
                self.assertEqual(report,{})
            # A stale successful LLVM file cannot substitute for this job's output.
            llvm.write_bytes(module.encode('utf-8'))
            with self.assertRaises(RuntimeError):
                gate.native_link_target('clang',SimpleNamespace(run=lambda *a,**k:self.result()),work,target,{})
            self.assertFalse(llvm.exists())
            def wrong(command,*args,**kwargs):
                Path(command[-1]).write_bytes(b'target triple = "x86_64-apple-macosx15.0.0"\n')
                return self.result()
            with self.assertRaises(RuntimeError):
                gate.native_link_target('clang',SimpleNamespace(run=wrong),work,target,{})

    def test_native_module_changes_only_one_darwin_target_header(self):
        body='target datalayout = "e-m:o-i64:64"\n%pair = type { i1, i64 }\ndefine i64 @main() { ret i64 0 }\n'
        for target in ('x86_64-unknown-linux-gnu','aarch64-unknown-linux-gnu','x86_64-w64-windows-gnu'):
            module='target triple = "'+target+'"\n'+body
            self.assertIs(gate.native_link_module(module,target,target),module)
            with self.assertRaises(RuntimeError): gate.native_link_module(module,target,'wrong')
        header='target triple = "aarch64-apple-darwin"\n'
        module=header+body;selected='arm64-apple-macosx15.0.0'
        linked=gate.native_link_module(module,'aarch64-apple-darwin',selected)
        self.assertEqual(linked,'target triple = "'+selected+'"\n'+body)
        self.assertEqual(linked.split('\n',1)[1].encode(),module.split('\n',1)[1].encode())
        for bad in (body,module+header,module+'  '+header,module.replace('aarch64-apple-darwin',selected)):
            with self.assertRaises(RuntimeError): gate.native_link_module(bad,'aarch64-apple-darwin',selected)
        with self.assertRaises(RuntimeError): gate.native_link_module(module,'aarch64-apple-darwin','aarch64-apple-darwin')

    def test_runtime_audit_and_sanitizer_builds_use_the_native_target(self):
        run=next(node for node in ast.parse(Path(gate.__file__).read_text(encoding='utf-8')).body
                 if isinstance(node,ast.FunctionDef) and node.name=='run_gate')
        loop=next(node for node in ast.walk(run) if isinstance(node,ast.For)
                  and isinstance(node.target,ast.Name) and node.target.id=='opt')
        seed=loop.body[0]
        self.assertIsInstance(seed,ast.Assign)
        self.assertEqual(seed.targets[0].id,'flags')
        append_sanitizers=loop.body[1]
        self.assertIsInstance(append_sanitizers,ast.If)
        calls={}
        for node in ast.walk(run):
            if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or node.func.attr!='run':
                continue
            label=node.args[1]
            if isinstance(label,ast.JoinedStr):
                text=''.join(part.value for part in label.values if isinstance(part,ast.Constant))
                if text.startswith('scalar Sum runtime '): calls['runtime']=node
                if text.startswith('scalar Sum audit link O'): calls['audit']=node
            elif isinstance(label,ast.Constant) and label.value=='scalar Sum sanitizer link':
                calls['sanitizer']=node
        self.assertEqual(set(calls),{'runtime','audit','sanitizer'})
        for call in calls.values():
            self.assertEqual({key.arg:ast.literal_eval(key.value) for key in call.keywords},
                             {'timeout':120,'memory':512})
        def command(expression, values):
            return eval(compile(ast.Expression(expression),gate.__file__,'eval'),{'__builtins__':{}},values)
        for target in ('x86_64-unknown-linux-gnu','aarch64-apple-darwin','x86_64-w64-windows-gnu'):
            for plain in (False,True):
                for opt in gate.OPTS:
                    values={'args':SimpleNamespace(clang='clang',plain=plain),'target':target,'opt':opt,
                            'checks':SimpleNamespace(RUNTIME_ROOT=Path('runtime'),runtime_platform_final_link_args=lambda:['platform-lib']),
                            'AUDIT_FLAGS':gate.AUDIT_FLAGS,'SANITIZER_FLAGS':gate.SANITIZER_FLAGS,
                            'path':Path('runtime/source.c'),'output':Path('runtime.o'),'audit':Path('audit.c'),
                            'probe':Path('sanitizer.c'),'binary':Path('probe'),'objects':{opt:['runtime.o']},'str':str,'list':list}
                    exec(compile(ast.Module([seed,append_sanitizers],type_ignores=[]),gate.__file__,'exec'),
                         {'__builtins__':{}},values)
                    flags=['--target='+target,'-w',f'-O{opt}','-Iruntime',*gate.AUDIT_FLAGS]
                    if not plain: flags+=list(gate.SANITIZER_FLAGS)
                    expected={'runtime':['clang',*flags,'-c',str(values['path']),'-o','runtime.o'],
                              'audit':['clang',*flags,'audit.c','runtime.o','-o','probe','platform-lib'],
                              'sanitizer':['clang','--target='+target,'-O0',*gate.SANITIZER_FLAGS,'sanitizer.c','-o','probe']}
                    for role,call in calls.items():
                        with self.subTest(target=target,plain=plain,opt=opt,role=role):
                            actual=command(call.args[0],values)
                            self.assertEqual(actual,expected[role])
                            self.assertEqual([arg for arg in actual if arg.startswith('--target=')],['--target='+target])
                    # Exact old default-target stages must fail this oracle.
                    old_values={**values,'flags':[flag for flag in values['flags'] if not flag.startswith('--target=')]}
                    for role in ('runtime','audit'):
                        self.assertNotEqual(command(calls[role].args[0],old_values),expected[role])
                    old_sanitizer=copy.deepcopy(calls['sanitizer'].args[0])
                    old_sanitizer.elts=[part for part in old_sanitizer.elts if not (isinstance(part,ast.BinOp)
                                        and isinstance(part.left,ast.Constant) and part.left.value=='--target=')]
                    self.assertNotEqual(command(old_sanitizer,values),expected['sanitizer'])

    def test_runtime_build_commands_preserve_windows_and_posix_paths(self):
        source_path = Path(gate.__file__)
        for flavor, expected in ((PurePosixPath, 'runtime/source.c'),
                                 (PureWindowsPath, 'runtime\\source.c')):
            runtime_source = flavor('runtime') / 'source.c'
            self.assertEqual(str(runtime_source), expected)
            self.assertEqual(runtime_source, flavor('runtime/source.c'))
            def modeled_path(*parts):
                if parts == (gate.__file__,):
                    return source_path
                return flavor(*parts)
            with self.subTest(flavor=flavor.__name__), patch(__name__+'.Path', modeled_path):
                self.test_runtime_audit_and_sanitizer_builds_use_the_native_target()

    def test_windows_locale_and_newlines_preserve_target_controls(self):
        original_read = Path.read_text
        def windows_read(path, encoding=None, errors=None):
            if path == Path(gate.__file__):
                raw = path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
                with io.TextIOWrapper(io.BytesIO(raw), encoding=encoding or 'cp1252', errors=errors) as stream:
                    return stream.read()
            return original_read(path, encoding=encoding or 'cp1252', errors=errors)
        def windows_write(path, data, encoding=None, errors=None, newline=None):
            with io.StringIO(newline='\r\n' if newline is None else newline) as stream:
                count = stream.write(data)
                path.write_bytes(stream.getvalue().encode(encoding or 'cp1252', errors or 'strict'))
                return count
        with patch.object(Path, 'read_text', windows_read), patch.object(Path, 'write_text', windows_write):
            self.test_deployment_probe_is_one_bounded_darwin_only_job()
            self.test_native_link_matches_emitted_target_and_strict_caps()
            self.test_runtime_audit_and_sanitizer_builds_use_the_native_target()
        with self.assertRaises(RuntimeError):
            gate.darwin_deployment_target('target triple = "arm64-apple-macosx15.0.0"\r\n')

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
        module_error=task(llvm,'v4_codegen_llvm_native_module_error')
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
            if declared != make_target.return_type.name or declared != module_text.params[1].type_ann.name or candidate.params[2].type_ann.name != module_error.return_type.name:
                raise RuntimeError('operator target forwarding disagrees with real target/module interfaces')
        consistent(helper)
        forwarding=[node for node in walk(helper.body) if type(node).__name__=='Call' and type(node.func).__name__=='Ident' and node.func.name=='v4_codegen_llvm_module_text']
        self.assertEqual(len(forwarding),1)
        self.assertEqual(forwarding[0].args[1].name,helper.params[1].name)
        binding=next(node for node in walk(caller.body) if type(node).__name__=='PilotDecl' and node.name=='target')
        self.assertEqual(binding.value.func.name,'v4_target_spec_new')
        calls=[node for node in walk(caller.body) if type(node).__name__=='Call' and type(node.func).__name__=='Ident' and node.func.name==helper.name]
        self.assertTrue(calls)
        self.assertTrue(all(node.args[1].name=='target' and node.args[2].name=='expected' for node in calls))
        error_binding=next(node for node in walk(caller.body) if type(node).__name__=='PilotDecl' and node.name=='expected')
        self.assertEqual(type(error_binding.value).__name__,'StrLit')
        old=copy.deepcopy(helper);old.params[1].type_ann.name='int'
        with self.assertRaises(RuntimeError): consistent(old)
        wrong_error=copy.deepcopy(helper);wrong_error.params[2].type_ann.name='int'
        with self.assertRaises(RuntimeError): consistent(wrong_error)

    def test_runtime_type_declarations_are_bootstrap_typechecked(self):
        from freakc.parser import Parser
        from freakc.type_checker import TypeChecker
        root = Path(gate.__file__).resolve().parents[1]
        programs=[Parser.from_source(path.read_text()) for path in sorted((root/'src/compiler/v4/crates').glob('*/src/lib.fk'))]
        target_name='v4_codegen_llvm_scalar_sum_runtime_lines'
        target=next(node for program in programs for node in program.statements if type(node).__name__=='TaskDecl' and node.name==target_name)
        combined=copy.deepcopy(programs[0]);combined.statements=[]
        for program in programs:
            for node in program.statements:
                copied=copy.copy(node)
                if type(copied).__name__=='TaskDecl' and copied.name!=target_name:
                    copied.body=[]
                combined.statements.append(copied)
        errors=lambda program:[diag for diag in TypeChecker().check(program) if diag.level=='error']
        self.assertEqual(errors(combined),[])
        def walk(node):
            yield node
            if isinstance(node,(list,tuple)):
                for child in node: yield from walk(child)
            elif hasattr(node,'__dict__'):
                for child in vars(node).values(): yield from walk(child)
        strings=[node for node in walk(target.body) if type(node).__name__=='StrLit']
        self.assertTrue(strings)
        self.assertTrue(all(all(expression is None for _,expression in (node.parts or [])) for node in strings))
        old=copy.deepcopy(combined)
        old_task=next(node for node in old.statements if type(node).__name__=='TaskDecl' and node.name==target_name)
        # Restore the exact old braced literals in the two output assignments.
        replaced=0
        declarations=[]
        for node in walk(old_task.body):
            if type(node).__name__=='Assign' and type(node.value).__name__=='BinOp':
                text_nodes=[child for child in walk(node.value) if type(child).__name__=='StrLit']
                text=''.join(child.value for child in text_nodes)
                if text.startswith('%freak_') and ' = type {' in text:
                    declarations.append(text)
                    node.value=Parser.from_source('pilot output = out + "'+text.replace('\n','\\n')+'"').statements[0].value
                    replaced+=1
        self.assertEqual(replaced,2)
        self.assertEqual(declarations,['%freak_maybe_int = type { i1, i64 }\n','%freak_result_word_word = type { i1, i64 }\n'])
        old_errors=errors(old)
        self.assertEqual(len(old_errors),2)
        self.assertTrue(all(' i1, i64 ' in diag.message for diag in old_errors))


if __name__=='__main__': unittest.main()
