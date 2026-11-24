/* ------------------------------------------------------------------ */
/*  std hook: oni (green tasks for the hyakki runtime)                */
/*                                                                    */
/*  An oni is a FREAK task with its own stack. The runtime owns only  */
/*  what FREAK code cannot do itself: making stacks, switching to and */
/*  from them, and waiting on sockets and deadlines. The scheduling   */
/*  loop (which ready oni runs next, joins, channels) belongs to the  */
/*  hyakki Hangar package, which drives these primitives from the     */
/*  main stack:                                                       */
/*                                                                    */
/*    oni::summon("task", arg)  new oni, queued ready                 */
/*    oni::next_ready()         pop the ready queue (0 when empty)    */
/*    oni::resume(h)            run h until it parks or finishes      */
/*    oni::poll(timeout_ms)     wait for sockets and deadlines        */
/*                                                                    */
/*  Inside an oni, tcp::socket_* and time::sleep park the oni instead */
/*  of blocking the thread. Outside an oni nothing changes.           */
/*                                                                    */
/*  Stacks: hand-written switches for x86-64 and AArch64 (System V    */
/*  and Darwin), Fibers on Windows. One OS thread runs every oni.     */
/* ------------------------------------------------------------------ */

#if defined(__has_feature)
#if __has_feature(address_sanitizer)
#define FREAK_ONI_ASAN 1
#endif
#endif
#if defined(__SANITIZE_ADDRESS__) && !defined(FREAK_ONI_ASAN)
#define FREAK_ONI_ASAN 1
#endif
#ifdef FREAK_ONI_ASAN
void __sanitizer_start_switch_fiber(void** fake_stack_save, const void* bottom, size_t size);
void __sanitizer_finish_switch_fiber(void* fake_stack_save, const void** bottom_old, size_t* size_old);
#endif

#if defined(_WIN32)
#define FREAK_ONI_FIBERS 1
#elif defined(__x86_64__) || defined(__aarch64__) || defined(__arm64__)
#define FREAK_ONI_ASM 1
#include <sys/mman.h>
#if !defined(MAP_ANON) && defined(MAP_ANONYMOUS)
#define MAP_ANON MAP_ANONYMOUS
#endif
#if !defined(MAP_ANON) && defined(__linux__)
#define MAP_ANON 0x20 /* _POSIX_C_SOURCE hides it; same value on every Linux arch we build */
#endif
#endif

#if defined(__linux__)
#include <sys/epoll.h>
#define FREAK_ONI_EPOLL 1
#endif

#define FREAK_ONI_HANDLE_DOMAIN UINT64_C(0x4f4e000000000000) /* "ON" */
#define FREAK_ONI_DOMAIN_MASK UINT64_C(0xffff000000000000)
#define FREAK_ONI_GENERATION_MAX UINT32_C(0xffff)

enum {
    FREAK_ONI_FREE = 0,
    FREAK_ONI_READY = 1,
    FREAK_ONI_RUNNING = 2,
    FREAK_ONI_PARKED = 3,
    FREAK_ONI_DONE = 4
};

enum {
    FREAK_ONI_PARK_NONE = 0,   /* manual: only oni::wake ends it */
    FREAK_ONI_PARK_SLEEP = 1,  /* deadline only */
    FREAK_ONI_PARK_READ = 2,   /* socket readable (or deadline) */
    FREAK_ONI_PARK_WRITE = 3   /* socket writable (or deadline) */
};

/* Why a park ended. */
enum {
    FREAK_ONI_WOKE_NONE = 0,
    FREAK_ONI_WOKE_READY = 1,     /* the socket became ready, or oni::wake */
    FREAK_ONI_WOKE_TIMEOUT = 2,   /* the deadline passed */
    FREAK_ONI_WOKE_CANCELLED = 3  /* oni::cancel */
};

typedef struct {
    uint32_t generation;
    int state;
    int park_kind;
    int woke;
    bool returns_int;
    bool cancelled;
    bool in_ready_queue;
    bool curfew_cut;       /* this park's deadline came from the curfew */
    int64_t next_free;
    int64_t entry;
    int64_t argument;
    int64_t result;
    int64_t deadline_ms;   /* absolute monotonic ms; 0 = none */
    int64_t curfew_ms;     /* absolute monotonic ms; 0 = none */
    int64_t park_sequence; /* bumps on every park, stales old heap entries; never reset */
    int64_t ready_ticket;  /* bumps on every enqueue, stales old ring entries; never reset */
    int64_t io_index;      /* position in freak_oni_io_slots while parked on a socket */
    int64_t io_next;       /* next oni parked on the same socket and direction (epoll) */
    uint64_t socket;       /* native socket when parked on READ/WRITE */
    size_t stack_size;
#ifdef FREAK_ONI_FIBERS
    LPVOID fiber;
#else
    void* stack_base;      /* mmap base, guard page first */
    size_t stack_mapped;
    void* sp;
#endif
} freak_oni_record;

static freak_oni_record* freak_onis = NULL;
static int64_t freak_oni_count = 0;
static int64_t freak_oni_capacity = 0;
static int64_t freak_oni_free_head = -1;
static int64_t freak_oni_current_slot = -1;
static int64_t freak_oni_live = 0;           /* summoned, not yet done */
static size_t freak_oni_stack_bytes = 256 * 1024;

/* Ready queue: a ring of (handle, ticket). An entry is live only while its
   ticket is the oni's latest, so a direct resume leaves no second entry. */
typedef struct { int64_t handle; int64_t ticket; } freak_oni_ready_entry;
static freak_oni_ready_entry* freak_oni_ready = NULL;
static int64_t freak_oni_ready_capacity = 0;
static int64_t freak_oni_ready_head = 0;
static int64_t freak_oni_ready_length = 0;
static int64_t freak_oni_ready_live = 0;   /* entries whose oni is still queued */

/* Deadline heap: (deadline, slot, park sequence), stale entries skipped. */
typedef struct { int64_t deadline_ms; int64_t slot; int64_t sequence; } freak_oni_timer;
static freak_oni_timer* freak_oni_timers = NULL;
static int64_t freak_oni_timer_count = 0;
static int64_t freak_oni_timer_capacity = 0;
static int64_t freak_oni_timer_compact_at = 64; /* sweep stale timers at this size */

/* Socket parks, for the poll() / WSAPoll path and for counting. */
static int64_t* freak_oni_io_slots = NULL;
static int64_t freak_oni_io_count = 0;
static int64_t freak_oni_io_capacity = 0;
static int64_t freak_oni_deadline_parks = 0; /* parked with a deadline but no socket */

#ifdef FREAK_ONI_FIBERS
static LPVOID freak_oni_main_fiber = NULL;
#else
static void* freak_oni_main_sp = NULL;
#endif
#ifdef FREAK_ONI_ASAN
static const void* freak_oni_main_stack_bottom = NULL;
static size_t freak_oni_main_stack_size = 0;
#endif

static _Noreturn void freak_oni_fail(const char* message) {
    fprintf(stderr, "FREAK: oni: %s\n", message);
    exit(1);
}

static int64_t freak_oni_now_ms(void) {
    return freak_time_monotonic_ns() / 1000000;
}

static void* freak_oni_grow(void* data, int64_t* capacity, size_t item, const char* what) {
    int64_t next = *capacity == 0 ? 64 : *capacity * 2;
    if (next <= *capacity || (uint64_t)next > SIZE_MAX / item) freak_oni_fail(what);
    void* grown = realloc(data, (size_t)next * item);
    if (!grown) freak_oni_fail(what);
    *capacity = next;
    return grown;
}

static int64_t freak_oni_make_handle(int64_t slot) {
    return (int64_t)(FREAK_ONI_HANDLE_DOMAIN |
        ((uint64_t)freak_onis[slot].generation << 32) | (uint64_t)(uint32_t)slot);
}

static int64_t freak_oni_slot(int64_t handle) {
    uint64_t raw = (uint64_t)handle;
    if ((raw & FREAK_ONI_DOMAIN_MASK) != FREAK_ONI_HANDLE_DOMAIN) return -1;
    int64_t slot = (int64_t)(uint32_t)(raw & UINT64_C(0xffffffff));
    uint32_t generation = (uint32_t)(raw >> 32) & FREAK_ONI_GENERATION_MAX;
    if (slot < 0 || slot >= freak_oni_count) return -1;
    if (freak_onis[slot].state == FREAK_ONI_FREE) return -1;
    if (freak_onis[slot].generation != generation) return -1;
    return slot;
}

static freak_oni_record* freak_oni_require(int64_t handle, const char* operation) {
    int64_t slot = freak_oni_slot(handle);
    if (slot < 0) {
        fprintf(stderr, "FREAK: oni: invalid or released oni handle in %s\n", operation);
        exit(1);
    }
    return &freak_onis[slot];
}

static bool freak_oni_inside(void) { return freak_oni_current_slot >= 0; }

static void freak_oni_queue_ready(int64_t slot) {
    freak_oni_record* oni = &freak_onis[slot];
    if (oni->in_ready_queue) return;
    if (freak_oni_ready_length == freak_oni_ready_capacity) {
        int64_t old = freak_oni_ready_capacity;
        freak_oni_ready_entry* grown = (freak_oni_ready_entry*)freak_oni_grow(
            NULL, &freak_oni_ready_capacity, sizeof(freak_oni_ready_entry), "ready queue is too large");
        for (int64_t i = 0; i < freak_oni_ready_length; i++) {
            grown[i] = freak_oni_ready[(freak_oni_ready_head + i) % old];
        }
        free(freak_oni_ready);
        freak_oni_ready = grown;
        freak_oni_ready_head = 0;
    }
    oni->ready_ticket += 1;
    freak_oni_ready_entry* entry =
        &freak_oni_ready[(freak_oni_ready_head + freak_oni_ready_length) % freak_oni_ready_capacity];
    entry->handle = freak_oni_make_handle(slot);
    entry->ticket = oni->ready_ticket;
    freak_oni_ready_length += 1;
    freak_oni_ready_live += 1;
    oni->in_ready_queue = true;
    oni->state = oni->state == FREAK_ONI_PARKED ? FREAK_ONI_READY : oni->state;
}

/* ---- deadline heap ---------------------------------------------- */

static bool freak_oni_timer_live(const freak_oni_timer* timer);
static void freak_oni_timer_sift_down(int64_t i);

/* Timers of parks that ended early stay in the heap until they reach the
   head. When the heap doubles past its last sweep, drop every stale entry
   and rebuild, so memory follows live timers and not finished waits. */
static void freak_oni_timer_compact(void) {
    int64_t kept = 0;
    for (int64_t i = 0; i < freak_oni_timer_count; i++) {
        if (freak_oni_timer_live(&freak_oni_timers[i])) freak_oni_timers[kept++] = freak_oni_timers[i];
    }
    freak_oni_timer_count = kept;
    for (int64_t i = kept / 2 - 1; i >= 0; i--) freak_oni_timer_sift_down(i);
    freak_oni_timer_compact_at = kept * 2 > 64 ? kept * 2 : 64;
}

static void freak_oni_timer_push(int64_t deadline_ms, int64_t slot, int64_t sequence) {
    if (freak_oni_timer_count >= freak_oni_timer_compact_at) freak_oni_timer_compact();
    if (freak_oni_timer_count == freak_oni_timer_capacity) {
        freak_oni_timers = (freak_oni_timer*)freak_oni_grow(
            freak_oni_timers, &freak_oni_timer_capacity, sizeof(freak_oni_timer),
            "deadline heap is too large");
    }
    int64_t i = freak_oni_timer_count++;
    freak_oni_timers[i].deadline_ms = deadline_ms;
    freak_oni_timers[i].slot = slot;
    freak_oni_timers[i].sequence = sequence;
    while (i > 0) {
        int64_t parent = (i - 1) / 2;
        if (freak_oni_timers[parent].deadline_ms <= freak_oni_timers[i].deadline_ms) break;
        freak_oni_timer swap = freak_oni_timers[parent];
        freak_oni_timers[parent] = freak_oni_timers[i];
        freak_oni_timers[i] = swap;
        i = parent;
    }
}

static void freak_oni_timer_sift_down(int64_t i) {
    for (;;) {
        int64_t left = i * 2 + 1, right = left + 1, best = i;
        if (left < freak_oni_timer_count &&
                freak_oni_timers[left].deadline_ms < freak_oni_timers[best].deadline_ms) best = left;
        if (right < freak_oni_timer_count &&
                freak_oni_timers[right].deadline_ms < freak_oni_timers[best].deadline_ms) best = right;
        if (best == i) break;
        freak_oni_timer swap = freak_oni_timers[best];
        freak_oni_timers[best] = freak_oni_timers[i];
        freak_oni_timers[i] = swap;
        i = best;
    }
}

static void freak_oni_timer_pop(void) {
    freak_oni_timer_count -= 1;
    if (freak_oni_timer_count == 0) return;
    freak_oni_timers[0] = freak_oni_timers[freak_oni_timer_count];
    freak_oni_timer_sift_down(0);
}

static bool freak_oni_timer_live(const freak_oni_timer* timer) {
    freak_oni_record* oni = &freak_onis[timer->slot];
    return oni->state == FREAK_ONI_PARKED && oni->park_sequence == timer->sequence;
}

/* Earliest live deadline, 0 when none. Drops stale heads. */
static int64_t freak_oni_next_deadline(void) {
    while (freak_oni_timer_count > 0 && !freak_oni_timer_live(&freak_oni_timers[0])) {
        freak_oni_timer_pop();
    }
    return freak_oni_timer_count > 0 ? freak_oni_timers[0].deadline_ms : 0;
}

/* ---- socket readiness ------------------------------------------- */

#ifdef FREAK_ONI_EPOLL
static int freak_oni_epoll = -1;
/* Per-fd interest: which oni read and which write. */
typedef struct { int64_t reader; int64_t writer; uint32_t events; } freak_oni_fd_interest;
static freak_oni_fd_interest* freak_oni_fds = NULL;
static int64_t freak_oni_fd_capacity = 0;

static freak_oni_fd_interest* freak_oni_fd_entry(int fd) {
    while ((int64_t)fd >= freak_oni_fd_capacity) {
        int64_t old = freak_oni_fd_capacity;
        freak_oni_fds = (freak_oni_fd_interest*)freak_oni_grow(
            freak_oni_fds, &freak_oni_fd_capacity, sizeof(freak_oni_fd_interest),
            "socket interest table is too large");
        for (int64_t i = old; i < freak_oni_fd_capacity; i++) {
            freak_oni_fds[i].reader = -1;
            freak_oni_fds[i].writer = -1;
            freak_oni_fds[i].events = 0;
        }
    }
    return &freak_oni_fds[fd];
}

/* Each socket is registered once, edge-triggered, for both directions, and
   stays registered until it closes. Callers try the read, write or accept
   first and park only on EAGAIN, so an edge that fires while nobody waits
   is never needed. This keeps epoll_ctl off the per-message path. */
static void freak_oni_epoll_sync(int fd) {
    freak_oni_fd_interest* entry = freak_oni_fd_entry(fd);
    if (entry->events != 0) return;
    if (entry->reader < 0 && entry->writer < 0) return;
    if (freak_oni_epoll < 0) {
        freak_oni_epoll = epoll_create1(EPOLL_CLOEXEC);
        if (freak_oni_epoll < 0) freak_oni_fail("cannot create the epoll poller");
    }
    struct epoll_event event;
    memset(&event, 0, sizeof(event));
    event.events = EPOLLIN | EPOLLOUT | EPOLLRDHUP | EPOLLET;
    event.data.u64 = (uint64_t)fd;
    if (epoll_ctl(freak_oni_epoll, EPOLL_CTL_ADD, fd, &event) != 0) {
        if (errno != EEXIST || epoll_ctl(freak_oni_epoll, EPOLL_CTL_MOD, fd, &event) != 0) {
            freak_oni_fail("cannot register a socket with epoll");
        }
    }
    entry->events = event.events;
}

/* The socket is closing: forget its registration (close removes it from epoll). */
static void freak_oni_epoll_forget(int fd) {
    if (fd < 0 || (int64_t)fd >= freak_oni_fd_capacity) return;
    freak_oni_fd_interest* entry = &freak_oni_fds[fd];
    if (entry->events != 0 && freak_oni_epoll >= 0) {
        struct epoll_event event;
        memset(&event, 0, sizeof(event));
        (void)epoll_ctl(freak_oni_epoll, EPOLL_CTL_DEL, fd, &event);
    }
    entry->events = 0;
}
#endif

static void freak_oni_io_add(int64_t slot) {
    if (freak_oni_io_count == freak_oni_io_capacity) {
        freak_oni_io_slots = (int64_t*)freak_oni_grow(
            freak_oni_io_slots, &freak_oni_io_capacity, sizeof(int64_t),
            "socket park table is too large");
    }
    freak_onis[slot].io_index = freak_oni_io_count;
    freak_oni_io_slots[freak_oni_io_count++] = slot;
#ifdef FREAK_ONI_EPOLL
    /* Every oni waiting on a socket in one direction is kept, newest first. */
    freak_oni_record* oni = &freak_onis[slot];
    freak_oni_fd_interest* entry = freak_oni_fd_entry((int)oni->socket);
    if (oni->park_kind == FREAK_ONI_PARK_READ) {
        oni->io_next = entry->reader;
        entry->reader = slot;
    } else {
        oni->io_next = entry->writer;
        entry->writer = slot;
    }
    freak_oni_epoll_sync((int)oni->socket);
#endif
}

static void freak_oni_io_remove(int64_t slot) {
    int64_t index = freak_onis[slot].io_index;
    if (index >= 0 && index < freak_oni_io_count && freak_oni_io_slots[index] == slot) {
        int64_t moved = freak_oni_io_slots[--freak_oni_io_count];
        freak_oni_io_slots[index] = moved;
        freak_onis[moved].io_index = index;
    }
    freak_onis[slot].io_index = -1;
#ifdef FREAK_ONI_EPOLL
    freak_oni_record* oni = &freak_onis[slot];
    freak_oni_fd_interest* entry = freak_oni_fd_entry((int)oni->socket);
    int64_t* link = oni->park_kind == FREAK_ONI_PARK_READ ? &entry->reader : &entry->writer;
    while (*link >= 0 && *link != slot) link = &freak_onis[*link].io_next;
    if (*link == slot) *link = oni->io_next;
    oni->io_next = -1;
#endif
}

static void freak_oni_unpark(int64_t slot, int woke);

#ifdef FREAK_ONI_EPOLL
/* Wake every oni on one socket list; each retries its call and re-parks if it lost the race. */
static int64_t freak_oni_wake_list(int64_t head) {
    int64_t woken = 0;
    while (head >= 0) {
        int64_t next = freak_onis[head].io_next;
        freak_oni_unpark(head, FREAK_ONI_WOKE_READY);
        woken += 1;
        head = next;
    }
    return woken;
}
#endif

/* End a park: unhook it from sockets and the deadline count, queue it. */
static void freak_oni_unpark(int64_t slot, int woke) {
    freak_oni_record* oni = &freak_onis[slot];
    if (oni->state != FREAK_ONI_PARKED) return;
    if (oni->park_kind == FREAK_ONI_PARK_READ || oni->park_kind == FREAK_ONI_PARK_WRITE) {
        freak_oni_io_remove(slot);
    } else if (oni->deadline_ms != 0) {
        freak_oni_deadline_parks -= 1;
    }
    oni->woke = woke;
    oni->park_sequence += 1;
    freak_oni_queue_ready(slot);
}

/* ---- stacks and switching --------------------------------------- */

static void freak_oni_run_current(void);

#ifdef FREAK_ONI_ASM
#if defined(__APPLE__)
#define FREAK_ONI_SYM(name) "_" #name
#else
#define FREAK_ONI_SYM(name) #name
#endif

void freak_oni_switch(void** save_sp, void* load_sp);
void freak_oni_trampoline(void);

#if defined(__x86_64__)
__asm__(
    ".text\n"
    ".globl " FREAK_ONI_SYM(freak_oni_switch) "\n"
#if !defined(__APPLE__)
    ".type freak_oni_switch,@function\n"
#endif
    FREAK_ONI_SYM(freak_oni_switch) ":\n"
    "    pushq %rbp\n"
    "    pushq %rbx\n"
    "    pushq %r12\n"
    "    pushq %r13\n"
    "    pushq %r14\n"
    "    pushq %r15\n"
    "    subq $8, %rsp\n"
    "    stmxcsr (%rsp)\n"
    "    fnstcw 4(%rsp)\n"
    "    movq %rsp, (%rdi)\n"
    "    movq %rsi, %rsp\n"
    "    ldmxcsr (%rsp)\n"
    "    fldcw 4(%rsp)\n"
    "    addq $8, %rsp\n"
    "    popq %r15\n"
    "    popq %r14\n"
    "    popq %r13\n"
    "    popq %r12\n"
    "    popq %rbx\n"
    "    popq %rbp\n"
    "    ret\n"
);
#define FREAK_ONI_FRAME_WORDS 9
#else /* AArch64 */
__asm__(
    ".text\n"
    ".globl " FREAK_ONI_SYM(freak_oni_switch) "\n"
#if !defined(__APPLE__)
    ".type freak_oni_switch,%function\n"
#endif
    ".p2align 2\n"
    FREAK_ONI_SYM(freak_oni_switch) ":\n"
    "    sub sp, sp, #160\n"
    "    stp x19, x20, [sp, #0]\n"
    "    stp x21, x22, [sp, #16]\n"
    "    stp x23, x24, [sp, #32]\n"
    "    stp x25, x26, [sp, #48]\n"
    "    stp x27, x28, [sp, #64]\n"
    "    stp x29, x30, [sp, #80]\n"
    "    stp d8, d9, [sp, #96]\n"
    "    stp d10, d11, [sp, #112]\n"
    "    stp d12, d13, [sp, #128]\n"
    "    stp d14, d15, [sp, #144]\n"
    "    mov x2, sp\n"
    "    str x2, [x0]\n"
    "    mov sp, x1\n"
    "    ldp x19, x20, [sp, #0]\n"
    "    ldp x21, x22, [sp, #16]\n"
    "    ldp x23, x24, [sp, #32]\n"
    "    ldp x25, x26, [sp, #48]\n"
    "    ldp x27, x28, [sp, #64]\n"
    "    ldp x29, x30, [sp, #80]\n"
    "    ldp d8, d9, [sp, #96]\n"
    "    ldp d10, d11, [sp, #112]\n"
    "    ldp d12, d13, [sp, #128]\n"
    "    ldp d14, d15, [sp, #144]\n"
    "    add sp, sp, #160\n"
    "    ret\n"
);
#endif

void freak_oni_trampoline(void) {
#ifdef FREAK_ONI_ASAN
    __sanitizer_finish_switch_fiber(NULL, &freak_oni_main_stack_bottom, &freak_oni_main_stack_size);
#endif
    freak_oni_run_current();
    freak_oni_fail("a finished oni was resumed");
}

static size_t freak_oni_page(void) {
    long page = sysconf(_SC_PAGESIZE);
    return page > 0 ? (size_t)page : 4096;
}

static void freak_oni_stack_make(freak_oni_record* oni) {
    size_t page = freak_oni_page();
    size_t usable = (oni->stack_size + page - 1) / page * page;
    size_t mapped = usable + page;
    void* base = mmap(NULL, mapped, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON, -1, 0);
    if (base == MAP_FAILED) freak_oni_fail("out of memory for an oni stack");
    if (mprotect(base, page, PROT_NONE) != 0) freak_oni_fail("cannot protect an oni stack guard page");
    oni->stack_base = base;
    oni->stack_mapped = mapped;
    uintptr_t top = ((uintptr_t)base + mapped) & ~(uintptr_t)15;
    uintptr_t* frame;
#if defined(__x86_64__)
    /* [csr][r15][r14][r13][r12][rbx][rbp][ret=trampoline][fake return] */
    frame = (uintptr_t*)(top - 8 * FREAK_ONI_FRAME_WORDS);
    memset(frame, 0, 8 * FREAK_ONI_FRAME_WORDS);
    uint32_t csr[2] = { 0x1F80, 0x037F };
    memcpy(&frame[0], csr, sizeof(csr));
    frame[7] = (uintptr_t)&freak_oni_trampoline;
    frame[8] = 0;
#else
    /* x19..x28, x29, x30=trampoline, d8..d15 */
    frame = (uintptr_t*)(top - 160);
    memset(frame, 0, 160);
    frame[11] = (uintptr_t)&freak_oni_trampoline;
#endif
    oni->sp = frame;
}

static void freak_oni_stack_free(freak_oni_record* oni) {
    if (oni->stack_base) munmap(oni->stack_base, oni->stack_mapped);
    oni->stack_base = NULL;
    oni->sp = NULL;
}

static void freak_oni_switch_in(freak_oni_record* oni) {
#ifdef FREAK_ONI_ASAN
    void* fake = NULL;
    __sanitizer_start_switch_fiber(&fake, (char*)oni->stack_base + freak_oni_page(),
                                   oni->stack_mapped - freak_oni_page());
#endif
    freak_oni_switch(&freak_oni_main_sp, oni->sp);
#ifdef FREAK_ONI_ASAN
    __sanitizer_finish_switch_fiber(fake, NULL, NULL);
#endif
}

static void freak_oni_switch_out(freak_oni_record* oni, bool finished) {
#ifdef FREAK_ONI_ASAN
    void* fake = NULL;
    __sanitizer_start_switch_fiber(finished ? NULL : &fake,
                                   freak_oni_main_stack_bottom, freak_oni_main_stack_size);
#endif
    freak_oni_switch(&oni->sp, freak_oni_main_sp);
#ifdef FREAK_ONI_ASAN
    __sanitizer_finish_switch_fiber(fake, &freak_oni_main_stack_bottom, &freak_oni_main_stack_size);
#endif
}
#elif defined(FREAK_ONI_FIBERS)
static VOID CALLBACK freak_oni_fiber_entry(LPVOID parameter) {
    (void)parameter;
    freak_oni_run_current();
    freak_oni_fail("a finished oni was resumed");
}

static void freak_oni_stack_make(freak_oni_record* oni) {
    if (!freak_oni_main_fiber) {
        freak_oni_main_fiber = IsThreadAFiber() ? GetCurrentFiber() : ConvertThreadToFiber(NULL);
        if (!freak_oni_main_fiber) freak_oni_fail("cannot convert the main thread to a fiber");
    }
    oni->fiber = CreateFiberEx(64 * 1024, oni->stack_size, FIBER_FLAG_FLOAT_SWITCH,
                               freak_oni_fiber_entry, NULL);
    if (!oni->fiber) freak_oni_fail("out of memory for an oni fiber");
}

static void freak_oni_stack_free(freak_oni_record* oni) {
    if (oni->fiber) DeleteFiber(oni->fiber);
    oni->fiber = NULL;
}

static void freak_oni_switch_in(freak_oni_record* oni) { SwitchToFiber(oni->fiber); }
static void freak_oni_switch_out(freak_oni_record* oni, bool finished) {
    (void)oni; (void)finished;
    SwitchToFiber(freak_oni_main_fiber);
}
#else
static void freak_oni_stack_make(freak_oni_record* oni) {
    (void)oni;
    freak_oni_fail("oni are not supported on this platform");
}
static void freak_oni_stack_free(freak_oni_record* oni) { (void)oni; }
static void freak_oni_switch_in(freak_oni_record* oni) { (void)oni; }
static void freak_oni_switch_out(freak_oni_record* oni, bool finished) { (void)oni; (void)finished; }
#endif

typedef void (*freak_oni_void_entry)(int64_t);
typedef int64_t (*freak_oni_int_entry)(int64_t);

static void freak_oni_run_current(void) {
    freak_oni_record* oni = &freak_onis[freak_oni_current_slot];
    if (oni->returns_int) {
        /* the table can grow while the task runs: store through a fresh pointer */
        int64_t result = ((freak_oni_int_entry)(intptr_t)oni->entry)(oni->argument);
        freak_onis[freak_oni_current_slot].result = result;
    } else {
        ((freak_oni_void_entry)(intptr_t)oni->entry)(oni->argument);
    }
    oni = &freak_onis[freak_oni_current_slot]; /* the table may have moved */
    oni->state = FREAK_ONI_DONE;
    freak_oni_live -= 1;
    freak_oni_switch_out(oni, true);
}

/* now + ms, saturating: a huge duration means "practically never". */
static int64_t freak_oni_deadline_after(int64_t now, int64_t ms) {
    if (ms > INT64_MAX - now) return INT64_MAX;
    return now + ms;
}

/* Park the running oni and switch back to the main stack. */
static int freak_oni_park(int kind, uint64_t socket, int64_t timeout_ms) {
    if (!freak_oni_inside()) freak_oni_fail("park called outside an oni");
    int64_t slot = freak_oni_current_slot;
    freak_oni_record* oni = &freak_onis[slot];
    if (oni->cancelled) { oni->woke = FREAK_ONI_WOKE_CANCELLED; return oni->woke; }
    int64_t now = 0;
    int64_t deadline = 0;
    bool curfew_cut = false;
    if (timeout_ms > 0) { now = freak_oni_now_ms(); deadline = freak_oni_deadline_after(now, timeout_ms); }
    if (oni->curfew_ms != 0) {
        if (deadline == 0 || oni->curfew_ms < deadline) { deadline = oni->curfew_ms; curfew_cut = true; }
        if (now == 0) now = freak_oni_now_ms();
        if (deadline <= now) { oni->woke = FREAK_ONI_WOKE_TIMEOUT; return oni->woke; }
    }
    oni->park_kind = kind;
    oni->socket = socket;
    oni->deadline_ms = deadline;
    oni->curfew_cut = curfew_cut;
    oni->woke = FREAK_ONI_WOKE_NONE;
    oni->park_sequence += 1;
    oni->state = FREAK_ONI_PARKED;
    if (deadline != 0) freak_oni_timer_push(deadline, slot, oni->park_sequence);
    if (kind == FREAK_ONI_PARK_READ || kind == FREAK_ONI_PARK_WRITE) freak_oni_io_add(slot);
    else if (deadline != 0) freak_oni_deadline_parks += 1;
    freak_oni_switch_out(oni, false);
    oni = &freak_onis[slot];
    oni->park_kind = FREAK_ONI_PARK_NONE;
    oni->deadline_ms = 0;
    return oni->woke;
}

/* ---- hooks used by tcp and time --------------------------------- */

/* true when inside an oni: the caller should use the parking path. */
static bool freak_oni_hooked(void) { return freak_oni_inside(); }

/* Wait for a socket inside an oni. 1 ready, 0 timed out or cancelled. */
static int freak_oni_wait_socket(uint64_t socket, bool for_write, int64_t timeout_ms) {
    int woke = freak_oni_park(
        for_write ? FREAK_ONI_PARK_WRITE : FREAK_ONI_PARK_READ, socket, timeout_ms);
    return woke == FREAK_ONI_WOKE_READY ? 1 : 0;
}

/* Cooperative budget: an oni whose socket calls keep succeeding without
   ever parking bows after this many, so one hot connection cannot starve
   the parade. Refilled on every resume. */
#define FREAK_ONI_BUDGET 128
static int64_t freak_oni_budget = FREAK_ONI_BUDGET;

static void freak_oni_sleep(int64_t ms);

static void freak_oni_spend(void) {
    if (!freak_oni_inside()) return;
    if (--freak_oni_budget > 0) return;
    freak_oni_sleep(0);
}

static void freak_oni_sleep(int64_t ms) {
    if (ms <= 0) {
        /* bow: let the others run */
        int64_t slot = freak_oni_current_slot;
        freak_onis[slot].park_sequence += 1;
        freak_onis[slot].state = FREAK_ONI_PARKED;
        freak_onis[slot].park_kind = FREAK_ONI_PARK_NONE;
        freak_oni_queue_ready(slot);
        freak_oni_switch_out(&freak_onis[slot], false);
        return;
    }
    freak_oni_park(FREAK_ONI_PARK_SLEEP, 0, ms);
}

/* A socket is closing: wake every oni parked on it (they find it gone). */
static void freak_oni_socket_closing(uint64_t socket) {
    for (int64_t i = freak_oni_io_count - 1; i >= 0; i--) {
        if (i >= freak_oni_io_count) continue;
        int64_t slot = freak_oni_io_slots[i];
        if (freak_onis[slot].socket == socket) freak_oni_unpark(slot, FREAK_ONI_WOKE_TIMEOUT);
    }
#ifdef FREAK_ONI_EPOLL
    freak_oni_epoll_forget((int)socket);
#endif
}

/* ---- the FREAK-facing API --------------------------------------- */

int64_t freak_oni_summon(int64_t entry, int64_t returns_int, int64_t argument) {
    if (entry == 0) freak_oni_fail("summon needs a task");
    int64_t slot = freak_oni_free_head;
    if (slot >= 0) {
        freak_oni_free_head = freak_onis[slot].next_free;
        freak_onis[slot].generation = (freak_onis[slot].generation + 1) & FREAK_ONI_GENERATION_MAX;
        if (freak_onis[slot].generation == 0) freak_onis[slot].generation = 1;
    } else {
        if (freak_oni_count == freak_oni_capacity) {
            int64_t old = freak_oni_capacity;
            freak_onis = (freak_oni_record*)freak_oni_grow(
                freak_onis, &freak_oni_capacity, sizeof(freak_oni_record), "oni table is too large");
            memset(freak_onis + old, 0, (size_t)(freak_oni_capacity - old) * sizeof(freak_oni_record));
        }
        if ((uint64_t)freak_oni_count >= UINT32_MAX) freak_oni_fail("oni table exhausted");
        slot = freak_oni_count++;
        freak_onis[slot].generation = 1;
    }
    freak_oni_record* oni = &freak_onis[slot];
    uint32_t generation = oni->generation;
    int64_t sequence = oni->park_sequence; /* stale timers of the last tenant must never match */
    int64_t ticket = oni->ready_ticket;    /* nor its stale ready entries */
    memset(oni, 0, sizeof(*oni));
    oni->generation = generation;
    oni->park_sequence = sequence + 1;
    oni->ready_ticket = ticket;
    oni->io_index = -1;
    oni->io_next = -1;
    oni->next_free = -1;
    oni->entry = entry;
    oni->returns_int = returns_int != 0;
    oni->argument = argument;
    oni->stack_size = freak_oni_stack_bytes;
    oni->state = FREAK_ONI_READY;
    freak_oni_stack_make(oni);
    freak_oni_live += 1;
    freak_oni_queue_ready(slot);
    return freak_oni_make_handle(slot);
}

int64_t freak_oni_resume(int64_t handle) {
    if (freak_oni_inside()) freak_oni_fail("resume is only allowed from the main stack (the parade loop)");
    int64_t slot = freak_oni_slot(handle);
    if (slot < 0) freak_oni_fail("invalid or released oni handle in resume");
    freak_oni_record* oni = &freak_onis[slot];
    if (oni->state == FREAK_ONI_DONE) return FREAK_ONI_DONE;
    if (oni->state == FREAK_ONI_PARKED) {
        /* resuming a parked oni ends its park as an explicit wake */
        freak_oni_unpark(slot, FREAK_ONI_WOKE_READY);
    }
    if (oni->in_ready_queue) {
        /* leave the queue entry; next_ready skips oni that are not READY */
        oni->in_ready_queue = false;
        freak_oni_ready_live -= 1;
    }
    oni->state = FREAK_ONI_RUNNING;
    freak_oni_current_slot = slot;
    freak_oni_budget = FREAK_ONI_BUDGET;
    freak_oni_switch_in(oni);
    freak_oni_current_slot = -1;
    oni = &freak_onis[slot];
    if (oni->state == FREAK_ONI_DONE) freak_oni_stack_free(oni);
    return oni->state;
}

int64_t freak_oni_next_ready(void) {
    while (freak_oni_ready_length > 0) {
        freak_oni_ready_entry entry = freak_oni_ready[freak_oni_ready_head];
        int64_t handle = entry.handle;
        freak_oni_ready_head = (freak_oni_ready_head + 1) % freak_oni_ready_capacity;
        freak_oni_ready_length -= 1;
        int64_t slot = freak_oni_slot(handle);
        if (slot < 0) continue;
        freak_oni_record* oni = &freak_onis[slot];
        if (!oni->in_ready_queue || entry.ticket != oni->ready_ticket) continue;
        oni->in_ready_queue = false;
        freak_oni_ready_live -= 1;
        if (oni->state != FREAK_ONI_READY) continue;
        return handle;
    }
    return 0;
}

void freak_oni_suspend(void) {
    if (!freak_oni_inside()) freak_oni_fail("suspend called outside an oni");
    freak_oni_park(FREAK_ONI_PARK_NONE, 0, 0);
}

/* Park until oni::wake or the timeout. true = woken, false = timed out or cancelled. */
bool freak_oni_suspend_for(int64_t timeout_ms) {
    if (!freak_oni_inside()) freak_oni_fail("suspend_for called outside an oni");
    int woke = freak_oni_park(FREAK_ONI_PARK_NONE, 0, timeout_ms > 0 ? timeout_ms : 0);
    return woke == FREAK_ONI_WOKE_READY;
}

void freak_oni_wake(int64_t handle) {
    int64_t slot = freak_oni_slot(handle);
    if (slot < 0) return;
    freak_oni_unpark(slot, FREAK_ONI_WOKE_READY);
}

void freak_oni_cancel(int64_t handle) {
    int64_t slot = freak_oni_slot(handle);
    if (slot < 0) return;
    freak_oni_record* oni = &freak_onis[slot];
    if (oni->state == FREAK_ONI_DONE) return;
    oni->cancelled = true;
    freak_oni_unpark(slot, FREAK_ONI_WOKE_CANCELLED);
}

bool freak_oni_cancelled(void) {
    return freak_oni_inside() && freak_onis[freak_oni_current_slot].cancelled;
}

bool freak_oni_timed_out(void) {
    return freak_oni_inside() && freak_onis[freak_oni_current_slot].woke == FREAK_ONI_WOKE_TIMEOUT;
}

int64_t freak_oni_current(void) {
    return freak_oni_inside() ? freak_oni_make_handle(freak_oni_current_slot) : 0;
}

int64_t freak_oni_state(int64_t handle) {
    int64_t slot = freak_oni_slot(handle);
    return slot < 0 ? 0 : freak_onis[slot].state;
}

int64_t freak_oni_returned(int64_t handle) {
    return freak_oni_require(handle, "returned")->result;
}

void freak_oni_release(int64_t handle) {
    int64_t slot = freak_oni_slot(handle);
    if (slot < 0) return;
    freak_oni_record* oni = &freak_onis[slot];
    if (oni->state != FREAK_ONI_DONE) freak_oni_fail("release of an oni that has not finished");
    if (oni->in_ready_queue) {
        oni->in_ready_queue = false;
        freak_oni_ready_live -= 1;
    }
    oni->state = FREAK_ONI_FREE;
    /* a slot whose generation is used up retires, so old handles never alias */
    if (oni->generation >= FREAK_ONI_GENERATION_MAX) return;
    oni->next_free = freak_oni_free_head;
    freak_oni_free_head = slot;
}

void freak_oni_curfew(int64_t ms) {
    if (!freak_oni_inside()) freak_oni_fail("curfew called outside an oni");
    freak_onis[freak_oni_current_slot].curfew_ms =
        ms > 0 ? freak_oni_deadline_after(freak_oni_now_ms(), ms) : 0;
}

void freak_oni_stack_kib(int64_t kib) {
    if (kib < 16 || kib > 1024 * 1024) freak_oni_fail("stack_kib must be between 16 and 1048576");
    freak_oni_stack_bytes = (size_t)kib * 1024;
}

int64_t freak_oni_live_count(void) { return freak_oni_live; }

/* Oni the runtime itself can wake: socket parks plus deadline parks. */
int64_t freak_oni_waiting(void) { return freak_oni_io_count + freak_oni_deadline_parks; }

int64_t freak_oni_ready_count(void) { return freak_oni_ready_live; }

static int64_t freak_oni_fire_deadlines(int64_t now) {
    int64_t woken = 0;
    while (freak_oni_next_deadline() != 0 && freak_oni_timers[0].deadline_ms <= now) {
        int64_t slot = freak_oni_timers[0].slot;
        freak_oni_timer_pop();
        /* a finished sleep is a normal wake; any other deadline is a timeout */
        bool slept = freak_onis[slot].park_kind == FREAK_ONI_PARK_SLEEP && !freak_onis[slot].curfew_cut;
        freak_oni_unpark(slot, slept ? FREAK_ONI_WOKE_READY : FREAK_ONI_WOKE_TIMEOUT);
        woken += 1;
    }
    return woken;
}

/* Wait for sockets and deadlines. timeout_ms < 0 waits until something
   wakes (returns at once when nothing could). Returns oni woken. */
int64_t freak_oni_poll(int64_t timeout_ms) {
    if (freak_oni_inside()) freak_oni_fail("poll is only allowed from the main stack (the parade loop)");
    int64_t now = freak_oni_now_ms();
    int64_t woken = freak_oni_fire_deadlines(now);
    if (woken > 0 || freak_oni_ready_live > 0) timeout_ms = 0;
    if (freak_oni_io_count == 0 && freak_oni_deadline_parks == 0) return woken;
    int64_t next = freak_oni_next_deadline();
    if (next != 0) {
        int64_t until = next - now;
        if (until < 0) until = 0;
        if (timeout_ms < 0 || until < timeout_ms) timeout_ms = until;
    }
    int wait = timeout_ms < 0 ? -1 : (timeout_ms > INT_MAX ? INT_MAX : (int)timeout_ms);
    if (freak_oni_io_count == 0) {
        if (wait > 0) freak_time_sleep(wait);
    } else {
#if defined(FREAK_ONI_EPOLL)
        struct epoll_event events[256];
        int ready;
        /* a signal (EINTR) ends this wait early; the deadlines below run and
           the caller polls again with the remaining time */
        ready = epoll_wait(freak_oni_epoll, events, 256, wait);
        for (int i = 0; i < ready; i++) {
            int fd = (int)events[i].data.u64;
            freak_oni_fd_interest* entry = freak_oni_fd_entry(fd);
            uint32_t got = events[i].events;
            bool failed = (got & (EPOLLERR | EPOLLHUP)) != 0;
            if (failed || (got & (EPOLLIN | EPOLLRDHUP))) woken += freak_oni_wake_list(entry->reader);
            if (failed || (got & EPOLLOUT)) woken += freak_oni_wake_list(entry->writer);
        }
#else
        int64_t count = freak_oni_io_count;
#ifdef _WIN32
        WSAPOLLFD* fds = (WSAPOLLFD*)calloc((size_t)count, sizeof(WSAPOLLFD));
#else
        struct pollfd* fds = (struct pollfd*)calloc((size_t)count, sizeof(struct pollfd));
#endif
        int64_t* slots = (int64_t*)calloc((size_t)count, sizeof(int64_t));
        if (!fds || !slots) freak_oni_fail("out of memory polling sockets");
        for (int64_t i = 0; i < count; i++) {
            int64_t slot = freak_oni_io_slots[i];
            slots[i] = slot;
#ifdef _WIN32
            fds[i].fd = (SOCKET)freak_onis[slot].socket;
#else
            fds[i].fd = (int)freak_onis[slot].socket;
#endif
            fds[i].events = freak_onis[slot].park_kind == FREAK_ONI_PARK_READ ? POLLIN : POLLOUT;
        }
        int ready;
#ifdef _WIN32
        ready = WSAPoll(fds, (ULONG)count, wait);
#else
        ready = poll(fds, (nfds_t)count, wait); /* EINTR: see the epoll branch */
#endif
        if (ready > 0) {
            for (int64_t i = 0; i < count; i++) {
                if (fds[i].revents != 0) {
                    freak_oni_unpark(slots[i], FREAK_ONI_WOKE_READY);
                    woken += 1;
                }
            }
        }
        free(fds);
        free(slots);
#endif
    }
    woken += freak_oni_fire_deadlines(freak_oni_now_ms());
    return woken;
}

/* ---- LLVM adapters (every value is i64) ------------------------- */

int64_t freak_llvm_oni_summon(int64_t entry, int64_t returns_int, int64_t argument) {
    return freak_oni_summon(entry, returns_int, argument);
}
int64_t freak_llvm_oni_resume(int64_t handle) { return freak_oni_resume(handle); }
int64_t freak_llvm_oni_next_ready(void) { return freak_oni_next_ready(); }
void freak_llvm_oni_suspend(void) { freak_oni_suspend(); }
int64_t freak_llvm_oni_suspend_for(int64_t ms) { return freak_oni_suspend_for(ms) ? 1 : 0; }
void freak_llvm_oni_wake(int64_t handle) { freak_oni_wake(handle); }
void freak_llvm_oni_cancel(int64_t handle) { freak_oni_cancel(handle); }
int64_t freak_llvm_oni_cancelled(void) { return freak_oni_cancelled() ? 1 : 0; }
int64_t freak_llvm_oni_timed_out(void) { return freak_oni_timed_out() ? 1 : 0; }
int64_t freak_llvm_oni_current(void) { return freak_oni_current(); }
int64_t freak_llvm_oni_state(int64_t handle) { return freak_oni_state(handle); }
int64_t freak_llvm_oni_returned(int64_t handle) { return freak_oni_returned(handle); }
void freak_llvm_oni_release(int64_t handle) { freak_oni_release(handle); }
void freak_llvm_oni_curfew(int64_t ms) { freak_oni_curfew(ms); }
void freak_llvm_oni_stack_kib(int64_t kib) { freak_oni_stack_kib(kib); }
int64_t freak_llvm_oni_live(void) { return freak_oni_live_count(); }
int64_t freak_llvm_oni_waiting(void) { return freak_oni_waiting(); }
int64_t freak_llvm_oni_ready_count(void) { return freak_oni_ready_count(); }
int64_t freak_llvm_oni_poll(int64_t timeout_ms) { return freak_oni_poll(timeout_ms); }
