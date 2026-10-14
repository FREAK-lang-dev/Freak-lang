/* Opt-in, bounded process-local handle observations. Process information class
   51 is PROCESS_HANDLE_SNAPSHOT_INFORMATION with PROCESS_HANDLE_TABLE_ENTRY_INFO
   entries (Windows 8+). The native ABI is pinned below. A handle value can be
   reused: these are table identities, not proof of kernel-object continuity.
   Object information class 2 queries only the type. Never query object names:
   a name query on a pipe can block. No handles are duplicated or opened here.
   Fixed storage and deferred output avoid allocating/printing before the cold
   entry snapshot. Ordinary probe runs never enter this code's native queries. */
#define PROBE_HANDLE_LIMIT 512
#define PROBE_SNAPSHOT_LIMIT 24
typedef struct {
    HANDLE value;
    ULONG_PTR handle_count, pointer_count;
    ACCESS_MASK access;
    ULONG type_index, attributes, reserved;
} probe_handle_entry;
typedef struct {
    ULONG_PTR count, reserved;
    probe_handle_entry entries[PROBE_HANDLE_LIMIT];
} probe_handle_table;
_Static_assert(offsetof(probe_handle_entry,access)==3*sizeof(ULONG_PTR),"process handle access ABI");
_Static_assert(sizeof(probe_handle_entry)==3*sizeof(ULONG_PTR)+4*sizeof(ULONG),"process handle entry ABI");
_Static_assert(offsetof(probe_handle_table,entries)==2*sizeof(ULONG_PTR),"process handle table ABI");
typedef LONG (NTAPI *probe_process_information_fn)(HANDLE,ULONG,PVOID,ULONG,PULONG);
typedef LONG (NTAPI *probe_object_information_fn)(HANDLE,ULONG,PVOID,ULONG,PULONG);
typedef struct {
    LONG status;
    int known;
    char name[256];
} probe_handle_type;
typedef struct {
    const char *phase;
    const char *native_phase, *owner_context;
    size_t trace_events_seen;
    LONG status;
    ULONG bytes;
    long before, after_query, after_types;
    int complete;
    probe_handle_table table;
    probe_handle_type types[PROBE_HANDLE_LIMIT];
} probe_handle_capture;
static probe_handle_capture probe_handle_captures[PROBE_SNAPSHOT_LIMIT];
static size_t probe_handle_capture_count;
static int probe_handle_capture_overflow;

static void probe_handle_snapshot(const char *phase) {
    if (!probe_handle_diagnostics) return;
    DWORD original_error=GetLastError();
    if (probe_handle_capture_count==PROBE_SNAPSHOT_LIMIT) {
        probe_handle_capture_overflow=1; SetLastError(original_error); return;
    }
    probe_handle_capture *capture=&probe_handle_captures[probe_handle_capture_count++];
    capture->phase=phase; capture->before=probe_process_count();
    capture->native_phase=probe_phase; capture->owner_context=probe_owner;
    capture->trace_events_seen=probe_event_count;
    HMODULE native=GetModuleHandleW(L"ntdll.dll");
    probe_process_information_fn query=native ? (probe_process_information_fn)(void *)
        GetProcAddress(native,"NtQueryInformationProcess") : NULL;
    probe_object_information_fn object=native ? (probe_object_information_fn)(void *)
        GetProcAddress(native,"NtQueryObject") : NULL;
    capture->status=query ? query(GetCurrentProcess(),51,&capture->table,sizeof(capture->table),&capture->bytes) : INT32_MIN;
    capture->after_query=probe_process_count();
    capture->complete=capture->status==0 && capture->bytes>=offsetof(probe_handle_table,entries) &&
        capture->bytes<=sizeof(capture->table) && capture->table.count<=PROBE_HANDLE_LIMIT &&
        capture->table.count<=(capture->bytes- offsetof(probe_handle_table,entries))/sizeof(probe_handle_entry);
    if (capture->complete) for (size_t i=0;i<capture->table.count;i++) {
        probe_handle_type *type=&capture->types[i];
        union { ULONG_PTR aligned; unsigned char bytes[4096]; } storage;
        ULONG bytes=0;
        type->status=object ? object(capture->table.entries[i].value,2,storage.bytes,sizeof(storage.bytes),&bytes) : INT32_MIN;
        if (type->status!=0 || bytes<sizeof(UNICODE_STRING) || bytes>sizeof(storage.bytes)) continue;
        UNICODE_STRING name; memcpy(&name,storage.bytes,sizeof(name));
        uintptr_t base=(uintptr_t)storage.bytes,position=(uintptr_t)name.Buffer;
        if (!name.Length || name.Length%sizeof(WCHAR) || position<base || position-base>bytes ||
            name.Length>bytes-(position-base) || position%_Alignof(WCHAR)) continue;
        int count=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,name.Buffer,name.Length/sizeof(WCHAR),
                                     type->name,sizeof(type->name)-1,NULL,NULL);
        if (count>0) { type->name[count]=0; type->known=1; }
    }
    capture->after_types=probe_process_count(); SetLastError(original_error);
}
static void probe_handle_dump(void) {
    if (!probe_handle_diagnostics) return;
    int complete=!probe_handle_capture_overflow, all_types=1;
    for (size_t i=0;i<probe_handle_capture_count;i++) {
        const probe_handle_capture *capture=&probe_handle_captures[i];
        complete &= capture->complete;
        printf("{\"type\":\"handle_snapshot\",\"ordinal\":%zu,\"phase\":",i); probe_string(capture->phase);
        printf(",\"native_phase\":"); probe_string(capture->native_phase);
        printf(",\"owner_context\":"); probe_string(capture->owner_context);
        printf(",\"trace_events_seen\":%zu",capture->trace_events_seen);
        printf(",\"process_id\":%lu,\"ntstatus\":%ld,\"returned_bytes\":%lu,\"complete\":%s,\"snapshot_handles\":",
            (unsigned long)GetCurrentProcessId(),(long)capture->status,(unsigned long)capture->bytes,
            capture->complete?"true":"false");
        if (capture->complete) printf("%"PRIu64,(uint64_t)capture->table.count); else printf("null");
        printf(",\"count_before_query\":%ld,\"count_after_query\":%ld,\"count_after_types\":%ld}\n",
            capture->before,capture->after_query,capture->after_types);
        if (!capture->complete) continue;
        for (size_t j=0;j<capture->table.count;j++) {
            const probe_handle_entry *entry=&capture->table.entries[j];
            const probe_handle_type *type=&capture->types[j]; all_types &= type->known;
            printf("{\"type\":\"handle_identity\",\"ordinal\":%zu,\"handle\":%"PRIu64
                   ",\"type_index\":%lu,\"access\":%lu,\"attributes\":%lu,\"handle_count\":%"PRIu64
                   ",\"pointer_count\":%"PRIu64",\"type_ntstatus\":%ld,\"type_known\":%s,\"object_type\":",
                i,(uint64_t)(uintptr_t)entry->value,(unsigned long)entry->type_index,
                (unsigned long)entry->access,(unsigned long)entry->attributes,(uint64_t)entry->handle_count,
                (uint64_t)entry->pointer_count,(long)type->status,type->known?"true":"false");
            if (type->known) probe_string(type->name); else printf("null");
            puts("}");
        }
    }
    printf("{\"type\":\"handle_diagnostic_summary\",\"snapshot_completed\":%s,\"all_types_known\":%s,\"snapshot_overflow\":%s,\"snapshot_count\":%zu,\"handle_limit\":%d,\"snapshot_limit\":%d,\"process_information_class\":51,\"object_information_class\":2,\"object_names_queried\":false,\"handles_opened_or_duplicated_by_snapshot\":false,\"identity_scope\":\"process table handle value/type/access; reuse can hide object replacement\",\"production_result_adjusted\":false,\"profile_mode\":\"%s\"}\n",
        complete?"true":"false",all_types?"true":"false",probe_handle_capture_overflow?"true":"false",
        probe_handle_capture_count,PROBE_HANDLE_LIMIT,PROBE_SNAPSHOT_LIMIT,
        probe_no_privilege_lookup?"profile_no_privilege_lookup":"full");
}
