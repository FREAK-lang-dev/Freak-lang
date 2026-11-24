# oni: green tasks (the std hook behind hyakki)

An **oni** is a FREAK task that runs on its own small stack. Many oni share
one OS thread. When an oni waits on a socket or a timer it *parks*, and
another one runs. This is the Go / Loom model (stackful green threads), not
Rust-style futures: your code stays ordinary straight-line FREAK, with no
`async` and no `await`.

`std` ships only the hook: making stacks, switching between them, and
waiting on sockets and deadlines. The scheduler loop, joins, channels,
select and semaphores live in the **hyakki** Hangar package. Most programs
should `use hyakki` rather than drive `oni::*` by hand.

Available from the first release after 0.15.2, on the V3.5 compiler, LLVM and C backends.

## The smallest parade

```fk
task greet(n: int) -> void {
    time::sleep(10 * n)          -- parks this oni, not the thread
    say "oni {n} woke up"
}

task parade() -> void {
    repeat until oni::live() == 0 {
        pilot h = oni::next_ready()
        if h != 0 {
            oni::resume(h)
        } else if oni::waiting() > 0 {
            oni::poll(0 - 1)         -- sleep until a socket or deadline fires
        } else {
            break                    -- everyone is suspended forever
        }
    }
}

task main() -> void {
    oni::summon("greet", 3)
    oni::summon("greet", 1)
    oni::summon("greet", 2)
    parade()
}
```

This prints oni 1, 2 and 3 in order, after about 30 ms in total rather than 60.

## What yields

Inside an oni, these calls park instead of blocking the thread:

| Call | Parks until |
|---|---|
| `time::sleep(ms)` | the deadline passes (`ms <= 0` just yields) |
| `tcp::socket_connect` | the connection completes or fails |
| `tcp::socket_accept` | a client is waiting |
| `tcp::socket_receive` | bytes, EOF or an error |
| `tcp::socket_send` / `socket_send_all` | the kernel takes more bytes |
| `oni::suspend()` / `oni::suspend_for(ms)` | `oni::wake(h)` (or the timeout) |

`tcp::socket_set_timeout` still applies. Inside an oni a receive or send
timeout becomes a park deadline and ends with the usual timeout status.
Closing a socket wakes any oni parked on it.

Outside an oni (on the main stack) nothing changes: every call blocks as before.

## API

| Builtin | Meaning |
|---|---|
| `oni::summon("task", arg) -> int` | New oni running `task(arg)`, queued ready. The name must be a string literal naming a top-level `task (int) -> void` or `(int) -> int`. Returns a handle. |
| `oni::next_ready() -> int` | Pop the ready queue, or 0 when it is empty. |
| `oni::resume(h) -> int` | Run `h` until it parks or finishes. Main stack only. Returns its state. |
| `oni::poll(timeout_ms) -> int` | Wait for sockets and deadlines and mark the woken oni ready. `-1` waits until something can wake, and returns at once if nothing can. Returns how many woke. Main stack only. |
| `oni::suspend()` | Park the current oni until `oni::wake`. |
| `oni::suspend_for(ms) -> bool` | The same, with a deadline. `true` = woken, `false` = timed out or cancelled. |
| `oni::wake(h)` | Make a parked oni ready. |
| `oni::cancel(h)` | Mark `h` cancelled and wake it. It decides how to stop. |
| `oni::cancelled() -> bool` | Has the current oni been cancelled? |
| `oni::timed_out() -> bool` | Did the current oni's last park end by deadline or curfew? |
| `oni::curfew(ms)` | Every park of the current oni ends by this deadline (`0` lifts it). |
| `oni::current() -> int` | The current oni's handle, or 0 on the main stack. |
| `oni::state(h) -> int` | 0 free, 1 ready, 2 running, 3 parked, 4 done. |
| `oni::returned(h) -> int` | What an `-> int` oni gave back. |
| `oni::release(h)` | Recycle a finished oni's slot. Its handle goes stale. |
| `oni::stack_kib(n)` | Stack size for oni summoned after this (default 256 KiB). |
| `oni::live() -> int` | Oni summoned and not yet done. |
| `oni::waiting() -> int` | Oni the runtime itself can wake (socket or deadline parks). |
| `oni::ready_count() -> int` | Length of the ready queue. |

Handles are generation-checked, so a released handle never aliases a new oni.

## Limits and sharp edges

- **One thread.** Every oni runs on the thread that summoned it. A busy oni
  that never parks starves the others. Call `time::sleep(0)` to bow out.
- **Stack size.** Each oni gets a fixed stack (256 KiB by default) with a
  guard page. Deep recursion inside an oni needs `oni::stack_kib(...)`
  first. An overflow crashes the process, the same way an overflow on the
  main stack does.
- **Resume and poll only from the main stack.** Nesting a resume inside an
  oni fails with `FREAK: oni: resume is only allowed from the main stack`.
- **Blocking calls still block.** `fs::*`, `process::*`, `http::*` (the
  client) and `http_server::*` are unchanged and block the whole parade.
  An async `http_server` lands after the event-loop poller is shared.
- **Platforms.** x86-64 and AArch64 on Linux (epoll) and macOS (poll), and
  Windows x64 (Fibers + WSAPoll).

## Under the hood

`freakc/runtime/freak_v35_oni.inc` holds the whole hook: a slot table with
generation handles, a ready ring, a deadline min-heap, per-socket
interest, hand-written stack switches (Fibers on Windows), and the
`freak_llvm_oni_*` adapters. `oni::summon` is the only compiler change:
the checker resolves the task name, and the emitters pass its address.
