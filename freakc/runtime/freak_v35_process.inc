/* Included once by freak_runtime.c, after its owned words and byte buffers.
   A command is a sequential owner of a child process group/job and its pipes. */
#define FREAK_COMMAND_DOMAIN UINT64_C(0xa000000000000000)
#define FREAK_COMMAND_DOMAIN_MASK UINT64_C(0xe000000000000000)
#define FREAK_COMMAND_GENERATION_MAX UINT32_C(0x1fffffff)

typedef struct {
    unsigned char *data;
    size_t length, capacity, limit;
} freak_command_capture;

typedef struct {
    char **argv;
    size_t argc, argv_capacity;
    char *cwd;
    char **env_names, **env_values;
    size_t env_count;
    uint32_t generation;
    bool in_use, child_live, inherited;
    int status;
    int64_t exit_code, signal_number;
    uint64_t deadline_ms;
    char error[256];
    freak_command_capture output, errors;
#ifdef _WIN32
    HANDLE process, job, stdout_read, stderr_read;
#else
    pid_t pid;
    pid_t terminal_owner;
    int stdout_read, stderr_read;
#endif
} freak_command_record;

static freak_command_record *freak_commands = NULL;
static size_t freak_commands_count = 0;
static size_t freak_commands_capacity = 0;
static size_t freak_commands_live = 0;
static size_t freak_commands_children = 0;
static bool freak_commands_cleanup_registered = false;
#ifdef _WIN32
static wchar_t *freak_command_wide(const char *text);
#endif

static _Noreturn void freak_command_fail(const char *message) {
    fprintf(stderr, "FREAK: process command: %s\n", message);
    exit(1);
}

static void *freak_command_allocate(size_t count, size_t width) {
    if (width && count > SIZE_MAX / width) freak_command_fail("allocation size overflow");
    void *memory = calloc(count ? count : 1, width ? width : 1);
    if (!memory) freak_command_fail("out of memory");
    return memory;
}

static char *freak_command_copy(freak_word value, bool allow_empty) {
    if ((!allow_empty && !value.length) || value.length >= SIZE_MAX ||
            (value.length && (!value.data || memchr(value.data, 0, value.length))))
        freak_command_fail("empty or NUL-containing OS argument");
    if (!freak_system_utf8_valid(value.data, value.length))
        freak_command_fail("OS argument is not valid UTF-8");
    char *copy = freak_command_allocate(value.length + 1, 1);
    if (value.length) memcpy(copy, value.data, value.length);
    return copy;
}

static freak_command_record *freak_command_require(int64_t ticket) {
    uint64_t bits = (uint64_t)ticket;
    uint32_t slot = (uint32_t)bits;
    uint32_t generation = (uint32_t)((bits >> 32) & FREAK_COMMAND_GENERATION_MAX);
    if ((bits & FREAK_COMMAND_DOMAIN_MASK) != FREAK_COMMAND_DOMAIN || !slot ||
            (size_t)slot > freak_commands_count)
        freak_command_fail("invalid or stale command ticket");
    freak_command_record *command = &freak_commands[slot - 1];
    if (!command->in_use || command->generation != generation)
        freak_command_fail("invalid or stale command ticket");
    return command;
}

static void freak_command_configurable(freak_command_record *command) {
    if (command->status != FREAK_COMMAND_READY)
        freak_command_fail("command was already launched");
}

static uint64_t freak_command_now_ms(void) {
    return (uint64_t)freak_time_monotonic_ns() / UINT64_C(1000000);
}

static void freak_command_native_stop(freak_command_record *command);
static void freak_command_wait_record(freak_command_record *command);

static void freak_command_cleanup(void) {
    for (size_t index = 0; index < freak_commands_count; index++) {
        freak_command_record *command = &freak_commands[index];
        if (command->in_use && command->child_live) {
            command->status = FREAK_COMMAND_CANCELLED;
            freak_command_native_stop(command);
            freak_command_wait_record(command);
        }
    }
#if defined(FREAK_RUNTIME_OWNERSHIP_AUDIT) || defined(FREAK_C_RUNTIME_OWNERSHIP_AUDIT)
    if (freak_commands_live) {
        fprintf(stderr, "FREAK: ownership audit found %llu live process command(s)\n",
                (unsigned long long)freak_commands_live);
        _Exit(1);
    }
#endif
}

int64_t freak_process_command_new(freak_word executable) {
    char *name = freak_command_copy(executable, false);
    if (!freak_commands_cleanup_registered) {
        if (atexit(freak_command_cleanup) != 0) freak_command_fail("cannot register child cleanup");
        freak_commands_cleanup_registered = true;
    }
    size_t slot = 0;
    while (slot < freak_commands_count && (freak_commands[slot].in_use ||
            freak_commands[slot].generation == FREAK_COMMAND_GENERATION_MAX)) slot++;
    if (slot == freak_commands_count) {
        if (slot >= UINT32_MAX - 1) freak_command_fail("command ticket table exhausted");
        if (slot == freak_commands_capacity) {
            size_t capacity = freak_commands_capacity ? freak_commands_capacity * 2 : 16;
            if (capacity < freak_commands_capacity || capacity > SIZE_MAX / sizeof(*freak_commands))
                freak_command_fail("command table size overflow");
            freak_command_record *grown = realloc(freak_commands, capacity * sizeof(*grown));
            if (!grown) freak_command_fail("out of memory growing command table");
            memset(grown + freak_commands_capacity, 0,
                    (capacity - freak_commands_capacity) * sizeof(*grown));
            freak_commands = grown;
            freak_commands_capacity = capacity;
        }
        freak_commands_count++;
    }
    freak_command_record *command = &freak_commands[slot];
    uint32_t generation = command->generation + 1;
    memset(command, 0, sizeof(*command));
    command->generation = generation;
    command->in_use = true;
    command->exit_code = -1;
    command->argv_capacity = 4;
    command->argv = freak_command_allocate(command->argv_capacity, sizeof(char *));
    command->argv[0] = name;
    command->argc = 1;
#ifndef _WIN32
    command->stdout_read = command->stderr_read = -1;
#endif
    freak_commands_live++;
    return (int64_t)(FREAK_COMMAND_DOMAIN | ((uint64_t)generation << 32) | (slot + 1));
}

void freak_process_command_arg(int64_t ticket, freak_word argument) {
    freak_command_record *command = freak_command_require(ticket);
    freak_command_configurable(command);
    if (command->argc >= 65535) freak_command_fail("too many command arguments");
    if (command->argc + 1 == command->argv_capacity) {
        size_t capacity = command->argv_capacity * 2;
        char **grown = realloc(command->argv, capacity * sizeof(char *));
        if (!grown) freak_command_fail("out of memory growing argument vector");
        command->argv = grown;
        command->argv_capacity = capacity;
    }
    command->argv[command->argc++] = freak_command_copy(argument, true);
    command->argv[command->argc] = NULL;
}

void freak_process_command_cwd(int64_t ticket, freak_word directory) {
    freak_command_record *command = freak_command_require(ticket);
    freak_command_configurable(command);
    char *copy = freak_command_copy(directory, false);
    free(command->cwd);
    command->cwd = copy;
}

static void freak_command_override(int64_t ticket, freak_word name, const freak_word *value) {
    freak_command_record *command = freak_command_require(ticket);
    freak_command_configurable(command);
    char *key = freak_command_copy(name, false);
    char *text = value ? freak_command_copy(*value, true) : NULL;
    if (strchr(key, '=')) freak_command_fail("environment name contains '='");
    for (size_t index = 0; index < command->env_count; index++) {
#ifdef _WIN32
        wchar_t *old_name = freak_command_wide(command->env_names[index]);
        wchar_t *new_name = freak_command_wide(key);
        bool same = CompareStringOrdinal(old_name, -1, new_name, -1, TRUE) == CSTR_EQUAL;
        free(old_name); free(new_name);
#else
        bool same = strcmp(command->env_names[index], key) == 0;
#endif
        if (same) {
            free(key);
            free(command->env_values[index]);
            command->env_values[index] = text;
            return;
        }
    }
    if (command->env_count >= 65535) freak_command_fail("too many environment overrides");
    size_t count = command->env_count + 1;
    char **names = realloc(command->env_names, count * sizeof(char *));
    if (!names) freak_command_fail("out of memory growing environment");
    command->env_names = names;
    char **values = realloc(command->env_values, count * sizeof(char *));
    if (!values) freak_command_fail("out of memory growing environment");
    command->env_values = values;
    command->env_names[command->env_count] = key;
    command->env_values[command->env_count++] = text;
}

void freak_process_command_env(int64_t ticket, freak_word name, freak_word value) {
    freak_command_override(ticket, name, &value);
}
void freak_process_command_unset_env(int64_t ticket, freak_word name) {
    freak_command_override(ticket, name, NULL);
}

static void freak_command_set_error(freak_command_record *command, const char *reason) {
    snprintf(command->error, sizeof(command->error), "%s", reason);
}

static void freak_command_capture_append(freak_command_record *command,
        freak_command_capture *capture, const unsigned char *bytes, size_t length) {
    size_t accepted = length;
    if (accepted > capture->limit - capture->length) accepted = capture->limit - capture->length;
    if (accepted) {
        size_t needed = capture->length + accepted;
        if (needed > capture->capacity) {
            size_t capacity = capture->capacity ? capture->capacity : 4096;
            if (capacity > capture->limit) capacity = capture->limit;
            while (capacity < needed) {
                if (capacity > capture->limit / 2) { capacity = capture->limit; break; }
                capacity *= 2;
            }
            unsigned char *grown = realloc(capture->data, capacity);
            if (!grown) freak_command_fail("out of memory capturing child output");
            capture->data = grown;
            capture->capacity = capacity;
        }
        memcpy(capture->data + capture->length, bytes, accepted);
        capture->length += accepted;
    }
    if (accepted != length && (command->status == FREAK_COMMAND_RUNNING ||
            command->status == FREAK_COMMAND_EXITED || command->status == FREAK_COMMAND_SIGNALED)) {
        command->status = FREAK_COMMAND_OUTPUT_LIMIT;
        freak_command_set_error(command, "child output limit exceeded");
        freak_command_native_stop(command);
    }
}

#ifndef _WIN32
extern char **environ;

static void freak_command_close_pipe(int *descriptor) {
    if (*descriptor >= 0) close(*descriptor);
    *descriptor = -1;
}

static bool freak_command_pipe(int descriptors[2]) {
    if (pipe(descriptors) != 0) return false;
    if (fcntl(descriptors[0], F_SETFD, FD_CLOEXEC) < 0 ||
            fcntl(descriptors[1], F_SETFD, FD_CLOEXEC) < 0) {
        int saved = errno;
        close(descriptors[0]); close(descriptors[1]);
        descriptors[0] = descriptors[1] = -1;
        errno = saved;
        return false;
    }
    return true;
}

static char **freak_command_environment(freak_command_record *command) {
    freak_process_environment_acquire();
    size_t count = 0;
    while (environ[count]) count++;
    char **result = freak_command_allocate(count + command->env_count + 1, sizeof(char *));
    size_t used = 0;
    for (size_t index = 0; index < count; index++) {
        bool overridden = false;
        for (size_t key = 0; key < command->env_count; key++) {
            size_t length = strlen(command->env_names[key]);
            if (strncmp(environ[index], command->env_names[key], length) == 0 &&
                    environ[index][length] == '=') { overridden = true; break; }
        }
        if (!overridden) {
            /* Inherited POSIX environment storage can contain arbitrary bytes;
               preserve it without treating it as a new FREAK text argument. */
            size_t length = strlen(environ[index]);
            result[used] = freak_command_allocate(length + 1, 1);
            memcpy(result[used++], environ[index], length + 1);
        }
    }
    freak_process_environment_release();
    for (size_t key = 0; key < command->env_count; key++) {
        if (!command->env_values[key]) continue;
        size_t names = strlen(command->env_names[key]), values = strlen(command->env_values[key]);
        if (values > SIZE_MAX - names - 2) freak_command_fail("environment size overflow");
        char *entry = freak_command_allocate(names + values + 2, 1);
        memcpy(entry, command->env_names[key], names);
        entry[names] = '=';
        memcpy(entry + names + 1, command->env_values[key], values);
        result[used++] = entry;
    }
    return result;
}

static void freak_command_free_environment(char **environment) {
    for (size_t index = 0; environment[index]; index++) free(environment[index]);
    free(environment);
}

static char **freak_command_executables(freak_command_record *command, char **environment) {
    if (strchr(command->argv[0], '/')) {
        char **targets = freak_command_allocate(2, sizeof(char *));
        targets[0] = freak_command_copy(freak_word_lit(command->argv[0]), false);
        return targets;
    }
    const char *path = "/bin:/usr/bin";
    for (size_t index = 0; environment[index]; index++)
        if (strncmp(environment[index], "PATH=", 5) == 0) path = environment[index] + 5;
    size_t count = 1;
    for (const char *cursor = path; *cursor; cursor++) if (*cursor == ':') count++;
    char **targets = freak_command_allocate(count + 1, sizeof(char *));
    const char *cursor = path;
    for (size_t index = 0; index < count; index++) {
        const char *end = strchr(cursor, ':');
        size_t directory = end ? (size_t)(end - cursor) : strlen(cursor);
        size_t name = strlen(command->argv[0]);
        if (directory > SIZE_MAX - name - 2) freak_command_fail("executable search path overflow");
        targets[index] = freak_command_allocate(directory + name + 2, 1);
        if (directory) {
            memcpy(targets[index], cursor, directory);
            targets[index][directory++] = '/';
        }
        memcpy(targets[index] + directory, command->argv[0], name);
        cursor = end ? end + 1 : cursor + strlen(cursor);
    }
    return targets;
}

static void freak_command_native_stop(freak_command_record *command) {
    if (command->child_live) {
        /* The child establishes this group before exec; parent repeats setpgid
           before returning spawn, avoiding a cancellation race. */
        if (kill(-command->pid, SIGKILL) != 0 && errno == ESRCH)
            (void)kill(command->pid, SIGKILL);
    }
}

static bool freak_command_terminal_set(pid_t foreground) {
    sigset_t blocked, previous;
    sigemptyset(&blocked);
    sigaddset(&blocked, SIGTTOU);
    if (sigprocmask(SIG_BLOCK, &blocked, &previous) != 0) return false;
    int result = tcsetpgrp(STDIN_FILENO, foreground);
    int saved = errno;
    (void)sigprocmask(SIG_SETMASK, &previous, NULL);
    errno = saved;
    return result == 0;
}

static void freak_command_terminal_restore(freak_command_record *command) {
    if (command->terminal_owner) {
        if (!freak_command_terminal_set(command->terminal_owner)) {
            command->status = FREAK_COMMAND_IO_ERROR;
            freak_command_set_error(command, "could not restore terminal foreground ownership");
        }
        command->terminal_owner = 0;
    }
}

static void freak_command_drain(freak_command_record *command, int *descriptor,
        freak_command_capture *capture) {
    unsigned char bytes[4096];
    /* Bound each turn so a flooding stdout cannot starve stderr/deadlines. */
    for (int turn = 0; *descriptor >= 0 && turn < 16; turn++) {
        ssize_t count = read(*descriptor, bytes, sizeof(bytes));
        if (count > 0) freak_command_capture_append(command, capture, bytes, (size_t)count);
        else if (count == 0) freak_command_close_pipe(descriptor);
        else if (errno == EINTR) continue;
        else if (errno == EAGAIN || errno == EWOULDBLOCK) break;
        else {
            freak_command_close_pipe(descriptor);
            if (command->status == FREAK_COMMAND_RUNNING) {
                command->status = FREAK_COMMAND_IO_ERROR;
                freak_command_set_error(command, "could not read child output");
                freak_command_native_stop(command);
            }
        }
    }
}

static void freak_command_wait_record(freak_command_record *command) {
    while (command->child_live || command->stdout_read >= 0 || command->stderr_read >= 0) {
        freak_command_drain(command, &command->stdout_read, &command->output);
        freak_command_drain(command, &command->stderr_read, &command->errors);
        if (command->child_live) {
            int status = 0;
            pid_t waited = waitpid(command->pid, &status, WNOHANG);
            if (waited == command->pid) {
                /* Reap the direct child and kill any still-owned descendants,
                   including ones retaining pipe writers after it has exited. */
                (void)kill(-command->pid, SIGKILL);
                command->child_live = false;
                freak_commands_children--;
                if (command->status == FREAK_COMMAND_RUNNING) {
                    if (WIFEXITED(status)) {
                        command->status = FREAK_COMMAND_EXITED;
                        command->exit_code = WEXITSTATUS(status);
                    } else if (WIFSIGNALED(status)) {
                        command->status = FREAK_COMMAND_SIGNALED;
                        command->signal_number = WTERMSIG(status);
                        freak_command_set_error(command, "child terminated by signal");
                    }
                }
                freak_command_terminal_restore(command);
            } else if (waited < 0 && errno != EINTR) {
                command->child_live = false;
                freak_commands_children--;
                command->status = FREAK_COMMAND_IO_ERROR;
                freak_command_set_error(command, "could not reap child process");
                (void)kill(-command->pid, SIGKILL);
                freak_command_terminal_restore(command);
            }
        }
        if (!command->child_live && command->stdout_read < 0 && command->stderr_read < 0) break;
        if (!command->child_live) {
            /* All direct-child output is now in the pipes. Close an inherited
               writer held by a detached daemon instead of waiting forever.
               Drain buffered data in bounded turns before closing. */
            size_t out_before = command->output.length, err_before = command->errors.length;
            freak_command_drain(command, &command->stdout_read, &command->output);
            freak_command_drain(command, &command->stderr_read, &command->errors);
            if (out_before == command->output.length) freak_command_close_pipe(&command->stdout_read);
            if (err_before == command->errors.length) freak_command_close_pipe(&command->stderr_read);
            continue;
        }
        if (command->status == FREAK_COMMAND_RUNNING && command->deadline_ms &&
                freak_command_now_ms() >= command->deadline_ms) {
            command->status = FREAK_COMMAND_TIMED_OUT;
            freak_command_set_error(command, "child process timed out");
            freak_command_native_stop(command);
        }
        struct pollfd descriptors[2] = {
            {command->stdout_read, POLLIN | POLLHUP, 0},
            {command->stderr_read, POLLIN | POLLHUP, 0}
        };
        int delay = 10;
        if (poll(descriptors, 2, delay) < 0 && errno != EINTR) {
            command->status = FREAK_COMMAND_IO_ERROR;
            freak_command_set_error(command, "could not poll child output");
            freak_command_native_stop(command);
            freak_command_close_pipe(&command->stdout_read);
            freak_command_close_pipe(&command->stderr_read);
        }
    }
}

static bool freak_command_posix_spawn(freak_command_record *command) {
    int output[2] = {-1, -1}, errors[2] = {-1, -1}, execution[2] = {-1, -1};
    char **environment = freak_command_environment(command);
    char **executables = freak_command_executables(command, environment);
    if (command->inherited && isatty(STDIN_FILENO)) {
        pid_t owner = tcgetpgrp(STDIN_FILENO);
        if (owner >= 0 && owner != getpgrp()) {
            errno = EPERM;
            goto failed;
        }
        if (owner >= 0) command->terminal_owner = owner;
    }
    if ((!command->inherited && (!freak_command_pipe(output) || !freak_command_pipe(errors))) ||
            !freak_command_pipe(execution)) goto failed;
    if (!command->inherited && (fcntl(output[0], F_SETFL, O_NONBLOCK) < 0 ||
            fcntl(errors[0], F_SETFL, O_NONBLOCK) < 0)) goto failed;
    pid_t pid = fork();
    if (pid < 0) goto failed;
    if (pid == 0) {
        close(execution[0]);
        int failure = 0;
        if (setpgid(0, 0) != 0) failure = errno;
        if (!failure && command->cwd && chdir(command->cwd) != 0) failure = errno;
        if (!failure && command->terminal_owner && !freak_command_terminal_set(getpid())) failure = errno;
        if (!command->inherited) {
            close(output[0]); close(errors[0]);
            if (!failure && (dup2(output[1], STDOUT_FILENO) < 0 ||
                    dup2(errors[1], STDERR_FILENO) < 0)) failure = errno;
            close(output[1]); close(errors[1]);
        }
        if (!failure) {
            /* execve never falls back to /bin/sh on ENOEXEC. All strings and
               PATH candidates are allocated in the parent before fork. */
            int denied = 0;
            for (size_t target = 0; executables[target]; target++) {
                execve(executables[target], command->argv, environment);
                failure = errno;
                if (failure == EACCES) { denied = EACCES; continue; }
                if (failure != ENOENT && failure != ENOTDIR) break;
            }
            if ((failure == ENOENT || failure == ENOTDIR) && denied) failure = denied;
        }
        ssize_t sent;
        do { sent = write(execution[1], &failure, sizeof(failure)); } while (sent < 0 && errno == EINTR);
        _exit(127);
    }
    command->pid = pid;
    command->child_live = true;
    freak_commands_children++;
    (void)setpgid(pid, pid);
    freak_command_close_pipe(&execution[1]);
    freak_command_close_pipe(&output[1]);
    freak_command_close_pipe(&errors[1]);
    command->stdout_read = output[0]; output[0] = -1;
    command->stderr_read = errors[0]; errors[0] = -1;
    /* CLOEXEC makes EOF unambiguous: a successfully launched child may still
       exit 127, whereas exec/chdir errors carry errno through this private pipe. */
    int failure = 0;
    ssize_t received;
    while (true) {
        struct pollfd handshake = {execution[0], POLLIN | POLLHUP, 0};
        int ready = poll(&handshake, 1, 10);
        if (ready > 0) {
            do { received = read(execution[0], &failure, sizeof(failure)); } while (received < 0 && errno == EINTR);
            break;
        }
        if (ready < 0 && errno != EINTR) { received = -1; break; }
        if (command->deadline_ms && freak_command_now_ms() >= command->deadline_ms) {
            command->status = FREAK_COMMAND_TIMED_OUT;
            freak_command_set_error(command, "executable launch timed out");
            freak_command_native_stop(command);
            received = 0;
            break;
        }
    }
    freak_command_close_pipe(&execution[0]);
    freak_command_free_environment(environment);
    freak_command_free_environment(executables);
    if (command->status == FREAK_COMMAND_TIMED_OUT) {
        freak_command_wait_record(command);
        return false;
    }
    if (received != 0) {
        command->status = FREAK_COMMAND_SPAWN_FAILED;
        snprintf(command->error, sizeof(command->error), "could not launch executable: %s",
                received == sizeof(failure) ? strerror(failure) : "exec status pipe failed");
        freak_command_native_stop(command);
        freak_command_wait_record(command);
        return false;
    }
    return true;
failed:
    command->status = FREAK_COMMAND_SPAWN_FAILED;
    snprintf(command->error, sizeof(command->error), "could not create child process: %s", strerror(errno));
    freak_command_free_environment(environment);
    freak_command_free_environment(executables);
    for (int index = 0; index < 2; index++) {
        freak_command_close_pipe(&output[index]);
        freak_command_close_pipe(&errors[index]);
        freak_command_close_pipe(&execution[index]);
    }
    return false;
}

#else
static wchar_t *freak_command_wide(const char *text) {
    size_t length = strlen(text);
    if (length > INT_MAX) freak_command_fail("Windows OS argument is too large");
    int count = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text, (int)length, NULL, 0);
    if (length && count <= 0) freak_command_fail("cannot convert Windows OS argument");
    wchar_t *result = freak_command_allocate((size_t)count + 1, sizeof(wchar_t));
    if (count && MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text, (int)length,
            result, count) != count) freak_command_fail("cannot convert Windows OS argument");
    return result;
}

static wchar_t *freak_command_windows_line(freak_command_record *command) {
    size_t capacity = 1;
    wchar_t **arguments = freak_command_allocate(command->argc, sizeof(wchar_t *));
    for (size_t index = 0; index < command->argc; index++) {
        arguments[index] = freak_command_wide(command->argv[index]);
        size_t length = wcslen(arguments[index]);
        if (length > (SIZE_MAX - capacity - 4) / 2) freak_command_fail("command line size overflow");
        capacity += length * 2 + 4;
    }
    wchar_t *line = freak_command_allocate(capacity, sizeof(wchar_t));
    size_t used = 0;
    for (size_t index = 0; index < command->argc; index++) {
        if (index) line[used++] = L' ';
        line[used++] = L'"';
        const wchar_t *cursor = arguments[index];
        while (*cursor) {
            size_t slashes = 0;
            while (*cursor == L'\\') { slashes++; cursor++; }
            size_t escaped = (*cursor == L'"' || !*cursor) ? slashes * 2 : slashes;
            for (size_t slash = 0; slash < escaped; slash++) line[used++] = L'\\';
            if (*cursor == L'"') line[used++] = L'\\';
            if (*cursor) line[used++] = *cursor++;
        }
        line[used++] = L'"';
        free(arguments[index]);
    }
    free(arguments);
    if (used >= 32767) { free(line); return NULL; }
    return line;
}

static int freak_command_environment_compare(const void *left, const void *right) {
    const wchar_t *a = *(const wchar_t * const *)left, *b = *(const wchar_t * const *)right;
    int order = CompareStringOrdinal(a, -1, b, -1, TRUE);
    return order == CSTR_LESS_THAN ? -1 : order == CSTR_GREATER_THAN ? 1 : 0;
}

static wchar_t *freak_command_windows_environment(freak_command_record *command) {
    freak_process_environment_acquire();
    wchar_t *snapshot = GetEnvironmentStringsW();
    if (!snapshot) { freak_process_environment_release(); return NULL; }
    size_t inherited_count = 0;
    for (wchar_t *entry = snapshot; *entry; entry += wcslen(entry) + 1) inherited_count++;
    wchar_t **entries = freak_command_allocate(inherited_count + command->env_count + 1, sizeof(wchar_t *));
    wchar_t **names = freak_command_allocate(command->env_count, sizeof(wchar_t *));
    for (size_t index = 0; index < command->env_count; index++) names[index] = freak_command_wide(command->env_names[index]);
    size_t count = 0, total = 1;
    for (wchar_t *entry = snapshot; *entry; entry += wcslen(entry) + 1) {
        bool overridden = false;
        for (size_t index = 0; index < command->env_count; index++) {
            size_t size = wcslen(names[index]);
            if (_wcsnicmp(entry, names[index], size) == 0 && entry[size] == L'=') { overridden = true; break; }
        }
        if (!overridden) {
            size_t size = wcslen(entry) + 1;
            entries[count] = freak_command_allocate(size, sizeof(wchar_t));
            memcpy(entries[count++], entry, size * sizeof(wchar_t));
            total += size;
        }
    }
    FreeEnvironmentStringsW(snapshot);
    freak_process_environment_release();
    for (size_t index = 0; index < command->env_count; index++) {
        if (!command->env_values[index]) { free(names[index]); continue; }
        wchar_t *value = freak_command_wide(command->env_values[index]);
        size_t n = wcslen(names[index]), v = wcslen(value);
        entries[count] = freak_command_allocate(n + v + 2, sizeof(wchar_t));
        memcpy(entries[count], names[index], n * sizeof(wchar_t));
        entries[count][n] = L'=';
        memcpy(entries[count] + n + 1, value, (v + 1) * sizeof(wchar_t));
        total += n + v + 2;
        count++;
        free(names[index]); free(value);
    }
    free(names);
    qsort(entries, count, sizeof(wchar_t *), freak_command_environment_compare);
    wchar_t *block = freak_command_allocate(total + 1, sizeof(wchar_t));
    size_t used = 0;
    for (size_t index = 0; index < count; index++) {
        size_t size = wcslen(entries[index]) + 1;
        memcpy(block + used, entries[index], size * sizeof(wchar_t));
        used += size;
        free(entries[index]);
    }
    free(entries);
    return block;
}

static void freak_command_close_handle(HANDLE *handle) {
    if (*handle && *handle != INVALID_HANDLE_VALUE) CloseHandle(*handle);
    *handle = NULL;
}

static void freak_command_native_stop(freak_command_record *command) {
    if (command->child_live && command->job) (void)TerminateJobObject(command->job, 1);
}

static void freak_command_drain(freak_command_record *command, HANDLE *pipe,
        freak_command_capture *capture) {
    unsigned char bytes[4096];
    for (int turn = 0; *pipe && turn < 16; turn++) {
        DWORD available = 0, count = 0;
        if (!PeekNamedPipe(*pipe, NULL, 0, NULL, &available, NULL)) {
            DWORD error = GetLastError();
            freak_command_close_handle(pipe);
            if (error != ERROR_BROKEN_PIPE && command->status == FREAK_COMMAND_RUNNING) {
                command->status = FREAK_COMMAND_IO_ERROR;
                freak_command_set_error(command, "could not inspect child output pipe");
                freak_command_native_stop(command);
            }
            break;
        }
        if (!available) break;
        DWORD wanted = available < sizeof(bytes) ? available : (DWORD)sizeof(bytes);
        if (!ReadFile(*pipe, bytes, wanted, &count, NULL)) {
            DWORD error = GetLastError();
            freak_command_close_handle(pipe);
            if (error != ERROR_BROKEN_PIPE && command->status == FREAK_COMMAND_RUNNING) {
                command->status = FREAK_COMMAND_IO_ERROR;
                freak_command_set_error(command, "could not read child output");
                freak_command_native_stop(command);
            }
            break;
        }
        if (count) freak_command_capture_append(command, capture, bytes, count);
    }
}

static void freak_command_wait_record(freak_command_record *command) {
    while (command->child_live || command->stdout_read || command->stderr_read) {
        freak_command_drain(command, &command->stdout_read, &command->output);
        freak_command_drain(command, &command->stderr_read, &command->errors);
        if (command->child_live) {
            DWORD state = WaitForSingleObject(command->process, 0);
            if (state == WAIT_OBJECT_0) {
                DWORD code = 0;
                if (!GetExitCodeProcess(command->process, &code)) {
                    command->status = FREAK_COMMAND_IO_ERROR;
                    freak_command_set_error(command, "could not read child exit status");
                } else if (command->status == FREAK_COMMAND_RUNNING) {
                    command->status = FREAK_COMMAND_EXITED;
                    command->exit_code = (int64_t)code;
                }
                (void)TerminateJobObject(command->job, 1);
                command->child_live = false;
                freak_commands_children--;
                freak_command_close_handle(&command->process);
                freak_command_close_handle(&command->job);
            } else if (state == WAIT_FAILED) {
                command->status = FREAK_COMMAND_IO_ERROR;
                freak_command_set_error(command, "could not wait for child process");
                freak_command_native_stop(command);
            }
        }
        if (!command->child_live && !command->stdout_read && !command->stderr_read) break;
        if (command->status == FREAK_COMMAND_RUNNING && command->deadline_ms &&
                freak_command_now_ms() >= command->deadline_ms) {
            command->status = FREAK_COMMAND_TIMED_OUT;
            freak_command_set_error(command, "child process timed out");
            freak_command_native_stop(command);
        }
        Sleep(10);
    }
}

static HANDLE freak_command_inherited_handle(DWORD standard) {
    HANDLE source = GetStdHandle(standard), result = NULL;
    if (source && source != INVALID_HANDLE_VALUE && DuplicateHandle(GetCurrentProcess(), source,
            GetCurrentProcess(), &result, 0, TRUE, DUPLICATE_SAME_ACCESS)) return result;
    SECURITY_ATTRIBUTES attributes = {sizeof(attributes), NULL, TRUE};
    return CreateFileW(L"NUL", standard == STD_INPUT_HANDLE ? GENERIC_READ : GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE, &attributes, OPEN_EXISTING, 0, NULL);
}

static bool freak_command_windows_spawn(freak_command_record *command) {
    SECURITY_ATTRIBUTES security = {sizeof(security), NULL, TRUE};
    STARTUPINFOEXW startup;
    PROCESS_INFORMATION child;
    memset(&startup, 0, sizeof(startup)); memset(&child, 0, sizeof(child));
    startup.StartupInfo.cb = sizeof(startup);
    startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
    HANDLE output_write = NULL, error_write = NULL, input = NULL;
    SIZE_T attributes_size = 0;
    bool attributes_initialized = false;
    wchar_t *executable = freak_command_wide(command->argv[0]);
    wchar_t *line = freak_command_windows_line(command);
    wchar_t *cwd = command->cwd ? freak_command_wide(command->cwd) : NULL;
    wchar_t *environment = freak_command_windows_environment(command);
    DWORD failure = ERROR_NOT_ENOUGH_MEMORY;
    if (!line || !environment) goto failed;
    input = freak_command_inherited_handle(STD_INPUT_HANDLE);
    if (!input || input == INVALID_HANDLE_VALUE) goto native_failed;
    if (command->inherited) {
        output_write = freak_command_inherited_handle(STD_OUTPUT_HANDLE);
        error_write = freak_command_inherited_handle(STD_ERROR_HANDLE);
        if (!output_write || output_write == INVALID_HANDLE_VALUE ||
                !error_write || error_write == INVALID_HANDLE_VALUE) goto native_failed;
    } else {
        if (!CreatePipe(&command->stdout_read, &output_write, &security, 0) ||
                !CreatePipe(&command->stderr_read, &error_write, &security, 0) ||
                !SetHandleInformation(command->stdout_read, HANDLE_FLAG_INHERIT, 0) ||
                !SetHandleInformation(command->stderr_read, HANDLE_FLAG_INHERIT, 0)) goto native_failed;
    }
    startup.StartupInfo.hStdInput = input;
    startup.StartupInfo.hStdOutput = output_write;
    startup.StartupInfo.hStdError = error_write;
    InitializeProcThreadAttributeList(NULL, 1, 0, &attributes_size);
    startup.lpAttributeList = freak_command_allocate(attributes_size, 1);
    if (!InitializeProcThreadAttributeList(startup.lpAttributeList, 1, 0, &attributes_size)) goto native_failed;
    attributes_initialized = true;
    HANDLE inherited[3] = {input, output_write, error_write};
    if (!UpdateProcThreadAttribute(startup.lpAttributeList, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
            inherited, sizeof(inherited), NULL, NULL)) goto native_failed;
    command->job = CreateJobObjectW(NULL, NULL);
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION job;
    memset(&job, 0, sizeof(job));
    job.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if (!command->job || !SetInformationJobObject(command->job, JobObjectExtendedLimitInformation,
            &job, sizeof(job))) goto native_failed;
    if (!CreateProcessW(executable, line, NULL, NULL, TRUE,
            CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT | EXTENDED_STARTUPINFO_PRESENT,
            environment, cwd, &startup.StartupInfo, &child)) goto native_failed;
    if (!AssignProcessToJobObject(command->job, child.hProcess) || ResumeThread(child.hThread) == (DWORD)-1) {
        failure = GetLastError();
        TerminateProcess(child.hProcess, 1);
        WaitForSingleObject(child.hProcess, INFINITE);
        CloseHandle(child.hThread); CloseHandle(child.hProcess);
        goto failed;
    }
    CloseHandle(child.hThread);
    command->process = child.hProcess;
    command->child_live = true;
    freak_commands_children++;
    DeleteProcThreadAttributeList(startup.lpAttributeList);
    free(startup.lpAttributeList);
    freak_command_close_handle(&input);
    freak_command_close_handle(&output_write);
    freak_command_close_handle(&error_write);
    free(executable); free(line); free(cwd); free(environment);
    return true;
native_failed:
    failure = GetLastError();
failed:
    if (startup.lpAttributeList) {
        if (attributes_initialized) DeleteProcThreadAttributeList(startup.lpAttributeList);
        free(startup.lpAttributeList);
    }
    freak_command_close_handle(&input);
    freak_command_close_handle(&output_write);
    freak_command_close_handle(&error_write);
    freak_command_close_handle(&command->stdout_read);
    freak_command_close_handle(&command->stderr_read);
    freak_command_close_handle(&command->job);
    free(executable); free(line); free(cwd); free(environment);
    command->status = FREAK_COMMAND_SPAWN_FAILED;
    snprintf(command->error, sizeof(command->error), "could not launch executable (Windows error %lu)",
            (unsigned long)failure);
    return false;
}
#endif

static int64_t freak_command_spawn_mode(int64_t ticket, int64_t timeout_ms,
        int64_t stdout_limit, int64_t stderr_limit, bool inherited) {
    freak_command_record *command = freak_command_require(ticket);
    freak_command_configurable(command);
    if (timeout_ms < 0 || stdout_limit < 0 || stderr_limit < 0 ||
            (uint64_t)stdout_limit > SIZE_MAX || (uint64_t)stderr_limit > SIZE_MAX)
        freak_command_fail("negative or oversized process limit");
    command->output.limit = (size_t)stdout_limit;
    command->errors.limit = (size_t)stderr_limit;
    command->inherited = inherited;
    command->deadline_ms = timeout_ms ? freak_command_now_ms() + (uint64_t)timeout_ms : 0;
    command->status = FREAK_COMMAND_RUNNING;
#ifdef _WIN32
    (void)freak_command_windows_spawn(command);
#else
    (void)freak_command_posix_spawn(command);
#endif
    return command->status;
}

int64_t freak_process_command_spawn(int64_t ticket, int64_t timeout_ms,
        int64_t stdout_limit, int64_t stderr_limit) {
    return freak_command_spawn_mode(ticket, timeout_ms, stdout_limit, stderr_limit, false);
}
int64_t freak_process_command_spawn_inherit(int64_t ticket, int64_t timeout_ms) {
    return freak_command_spawn_mode(ticket, timeout_ms, 0, 0, true);
}
int64_t freak_process_command_wait(int64_t ticket) {
    freak_command_record *command = freak_command_require(ticket);
    freak_command_wait_record(command);
    return command->status;
}
int64_t freak_process_command_run(int64_t ticket, int64_t timeout_ms,
        int64_t stdout_limit, int64_t stderr_limit) {
    freak_process_command_spawn(ticket, timeout_ms, stdout_limit, stderr_limit);
    return freak_process_command_wait(ticket);
}
int64_t freak_process_command_run_inherit(int64_t ticket, int64_t timeout_ms) {
    freak_process_command_spawn_inherit(ticket, timeout_ms);
    return freak_process_command_wait(ticket);
}
void freak_process_command_terminate(int64_t ticket) {
    freak_command_record *command = freak_command_require(ticket);
    if (command->child_live) {
        command->status = FREAK_COMMAND_CANCELLED;
        freak_command_set_error(command, "child process cancelled");
        freak_command_native_stop(command);
        freak_command_wait_record(command);
    }
}
int64_t freak_process_command_status(int64_t ticket) { return freak_command_require(ticket)->status; }
int64_t freak_process_command_exit_code(int64_t ticket) { return freak_command_require(ticket)->exit_code; }
int64_t freak_process_command_signal(int64_t ticket) { return freak_command_require(ticket)->signal_number; }
freak_word freak_process_command_error(int64_t ticket) {
    return freak_word_clone(freak_word_lit(freak_command_require(ticket)->error));
}
static freak_word freak_command_text(freak_command_capture *capture) {
    if (!freak_byte_buffer_utf8_valid(capture->data, capture->length))
        freak_command_fail("captured output is not NUL-free UTF-8; use the bytes getter");
    char *copy = freak_command_allocate(capture->length + 1, 1);
    if (capture->length) memcpy(copy, capture->data, capture->length);
    return freak_word_own(copy, capture->length);
}
freak_word freak_process_command_stdout(int64_t ticket) { return freak_command_text(&freak_command_require(ticket)->output); }
freak_word freak_process_command_stderr(int64_t ticket) { return freak_command_text(&freak_command_require(ticket)->errors); }
static int64_t freak_command_bytes(freak_command_capture *capture) {
    int64_t buffer = freak_byte_buffer_with_capacity((int64_t)capture->length);
    freak_byte_buffer_record *record = freak_byte_buffer_require(buffer, "process output");
    if (capture->length) memcpy(record->data, capture->data, capture->length);
    record->length = capture->length;
    return buffer;
}
int64_t freak_process_command_stdout_bytes(int64_t ticket) { return freak_command_bytes(&freak_command_require(ticket)->output); }
int64_t freak_process_command_stderr_bytes(int64_t ticket) { return freak_command_bytes(&freak_command_require(ticket)->errors); }
void freak_process_command_release(int64_t ticket) {
    freak_command_record *command = freak_command_require(ticket);
    freak_process_command_terminate(ticket);
    for (size_t index = 0; index < command->argc; index++) free(command->argv[index]);
    for (size_t index = 0; index < command->env_count; index++) {
        free(command->env_names[index]); free(command->env_values[index]);
    }
    free(command->argv); free(command->cwd);
    free(command->env_names); free(command->env_values);
    free(command->output.data); free(command->errors.data);
    command->argv = NULL; command->cwd = NULL;
    command->env_names = command->env_values = NULL;
    command->output.data = command->errors.data = NULL;
    command->in_use = false;
    freak_commands_live--;
}
int64_t freak_process_command_live(void) { return (int64_t)freak_commands_live; }
int64_t freak_process_command_children(void) { return (int64_t)freak_commands_children; }
int64_t freak_process_command_retained_bytes(void) {
    uint64_t total = 0;
    for (size_t index = 0; index < freak_commands_count; index++) {
        freak_command_record *command = &freak_commands[index];
        if (!command->in_use) continue;
        total += command->output.capacity + command->errors.capacity;
        total += command->argv_capacity * sizeof(char *) + command->env_count * 2 * sizeof(char *);
        for (size_t arg = 0; arg < command->argc; arg++) total += strlen(command->argv[arg]) + 1;
        for (size_t env = 0; env < command->env_count; env++)
            total += strlen(command->env_names[env]) +
                     (command->env_values[env] ? strlen(command->env_values[env]) : 0) + 2;
        if (command->cwd) total += strlen(command->cwd) + 1;
    }
    if (total > INT64_MAX) freak_command_fail("retained byte count overflow");
    return (int64_t)total;
}
