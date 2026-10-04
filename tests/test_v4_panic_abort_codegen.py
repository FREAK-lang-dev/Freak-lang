"""Pure adversarial controls for authored panic compiler/native oracles."""
import importlib.util
from pathlib import Path
import signal
from types import SimpleNamespace
import unittest
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
        for bad in (text+'extra\n',text.replace('v8-restore=true','v8-restore=false'),text.replace('old-seal=true','old-seal=false'),text.replace('fresh-module=true','fresh-module=false'),text.replace('\n','\r\n'),text.replace('define void @x() { unreachable }','')):
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
if __name__=='__main__':unittest.main()
