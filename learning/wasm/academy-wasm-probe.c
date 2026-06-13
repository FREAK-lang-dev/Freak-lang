// Minimal freestanding FREAK Academy WASM probe.
//
// This is not the lesson evaluator. It proves that the repository can produce
// a browser-loadable WASM artifact behind the Academy worker boundary while the
// real compiler-owned implementation is still pending.

#define ACADEMY_WORKER_PROTOCOL_VERSION 1
#define ACADEMY_WASM_PROBE_VERSION 1
#define ACADEMY_SUPPORTED_LESSON_COUNT 0

__attribute__((visibility("default")))
int academy_protocol_version(void) {
    return ACADEMY_WORKER_PROTOCOL_VERSION;
}

__attribute__((visibility("default")))
int academy_wasm_probe_version(void) {
    return ACADEMY_WASM_PROBE_VERSION;
}

__attribute__((visibility("default")))
int academy_supported_lesson_count(void) {
    return ACADEMY_SUPPORTED_LESSON_COUNT;
}
