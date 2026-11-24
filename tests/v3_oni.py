#!/usr/bin/env python3
"""Prove the oni std hook (green tasks for the hyakki runtime) on both backends.

Each program drives oni::* from a tiny parade loop written in FREAK, the way
the hyakki Hangar package does, and prints lines the test compares exactly.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


PARADE = r'''
task parade() -> void {
    repeat until oni::live() == 0 {
        pilot h = oni::next_ready()
        if h != 0 {
            oni::resume(h)
        } else if oni::waiting() > 0 {
            oni::poll(0 - 1)
        } else {
            say "stalled"
            break
        }
    }
}
'''

SCHEDULER = PARADE + r'''
pilot log = ""

task sleeper(ms: int) -> void {
    time::sleep(ms)
    log = log + "s" + word_from_int(ms) + " "
}

task square(x: int) -> int {
    time::sleep(0)
    give back x * x
}

task bower(id: int) -> void {
    pilot i = 0
    repeat 3 times {
        log = log + word_from_int(id) + word_from_int(i) + " "
        time::sleep(0)
        i += 1
    }
}

task depth(n: int) -> int {
    if n == 0 { give back 0 }
    give back 1 + depth(n - 1)
}

task deep(n: int) -> int {
    give back depth(n)
}

task whoami(x: int) -> int {
    pilot me = oni::current()
    if me != 0 { give back x }
    give back 0 - 1
}

pilot counted = 0
task tally(x: int) -> void {
    counted += x
}

task main() -> void {
    oni::summon("sleeper", 30)
    oni::summon("sleeper", 10)
    oni::summon("sleeper", 20)
    parade()
    say log
    log = ""
    oni::summon("bower", 1)
    oni::summon("bower", 2)
    parade()
    say log
    pilot s = oni::summon("square", 12)
    say oni::state(s)
    parade()
    say oni::returned(s)
    say oni::state(s)
    oni::release(s)
    say oni::state(s)
    oni::stack_kib(2048)
    pilot d = oni::summon("deep", 3000)
    parade()
    say oni::returned(d)
    pilot w = oni::summon("whoami", 7)
    parade()
    say oni::returned(w)
    say oni::current()
    oni::stack_kib(64)
    pilot i = 0
    repeat 2000 times {
        pilot h = oni::summon("tally", 1)
        oni::resume(h)
        oni::release(h)
        i += 1
    }
    say counted
    say oni::live()
}
'''

SCHEDULER_EXPECTED = """s10 s20 s30\x20
10 20 11 21 12 22\x20
1
144
4
0
3000
7
0
2000
0
"""

WAITS = PARADE + r'''
pilot sleeper_handle = 0
pilot waiter_handle = 0
pilot log = ""

task waiter(x: int) -> void {
    oni::suspend()
    log = log + "woken "
}

task waker(x: int) -> void {
    time::sleep(5)
    oni::wake(waiter_handle)
}

task patient(ms: int) -> void {
    pilot woke = oni::suspend_for(ms)
    if woke { log = log + "ok " } else { log = log + "late " }
    if oni::timed_out() { log = log + "timed_out " }
}

task long_sleeper(x: int) -> void {
    pilot started = time::monotonic_ns()
    time::sleep(5000)
    pilot ms = (time::monotonic_ns() - started) / 1000000
    if oni::cancelled() { log = log + "cancelled " }
    if ms < 1000 { log = log + "early " }
}

task canceller(x: int) -> void {
    time::sleep(5)
    oni::cancel(sleeper_handle)
}

task curfewed(x: int) -> void {
    oni::curfew(10)
    pilot started = time::monotonic_ns()
    time::sleep(5000)
    pilot ms = (time::monotonic_ns() - started) / 1000000
    if oni::timed_out() and ms < 1000 { log = log + "curfew " }
    oni::curfew(0)
    time::sleep(1)
    if not oni::timed_out() { log = log + "lifted " }
}

task main() -> void {
    waiter_handle = oni::summon("waiter", 0)
    oni::summon("waker", 0)
    parade()
    oni::summon("patient", 10)
    parade()
    sleeper_handle = oni::summon("long_sleeper", 0)
    oni::summon("canceller", 0)
    parade()
    oni::summon("curfewed", 0)
    parade()
    pilot lost = oni::summon("waiter", 0)
    parade()
    say log
    say oni::live()
    say oni::waiting()
    say oni::state(lost)
    say oni::poll(0)
}
'''

WAITS_EXPECTED = """stalled
woken late timed_out cancelled early curfew lifted\x20
1
0
3
0
"""

SOCKETS = PARADE + r'''
pilot port = 0
pilot clients = 200
pilot replies = 0
pilot ticks = 0
pilot big_ok = 0
pilot timed_out_ok = 0
pilot closed_ok = 0
pilot victim = 0

task handler(conn: int) -> void {
    pilot buf = ByteBuffer::new()
    repeat until false {
        pilot n = tcp::socket_receive(conn, buf, 65536)
        if n == 0 { break }
        tcp::socket_send_all(conn, buf, 0, n)
        buf.clear()
    }
    buf.release()
    tcp::socket_close(conn)
}

task gate(listener: int) -> void {
    pilot accepted = 0
    repeat until accepted >= clients + 1 {
        pilot conn = tcp::socket_accept(listener)
        oni::summon("handler", conn)
        accepted += 1
    }
    tcp::socket_close(listener)
}

task client(i: int) -> void {
    pilot sock = tcp::socket_connect("127.0.0.1", port)
    pilot out = ByteBuffer::new()
    out.write_word("ping-" + word_from_int(i))
    time::sleep(i % 7)
    tcp::socket_send_all(sock, out, 0, out.length())
    pilot inbox = ByteBuffer::new()
    pilot n = tcp::socket_receive(sock, inbox, 4096)
    if n == out.length() { replies += 1 }
    out.release()
    inbox.release()
    tcp::socket_close(sock)
}

-- 4 MiB through one echo connection while the ticker keeps running.
task big(x: int) -> void {
    pilot sock = tcp::socket_connect("127.0.0.1", port)
    pilot out = ByteBuffer::with_capacity(4194304)
    pilot i = 0
    repeat 65536 times {
        out.write_word("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
        i += 1
    }
    pilot sent = tcp::socket_send_all(sock, out, 0, out.length())
    pilot inbox = ByteBuffer::new()
    repeat until inbox.length() >= sent {
        pilot n = tcp::socket_receive(sock, inbox, 65536)
        if n == 0 { break }
    }
    if sent == 4194304 and inbox.length() == sent { big_ok = 1 }
    out.release()
    inbox.release()
    tcp::socket_close(sock)
}

task ticker(x: int) -> void {
    repeat until big_ok == 1 or ticks > 100000 {
        ticks += 1
        time::sleep(0)
    }
}

task silent_server(x: int) -> void {
    pilot listener = tcp::socket_listen("127.0.0.1", 0, 4)
    pilot quiet_port = tcp::socket_local_port(listener)
    victim = tcp::socket_connect("127.0.0.1", quiet_port)
    pilot peer = tcp::socket_accept(listener)
    tcp::socket_set_timeout(victim, 30, 30)
    pilot inbox = ByteBuffer::new()
    pilot n = tcp::socket_receive(victim, inbox, 16)
    if n == 0 and tcp::socket_status(victim) == 10 { timed_out_ok = 1 }
    inbox.release()
    tcp::socket_close(victim)
    tcp::socket_close(peer)
    tcp::socket_close(listener)
}

pilot doomed = 0
task doomed_reader(x: int) -> void {
    pilot inbox = ByteBuffer::new()
    pilot n = tcp::socket_receive(doomed, inbox, 16)
    if n == 0 { closed_ok = 1 }
    inbox.release()
}

task closer(x: int) -> void {
    time::sleep(5)
    tcp::socket_close(doomed)
}

-- A reader whose data is always there must still let others run.
pilot hog_sock = 0
pilot hog_done = 0
pilot witnessed = 0
task hog(x: int) -> void {
    pilot inbox = ByteBuffer::new()
    repeat until false {
        pilot n = tcp::socket_receive(hog_sock, inbox, 16)
        if n == 0 { break }
        inbox.clear()
    }
    inbox.release()
    hog_done = 1
}

task witness(x: int) -> void {
    repeat until hog_done == 1 {
        witnessed += 1
        time::sleep(0)
    }
}

task main() -> void {
    pilot listener = tcp::socket_listen("127.0.0.1", 0, 256)
    port = tcp::socket_local_port(listener)
    oni::summon("gate", listener)
    pilot i = 0
    repeat clients times {
        oni::summon("client", i)
        i += 1
    }
    oni::summon("big", 0)
    oni::summon("ticker", 0)
    oni::summon("silent_server", 0)
    parade()
    say replies
    say big_ok
    if ticks > 10 { say "ticked" } else { say "starved" }
    say timed_out_ok

    pilot l2 = tcp::socket_listen("127.0.0.1", 0, 4)
    doomed = tcp::socket_connect("127.0.0.1", tcp::socket_local_port(l2))
    pilot peer = tcp::socket_accept(l2)
    oni::summon("doomed_reader", 0)
    oni::summon("closer", 0)
    parade()
    say closed_ok
    tcp::socket_close(peer)
    tcp::socket_close(l2)

    pilot l3 = tcp::socket_listen("127.0.0.1", 0, 4)
    pilot writer = tcp::socket_connect("127.0.0.1", tcp::socket_local_port(l3))
    hog_sock = tcp::socket_accept(l3)
    pilot blob = ByteBuffer::new()
    repeat 1024 times { blob.write_word("0123456789abcdef0123456789abcdef") }
    tcp::socket_send_all(writer, blob, 0, blob.length())
    tcp::socket_close(writer)
    blob.release()
    oni::summon("hog", 0)
    oni::summon("witness", 0)
    parade()
    if witnessed >= 8 { say "shared" } else { say "hogged" }
    tcp::socket_close(hog_sock)
    tcp::socket_close(l3)
}
'''

SOCKETS_EXPECTED = """200
1
ticked
1
1
shared
"""

DIAGNOSTICS = [
    ("not_literal", 'task w(x: int) -> void { }\ntask main() -> void {\n    pilot name = "w"\n    oni::summon(name, 0)\n}\n',
     "needs the task name as a plain string literal"),
    ("unknown", 'task main() -> void {\n    oni::summon("nobody", 0)\n}\n',
     "there is no task named 'nobody'"),
    ("signature", 'task w(x: word) -> void { }\ntask main() -> void {\n    oni::summon("w", 0)\n}\n',
     "must take exactly one int and give back void or int"),
    ("returns", 'task w(x: int) -> word { give back "" }\ntask main() -> void {\n    oni::summon("w", 0)\n}\n',
     "must take exactly one int and give back void or int"),
    ("arg_type", 'task w(x: int) -> void { }\ntask main() -> void {\n    oni::summon("w", "zero")\n}\n',
     "oni::summon argument 2 expects int"),
    ("arity", 'task w(x: int) -> void { }\ntask main() -> void {\n    oni::summon("w")\n}\n',
     "oni::summon expects 2 argument(s)"),
    ("unresolved_arg", 'task w(x: int) -> void { }\ntask main() -> void {\n    oni::summon("w", List::new())\n}\n',
     "oni::summon argument 2 has an unresolved type"),
    ("global_order", 'task w(x: int) -> int { give back later }\npilot h = oni::summon("w", 0)\npilot r = oni::resume(h)\npilot later = 42\ntask main() -> void {\n    say r\n}\n',
     "depends on global 'later' before it is initialized"),
]

RUNTIME_FAILURE = PARADE + r'''
task nested(x: int) -> void {
    oni::resume(x)
}
task main() -> void {
    pilot h = oni::summon("nested", 0)
    oni::resume(h)
}
'''

REVIEW = PARADE + r'''
-- Regressions from review: each prints one line.

-- an int task whose children grow the oni table still stores its result
task leaf(x: int) -> void {
    time::sleep(0)
}
task grower(x: int) -> int {
    pilot i = 0
    repeat 2000 times {
        oni::summon("leaf", i)
        i += 1
    }
    time::sleep(0)
    give back 12345
}

-- a stale deadline from a released oni never wakes the next tenant
task early(x: int) -> void {
    oni::suspend_for(50)
}
task patient(x: int) -> void {
    oni::suspend_for(5000)
}
task blank(x: int) -> void {
    time::sleep(0)
}
task noop(x: int) -> void {
    pilot y = x
}
task huge(x: int) -> void {
    if oni::suspend_for(9223372036854775807) { say "huge wait woken" } else { say "huge wait expired" }
}
pilot bad_send_status = 0
task bad_sender(x: int) -> void {
    pilot blob = ByteBuffer::new()
    blob.write_word("abc")
    pilot n = tcp::socket_send(x, blob, 0, 0 - 1)
    bad_send_status = tcp::socket_status(x)
    blob.release()
}

pilot gate_port = 0
pilot gate_listener = 0
pilot accepted = 0
task acceptor(x: int) -> void {
    pilot c = tcp::socket_accept(gate_listener)
    if tcp::socket_status(c) == 0 { accepted += 1 }
    tcp::socket_close(c)
}

pilot feed = 0
pilot fed = ""
task reader(x: int) -> void {
    pilot inbox = ByteBuffer::new()
    pilot n = tcp::socket_receive(feed, inbox, 16)
    if n > 0 { fed = "read " + word_from_int(n) } else { fed = "empty" }
    inbox.release()
}

pilot slow_status = 0
pilot slow_sock = 0
task slow_reader(x: int) -> void {
    pilot inbox = ByteBuffer::new()
    pilot n = tcp::socket_receive(slow_sock, inbox, 16)
    slow_status = tcp::socket_status(slow_sock)
    inbox.release()
}

pilot stuck = 0
pilot stuck_sent = 0
task stuffer(x: int) -> void {
    pilot blob = ByteBuffer::new()
    repeat 262144 times { blob.write_word("0123456789abcdef0123456789abcdef") }
    stuck_sent = tcp::socket_send_all(stuck, blob, 0, blob.length())
    blob.release()
}

task main() -> void {
    pilot g = oni::summon("grower", 0)
    parade()
    say oni::returned(g)

    pilot a = oni::summon("early", 0)
    oni::resume(oni::next_ready())
    oni::wake(a)
    oni::resume(oni::next_ready())
    oni::release(a)
    pilot b = oni::summon("patient", 0)
    oni::resume(oni::next_ready())
    pilot t0 = time::now_ms()
    oni::poll(150)
    if oni::state(b) == 3 { say "stale timer ignored" } else { say "woken by a stale timer" }
    oni::cancel(b)
    parade()
    oni::release(b)

    pilot first = oni::summon("blank", 0)
    parade()
    oni::release(first)
    pilot aliased = 0
    repeat 70000 times {
        pilot h = oni::summon("blank", 0)
        if h == first { aliased += 1 }
        parade()
        oni::release(h)
    }
    say aliased

    pilot s = oni::summon("patient", 0)
    oni::resume(s)
    oni::wake(s)
    oni::resume(s)
    pilot sl = oni::summon("noop", 0)
    oni::resume(sl)
    oni::release(sl)
    pilot q = oni::summon("early", 0)
    oni::resume(q)
    pilot t1 = time::now_ms()
    oni::poll(0 - 1)
    if time::now_ms() - t1 >= 30 { say "poll waited" } else { say "poll spun" }
    parade()

    gate_listener = tcp::socket_listen("127.0.0.1", 0, 8)
    gate_port = tcp::socket_local_port(gate_listener)
    oni::summon("acceptor", 0)
    oni::summon("acceptor", 0)
    oni::resume(oni::next_ready())
    oni::resume(oni::next_ready())
    pilot c1 = tcp::socket_connect("127.0.0.1", gate_port)
    pilot c2 = tcp::socket_connect("127.0.0.1", gate_port)
    parade()
    say accepted
    tcp::socket_close(c1)
    tcp::socket_close(c2)

    pilot writer = tcp::socket_connect("127.0.0.1", gate_port)
    feed = tcp::socket_accept(gate_listener)
    pilot r = oni::summon("reader", 0)
    oni::resume(oni::next_ready())
    oni::wake(r)
    pilot t2 = time::now_ms()
    oni::resume(oni::next_ready())
    if time::now_ms() - t2 < 50 and oni::state(r) == 3 { say "woken reader parked again" } else { say "woken reader blocked" }
    pilot out = ByteBuffer::new()
    out.write_word("hey")
    tcp::socket_send_all(writer, out, 0, out.length())
    parade()
    say fed
    out.release()
    tcp::socket_close(writer)
    tcp::socket_close(feed)

    tcp::socket_set_timeout(gate_listener, 40, 40)
    pilot w2 = tcp::socket_connect("127.0.0.1", gate_port)
    slow_sock = tcp::socket_accept(gate_listener)
    oni::summon("slow_reader", 0)
    pilot t3 = time::now_ms()
    parade()
    if slow_status == 10 and time::now_ms() - t3 < 2000 { say "inherited timeout" } else { say "no inherited timeout" }
    tcp::socket_close(slow_sock)

    stuck = tcp::socket_connect("127.0.0.1", gate_port)
    pilot sink = tcp::socket_accept(gate_listener)
    tcp::socket_set_timeout(stuck, 40, 40)
    pilot st = oni::summon("stuffer", 0)
    pilot t4 = time::now_ms()
    oni::resume(oni::next_ready())
    repeat 8 times {
        oni::poll(10)
        oni::wake(st)
        if oni::state(st) != 4 { oni::resume(oni::next_ready()) }
    }
    parade()
    if time::now_ms() - t4 < 120 and stuck_sent < 8388608 { say "send deadline kept" } else { say "send deadline stretched" }
    tcp::socket_close(stuck)
    tcp::socket_close(sink)
    tcp::socket_close(w2)

    pilot bs = tcp::socket_connect("127.0.0.1", gate_port)
    pilot bs_peer = tcp::socket_accept(gate_listener)
    oni::summon("bad_sender", bs)
    parade()
    say bad_send_status
    tcp::socket_close(bs)
    tcp::socket_close(bs_peer)
    tcp::socket_close(gate_listener)

    pilot ra = oni::summon("blank", 0)
    pilot rb = oni::summon("blank", 0)
    oni::resume(ra)
    say oni::ready_count()
    if oni::next_ready() == rb { say "fifo kept after direct resume" } else { say "direct resume jumped the queue" }
    oni::resume(rb)
    parade()
    oni::release(ra)
    oni::release(rb)

    pilot waiting_one = oni::summon("blank", 0)
    repeat 100000 times {
        pilot d = oni::summon("noop", 0)
        oni::resume(d)
        oni::release(d)
    }
    if oni::ready_count() == 1 and oni::next_ready() == waiting_one { say "ring kept order through sweeps" } else { say "ring lost its order" }
    oni::resume(waiting_one)
    parade()
    oni::release(waiting_one)

    pilot keeper = oni::summon("early", 0)
    oni::resume(oni::next_ready())
    repeat 300 times {
        pilot w = oni::summon("patient", 0)
        oni::resume(w)
        oni::wake(w)
        oni::resume(w)
        oni::release(w)
    }
    pilot t5 = time::now_ms()
    parade()
    if oni::state(keeper) == 4 and time::now_ms() - t5 < 1000 { say "timers kept after sweep" } else { say "timers lost in sweep" }
    oni::release(keeper)

    pilot hg = oni::summon("huge", 0)
    oni::resume(oni::next_ready())
    oni::poll(10)
    oni::wake(hg)
    parade()
    oni::release(hg)
}
'''

REVIEW_EXPECTED = """12345
stale timer ignored
0
poll waited
2
woken reader parked again
read 3
inherited timeout
send deadline kept
1
2
fifo kept after direct resume
ring kept order through sweeps
timers kept after sweep
huge wait woken
"""


def plain(text: str) -> str:
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def build(freak: Path, source: Path, output: Path, flags: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(freak), "build", str(source), "-o", str(output), *flags],
        capture_output=True, text=True, timeout=600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freak", type=Path)
    parser.add_argument("--quick", action="store_true", help="LLVM O2 and C O2 only")
    args = parser.parse_args()
    freak = args.freak.resolve()
    exe = ".exe" if os.name == "nt" else ""
    profiles = [["--llvm"], ["--c"]] if args.quick else [
        ["--llvm"], ["--c"], ["--llvm", "--opt=0"], ["--c", "--opt=0"],
        ["--llvm", "--opt=3"], ["--c", "--strict-borrow"], ["--llvm", "--strict-borrow"]]
    failures = 0
    with tempfile.TemporaryDirectory(prefix="freak-oni-") as temp:
        root = Path(temp)
        for name, program, expected in (
                ("scheduler", SCHEDULER, SCHEDULER_EXPECTED),
                ("waits", WAITS, WAITS_EXPECTED),
                ("sockets", SOCKETS, SOCKETS_EXPECTED),
                ("review", REVIEW, REVIEW_EXPECTED)):
            source = root / f"{name}.fk"
            source.write_text(program, encoding="utf-8")
            for flags in profiles:
                label = f"{name} {' '.join(flags)}"
                binary = root / f"{name}{exe}"
                built = build(freak, source, binary, flags)
                if built.returncode != 0:
                    print(f"FAIL {label}: build failed\n{plain(built.stdout)}{plain(built.stderr)}")
                    failures += 1
                    continue
                ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
                got = ran.stdout.replace("\r\n", "\n")
                if ran.returncode != 0 or got != expected:
                    print(f"FAIL {label}: exit {ran.returncode}\n--- expected\n{expected}--- got\n{got}{ran.stderr}")
                    failures += 1
                else:
                    print(f"ok   {label}")
        for name, program, needle in DIAGNOSTICS:
            source = root / f"diag_{name}.fk"
            source.write_text(program, encoding="utf-8")
            checked = subprocess.run([str(freak), "check", str(source)],
                                     capture_output=True, text=True, timeout=120)
            text = plain(checked.stdout + checked.stderr)
            if checked.returncode == 0 or needle not in text:
                print(f"FAIL diagnostic {name}: exit {checked.returncode}, wanted {needle!r}\n{text}")
                failures += 1
            else:
                print(f"ok   diagnostic {name}")
        source = root / "nested.fk"
        source.write_text(RUNTIME_FAILURE, encoding="utf-8")
        for flags in (["--llvm"], ["--c"]):
            binary = root / f"nested{exe}"
            built = build(freak, source, binary, flags)
            ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=60) \
                if built.returncode == 0 else None
            if ran is None or ran.returncode != 1 or "resume is only allowed from the main stack" not in ran.stderr:
                print(f"FAIL nested resume {' '.join(flags)}: {ran and ran.returncode} {ran and ran.stderr}")
                failures += 1
            else:
                print(f"ok   nested resume {' '.join(flags)}")
    if failures:
        print(f"{failures} oni check(s) failed")
        return 1
    print("oni std hook: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
