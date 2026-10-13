"""Deadline-client controls using scripted I/O; no server or native tool runs."""
import errno
import unittest
from unittest.mock import patch

from v3_v35_http import absolute_deadline_probe


def timeout_wire(*, head=False, status=408, payload=None, length=None):
    body=b'' if head else b'Request Timeout\n'
    if payload is not None:body=payload
    if length is None:length=len(b'Request Timeout\n')
    return (f'HTTP/1.1 {status} Request Timeout\r\nConnection: close\r\n'
            f'Content-Length: {length}\r\n\r\n'.encode()+body)


class ScriptedSocket:
    """Script response arrival, closure, and a provider abort on later writes."""

    def __init__(self, frames, *, send_error=None, abort_on_late_send=False):
        self.frames=list(frames)
        self.send_error=send_error
        self.abort_on_late_send=abort_on_late_send
        self.now=0.0
        self.sent=[]
        self.received=[]
        self.waits=[]

    def sendall(self, data):
        self.sent.append((self.now,data))
        if self.send_error is not None and len(self.sent)==self.send_error[0]:
            raise self.send_error[1]
        if self.abort_on_late_send and self.frames and self.frames[0][0]<=self.now:
            # A post-close send can invalidate a reply which was not read yet.
            cause=ConnectionAbortedError(10053,'scripted local abort')
            self.frames=[(self.now,cause)]
            raise cause

    def recv(self, size):
        self.received.append(size)
        if not self.frames:return b''
        at,value=self.frames.pop(0)
        self.now=max(self.now,at)
        if isinstance(value,BaseException):raise value
        return value

    def select(self, reads, writes, errors, timeout):
        if reads!=[self] or writes or errors:
            raise AssertionError('unexpected I/O wait')
        self.waits.append(timeout)
        end=self.now+timeout
        if self.frames and self.frames[0][0]<=end:
            self.now=max(self.now,self.frames[0][0])
            return [self],[],[]
        self.now=end
        return [],[],[]


class AbsoluteDeadlineProbeTests(unittest.TestCase):
    def probe(self, client, *, head=False):
        with patch('v3_v35_http.time.monotonic',side_effect=lambda:client.now), \
                patch('v3_v35_http.select.select',side_effect=client.select):
            return absolute_deadline_probe(client,head=head)

    def test_reply_arrival_stops_writes_before_provider_can_discard_it(self):
        wire=timeout_wire()
        client=ScriptedSocket([(.22,wire[:17]),(.23,wire[17:]),(.24,b'')],
                              abort_on_late_send=True)
        self.probe(client)
        self.assertEqual([round(at,2) for at,_ in client.sent],[0,.05,.1,.15,.2])
        self.assertEqual([data for _,data in client.sent],[b'a']*5)
        self.assertEqual(client.waits,[.05]*5)
        self.assertEqual(client.frames,[])

    def test_body_reply_preserves_original_progress_cadence(self):
        client=ScriptedSocket([(.26,timeout_wire()),(.27,b'')])
        self.probe(client)
        self.assertEqual([round(at,2) for at,_ in client.sent],[0,.05,.1,.15,.2,.25])
        self.assertEqual(client.waits,[.05]*6)

    def test_all_ten_progress_writes_remain_when_no_reply_is_readable(self):
        client=ScriptedSocket([(.7,timeout_wire()),(.71,b'')])
        self.probe(client)
        self.assertEqual(len(client.sent),10)
        self.assertEqual([data for _,data in client.sent],[b'a']*10)
        self.assertEqual(client.waits,[.05]*10)

    def test_known_send_closures_still_require_and_accept_actual_reply(self):
        for kind,code in ((BrokenPipeError,errno.EPIPE),
                          (ConnectionResetError,errno.ECONNRESET),
                          (ConnectionAbortedError,10053)):
            for head in (False,True):
                with self.subTest(kind=kind.__name__,head=head):
                    cause=kind(code,'scripted send closure')
                    client=ScriptedSocket([(.06,timeout_wire(head=head)),(.07,b'')],
                                          send_error=(2,cause))
                    self.probe(client,head=head)
                    self.assertEqual(len(client.sent),2)
                    self.assertEqual(client.frames,[])

    def test_known_receive_closures_preserve_fragmented_complete_reply(self):
        for kind,code in ((ConnectionResetError,errno.ECONNRESET),
                          (ConnectionAbortedError,10053)):
            for head in (False,True):
                with self.subTest(kind=kind.__name__,head=head):
                    wire=timeout_wire(head=head)
                    client=ScriptedSocket([(.22,wire[:17]),(.23,wire[17:]),
                                          (.24,kind(code,'scripted receive closure'))])
                    self.probe(client,head=head)
                    self.assertEqual(len(client.sent),5)
                    self.assertEqual(client.frames,[])

    def test_closure_without_reply_cannot_pass(self):
        for kind in (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):
            with self.subTest(kind=kind.__name__):
                client=ScriptedSocket([(0,b'')],send_error=(1,kind('send closed')))
                with self.assertRaises(AssertionError):self.probe(client)
        for kind in (ConnectionResetError,ConnectionAbortedError):
            with self.subTest(kind=kind.__name__,operation='recv'):
                client=ScriptedSocket([(.22,kind('receive closed'))])
                with self.assertRaises(AssertionError):self.probe(client)

    def test_wrong_status_body_length_or_truncated_reply_cannot_pass(self):
        controls=[b'',b'HTTP/1.1 408 Request Timeout\r\n',
                  timeout_wire(status=400),timeout_wire(payload=b''),
                  timeout_wire(payload=b'wrong timeout\n'),timeout_wire(length=15)]
        for wire in controls:
            with self.subTest(wire=wire):
                client=ScriptedSocket([(.22,wire),(.23,ConnectionAbortedError('closed'))])
                with self.assertRaises(AssertionError):self.probe(client)

    def test_head_body_or_wrong_advertised_length_cannot_pass(self):
        for wire in (timeout_wire(),timeout_wire(head=True,length=0)):
            with self.subTest(wire=wire):
                client=ScriptedSocket([(.22,wire),(.23,ConnectionAbortedError('closed'))])
                with self.assertRaises(AssertionError):self.probe(client,head=True)

    def test_original_elapsed_limit_is_strict_even_after_known_closure(self):
        for at in (.8,.81):
            for head in (False,True):
                with self.subTest(at=at,head=head):
                    client=ScriptedSocket([(.22,timeout_wire(head=head)),
                                          (at,ConnectionAbortedError('closed'))])
                    with self.assertRaises(AssertionError):self.probe(client,head=head)

    def test_unknown_send_error_propagates_without_forgiving_wire(self):
        cause=OSError(errno.EACCES,'unrelated send failure')
        client=ScriptedSocket([(.22,timeout_wire()),(.23,b'')],send_error=(1,cause))
        with self.assertRaises(OSError) as caught:self.probe(client)
        self.assertIs(caught.exception,cause)
        self.assertEqual(client.received,[])

    def test_receive_timeout_or_other_error_propagates_after_valid_bytes(self):
        for cause in (TimeoutError('receive deadline'),
                      OSError(errno.EIO,'unrelated receive failure'),
                      BrokenPipeError(errno.EPIPE,'unexpected receive error')):
            with self.subTest(kind=type(cause).__name__):
                client=ScriptedSocket([(.22,timeout_wire()),(.23,cause)])
                with self.assertRaises(type(cause)) as caught:self.probe(client)
                self.assertIs(caught.exception,cause)

    def test_unknown_readiness_error_propagates(self):
        cause=OSError(errno.EBADF,'invalid readiness descriptor')
        client=ScriptedSocket([(.22,timeout_wire()),(.23,b'')])
        with patch('v3_v35_http.time.monotonic',side_effect=lambda:client.now), \
                patch('v3_v35_http.select.select',side_effect=cause):
            with self.assertRaises(OSError) as caught:absolute_deadline_probe(client)
        self.assertIs(caught.exception,cause)
        self.assertEqual(client.received,[])


if __name__=='__main__':unittest.main()
