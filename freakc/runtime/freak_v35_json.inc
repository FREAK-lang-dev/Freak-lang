#ifndef FREAK_V35_JSON_INCLUDED
#define FREAK_V35_JSON_INCLUDED 1
/* Strict, document-owned RFC 8259 JSON. Included after the ByteBuffer runtime.
   Profile: duplicate keys rejected; no BOM; byte offsets; exact numeric text.
   A document is a sequential owner (not a concurrent mutable object). */
#define FREAK_JSON_DOC_DOMAIN UINT64_C(0x6000000000000000)
#define FREAK_JSON_VIEW_DOMAIN UINT64_C(0x4000000000000000)
#define FREAK_JSON_DOMAIN_MASK UINT64_C(0xe000000000000000)
#define FREAK_JSON_GENERATION_MAX UINT32_C(0x1fffffff)
#define FREAK_JSON_INPUT_LIMIT (1024u * 1024u)
#define FREAK_JSON_DEPTH_LIMIT 128u
#define FREAK_JSON_NODE_LIMIT 65536u
#define FREAK_JSON_STRING_LIMIT (256u * 1024u)
#define FREAK_JSON_NUMBER_LIMIT 1024u
#define FREAK_JSON_OUTPUT_LIMIT (8u * 1024u * 1024u)

typedef struct {
    uint32_t child;
    unsigned char *key;
    size_t key_length;
    uint64_t hash;
} freak_json_edge;
typedef struct {
    int kind, boolean;
    uint32_t parent;
    unsigned char *text;
    size_t text_length;
    freak_json_edge *edges;
    size_t count, capacity;
    uint32_t *key_table;
    size_t key_capacity;
} freak_json_node;
typedef struct {
    uint32_t generation, root;
    bool in_use;
    freak_json_node *nodes;
    size_t count, capacity, text_bytes, error_position;
    char error[160];
} freak_json_document;
static freak_json_document *freak_json_documents;
static size_t freak_json_document_slot_count, freak_json_document_capacity;
static uint32_t freak_json_generation;
static size_t freak_json_live_documents, freak_json_live_nodes;
static bool freak_json_cleanup_registered;

static _Noreturn void freak_json_fail(const char *message) {
    fprintf(stderr, "FREAK: JSON document: %s\n", message);
    exit(1);
}
static void *freak_json_allocate(size_t count, size_t width) {
    if (width && count > SIZE_MAX / width) freak_json_fail("allocation overflow");
    void *p = calloc(count ? count : 1, width ? width : 1);
    if (!p) freak_json_fail("out of memory");
    return p;
}
static void freak_json_error(freak_json_document *d, size_t pos, const char *error) {
    if (!d->error[0]) {
        snprintf(d->error, sizeof(d->error), "%s", error);
        d->error_position = pos;
    }
}
static freak_json_document *freak_json_require(int64_t ticket) {
    uint64_t bits = (uint64_t)ticket;
    uint32_t slot = (uint32_t)bits;
    uint32_t generation = (uint32_t)(bits >> 32) & FREAK_JSON_GENERATION_MAX;
    if ((bits & FREAK_JSON_DOMAIN_MASK) != FREAK_JSON_DOC_DOMAIN || !slot ||
            slot > freak_json_document_slot_count) freak_json_fail("invalid or stale document ticket");
    freak_json_document *d = &freak_json_documents[slot - 1];
    if (!d->in_use || d->generation != generation) freak_json_fail("invalid or stale document ticket");
    return d;
}
static uint32_t freak_json_index(freak_json_document *d, int64_t view) {
    uint64_t bits = (uint64_t)view;
    uint32_t index = (uint32_t)bits;
    if ((bits & FREAK_JSON_DOMAIN_MASK) != FREAK_JSON_VIEW_DOMAIN || !index ||
            index > d->count || ((bits >> 32) & FREAK_JSON_GENERATION_MAX) != d->generation)
        freak_json_fail("invalid, foreign, or stale node view");
    return index;
}
static int64_t freak_json_view(freak_json_document *d, uint32_t index) {
    if (!index) return 0;
    return (int64_t)(FREAK_JSON_VIEW_DOMAIN | ((uint64_t)d->generation << 32) | index);
}
static freak_json_node *freak_json_typed(freak_json_document *d, int64_t view, int kind) {
    freak_json_node *n = &d->nodes[freak_json_index(d, view) - 1];
    if (n->kind != kind) freak_json_fail("node has the wrong type");
    return n;
}
static void freak_json_dispose(freak_json_document *d) {
    for (size_t i = 0; i < d->count; i++) {
        freak_json_node *n = &d->nodes[i];
        free(n->text);
        for (size_t j = 0; j < n->count; j++) free(n->edges[j].key);
        free(n->edges); free(n->key_table);
    }
    free(d->nodes);
    freak_json_live_nodes -= d->count;
    freak_json_live_documents--;
    uint32_t generation = d->generation;
    memset(d, 0, sizeof(*d)); d->generation = generation;
}
static void freak_json_cleanup(void) {
#if defined(FREAK_RUNTIME_OWNERSHIP_AUDIT) || defined(FREAK_C_RUNTIME_OWNERSHIP_AUDIT)
    if (freak_json_live_documents) {
        fprintf(stderr, "FREAK: ownership audit found %llu live JSON document(s)\n",
                (unsigned long long)freak_json_live_documents);
        _Exit(1);
    }
#endif
    for (size_t i = 0; i < freak_json_document_slot_count; i++)
        if (freak_json_documents[i].in_use) freak_json_dispose(&freak_json_documents[i]);
    free(freak_json_documents);
}
int64_t freak_json_document_new(void) {
    if (freak_json_generation == FREAK_JSON_GENERATION_MAX) freak_json_fail("document generations exhausted");
    if (!freak_json_cleanup_registered) {
        if (atexit(freak_json_cleanup)) freak_json_fail("cannot register cleanup");
        freak_json_cleanup_registered = true;
    }
    size_t slot = 0;
    while (slot < freak_json_document_slot_count && freak_json_documents[slot].in_use) slot++;
    if (slot == freak_json_document_slot_count) {
        if (slot >= UINT32_MAX - 1) freak_json_fail("document table exhausted");
        if (slot == freak_json_document_capacity) {
            size_t cap = freak_json_document_capacity ? freak_json_document_capacity * 2 : 16;
            if (cap > SIZE_MAX / sizeof(*freak_json_documents)) freak_json_fail("document table overflow");
            freak_json_document *grown = realloc(freak_json_documents, cap * sizeof(*grown));
            if (!grown) freak_json_fail("out of memory growing document table");
            memset(grown + freak_json_document_capacity, 0,
                    (cap - freak_json_document_capacity) * sizeof(*grown));
            freak_json_documents = grown; freak_json_document_capacity = cap;
        }
        freak_json_document_slot_count++;
    }
    freak_json_document *d = &freak_json_documents[slot];
    memset(d, 0, sizeof(*d)); d->in_use = true; d->generation = ++freak_json_generation;
    freak_json_live_documents++;
    return (int64_t)(FREAK_JSON_DOC_DOMAIN | ((uint64_t)d->generation << 32) | (slot + 1));
}
void freak_json_document_release(int64_t doc) { freak_json_dispose(freak_json_require(doc)); }
int64_t freak_json_document_ok(int64_t doc) { return !freak_json_require(doc)->error[0]; }
int64_t freak_json_document_error_position(int64_t doc) { return (int64_t)freak_json_require(doc)->error_position; }
freak_word freak_json_document_error(int64_t doc) { return freak_word_clone(freak_word_lit(freak_json_require(doc)->error)); }
int64_t freak_json_document_root(int64_t doc) {
    freak_json_document *d = freak_json_require(doc); return freak_json_view(d, d->root);
}
static uint32_t freak_json_add_node(freak_json_document *d, int kind, size_t pos) {
    if (d->error[0]) return 0;
    if (d->count == FREAK_JSON_NODE_LIMIT) { freak_json_error(d, pos, "node limit exceeded"); return 0; }
    if (d->count == d->capacity) {
        size_t cap = d->capacity ? d->capacity * 2 : 16;
        freak_json_node *grown = realloc(d->nodes, cap * sizeof(*grown));
        if (!grown) freak_json_fail("out of memory growing nodes");
        memset(grown + d->capacity, 0, (cap - d->capacity) * sizeof(*grown));
        d->nodes = grown; d->capacity = cap;
    }
    uint32_t index = (uint32_t)++d->count;
    d->nodes[index - 1].kind = kind; freak_json_live_nodes++; return index;
}
static bool freak_json_text_budget(freak_json_document *d, size_t length, size_t limit, size_t pos) {
    if (length > limit) { freak_json_error(d, pos, "string or number size limit exceeded"); return false; }
    if (length > FREAK_JSON_INPUT_LIMIT - d->text_bytes) {
        freak_json_error(d, pos, "document text budget exceeded"); return false;
    }
    d->text_bytes += length; return true;
}
static unsigned char *freak_json_copy(const unsigned char *data, size_t length) {
    unsigned char *copy = freak_json_allocate(length + 1, 1);
    if (length) memcpy(copy, data, length); return copy;
}
static uint64_t freak_json_hash(const unsigned char *data, size_t length) {
    uint64_t h = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < length; i++) h = (h ^ data[i]) * UINT64_C(1099511628211);
    return h;
}
static size_t freak_json_key_find(freak_json_node *n, const unsigned char *key, size_t length, uint64_t hash) {
    if (!n->key_capacity) return SIZE_MAX;
    size_t slot = (size_t)hash & (n->key_capacity - 1);
    while (n->key_table[slot]) {
        size_t index = n->key_table[slot] - 1;
        freak_json_edge *e = &n->edges[index];
        if (e->hash == hash && e->key_length == length && (!length || !memcmp(e->key, key, length))) return index;
        slot = (slot + 1) & (n->key_capacity - 1);
    }
    return SIZE_MAX;
}
static void freak_json_key_grow(freak_json_node *n) {
    size_t cap = n->key_capacity ? n->key_capacity * 2 : 16;
    uint32_t *table = freak_json_allocate(cap, sizeof(*table));
    for (size_t i = 0; i < n->count; i++) {
        size_t slot = (size_t)n->edges[i].hash & (cap - 1);
        while (table[slot]) slot = (slot + 1) & (cap - 1);
        table[slot] = (uint32_t)i + 1;
    }
    free(n->key_table); n->key_table = table; n->key_capacity = cap;
}
static bool freak_json_attach(freak_json_document *d, uint32_t parent, uint32_t child,
        unsigned char *key, size_t length, size_t pos) {
    freak_json_node *n = &d->nodes[parent - 1];
    uint64_t hash = freak_json_hash(key, length);
    if (n->kind == 6 && freak_json_key_find(n, key, length, hash) != SIZE_MAX) {
        free(key); freak_json_error(d, pos, "duplicate object key"); return false;
    }
    if (n->count == n->capacity) {
        size_t cap = n->capacity ? n->capacity * 2 : 8;
        freak_json_edge *grown = realloc(n->edges, cap * sizeof(*grown));
        if (!grown) freak_json_fail("out of memory growing child list");
        n->edges = grown; n->capacity = cap;
    }
    if (n->kind == 6 && (!n->key_capacity || (n->count + 1) * 2 >= n->key_capacity)) freak_json_key_grow(n);
    size_t index = n->count++;
    n->edges[index] = (freak_json_edge){child, key, length, hash};
    if (n->kind == 6) {
        size_t slot = (size_t)hash & (n->key_capacity - 1);
        while (n->key_table[slot]) slot = (slot + 1) & (n->key_capacity - 1);
        n->key_table[slot] = (uint32_t)index + 1;
    }
    d->nodes[child - 1].parent = parent; return true;
}
/* Parser state is stack-local, never shared between documents. */
typedef struct { freak_json_document *doc; const unsigned char *data; size_t length, pos; } freak_json_parser;
static void freak_json_space(freak_json_parser *p) {
    while (p->pos < p->length && (p->data[p->pos] == ' ' || p->data[p->pos] == '\t' ||
            p->data[p->pos] == '\n' || p->data[p->pos] == '\r')) p->pos++;
}
static int freak_json_hex(unsigned char ch) {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
    return -1;
}
static bool freak_json_hex4(freak_json_parser *p, uint32_t *code) {
    if (p->length - p->pos < 4) { freak_json_error(p->doc, p->pos, "incomplete Unicode escape"); return false; }
    *code = 0;
    for (size_t i = 0; i < 4; i++) {
        int digit = freak_json_hex(p->data[p->pos]);
        if (digit < 0) { freak_json_error(p->doc, p->pos, "invalid Unicode escape"); return false; }
        *code = (*code << 4) | (unsigned)digit; p->pos++;
    }
    return true;
}
static unsigned char *freak_json_parse_string(freak_json_parser *p, size_t *length) {
    size_t start = p->pos++;
    size_t cap = p->length - p->pos;
    if (cap > FREAK_JSON_STRING_LIMIT) cap = FREAK_JSON_STRING_LIMIT;
    unsigned char *text = freak_json_allocate(cap + 1, 1);
    size_t used = 0;
    while (p->pos < p->length) {
        size_t char_pos = p->pos;
        unsigned char ch = p->data[p->pos++];
        if (ch == '"') {
            if (!freak_system_utf8_valid((const char *)text, used)) {
                freak_json_error(p->doc, start, "string is not valid UTF-8"); break;
            }
            if (!freak_json_text_budget(p->doc, used, FREAK_JSON_STRING_LIMIT, start)) break;
            *length = used; return text;
        }
        if (ch < 0x20) { freak_json_error(p->doc, char_pos, "unescaped control byte in string"); break; }
        unsigned char encoded[4]; size_t n = 1; encoded[0] = ch;
        if (ch == '\\') {
            if (p->pos == p->length) { freak_json_error(p->doc, p->pos, "incomplete escape"); break; }
            ch = p->data[p->pos++];
            switch (ch) {
                case '"': case '\\': case '/': encoded[0] = ch; break;
                case 'b': encoded[0] = '\b'; break;
                case 'f': encoded[0] = '\f'; break;
                case 'n': encoded[0] = '\n'; break;
                case 'r': encoded[0] = '\r'; break;
                case 't': encoded[0] = '\t'; break;
                case 'u': {
                    uint32_t code;
                    if (!freak_json_hex4(p, &code)) goto failed;
                    if (code >= 0xd800 && code <= 0xdbff) {
                        if (p->length - p->pos < 2 || p->data[p->pos] != '\\' || p->data[p->pos + 1] != 'u') {
                            freak_json_error(p->doc, p->pos, "high surrogate needs a paired low surrogate"); goto failed;
                        }
                        p->pos += 2; uint32_t low;
                        if (!freak_json_hex4(p, &low)) goto failed;
                        if (low < 0xdc00 || low > 0xdfff) {
                            freak_json_error(p->doc, p->pos - 4, "invalid paired low surrogate"); goto failed;
                        }
                        code = 0x10000 + ((code - 0xd800) << 10) + low - 0xdc00;
                    } else if (code >= 0xdc00 && code <= 0xdfff) {
                        freak_json_error(p->doc, p->pos - 4, "unpaired low surrogate"); goto failed;
                    }
                    if (code < 0x80) encoded[0] = (unsigned char)code;
                    else if (code < 0x800) { n = 2; encoded[0] = 0xc0 | (code >> 6); encoded[1] = 0x80 | (code & 63); }
                    else if (code < 0x10000) { n = 3; encoded[0] = 0xe0 | (code >> 12); encoded[1] = 0x80 | ((code >> 6) & 63); encoded[2] = 0x80 | (code & 63); }
                    else { n = 4; encoded[0] = 0xf0 | (code >> 18); encoded[1] = 0x80 | ((code >> 12) & 63); encoded[2] = 0x80 | ((code >> 6) & 63); encoded[3] = 0x80 | (code & 63); }
                    break;
                }
                default: freak_json_error(p->doc, p->pos - 1, "invalid string escape"); goto failed;
            }
        }
        if (n > cap - used) { freak_json_error(p->doc, char_pos, "string size limit exceeded"); break; }
        memcpy(text + used, encoded, n); used += n;
    }
    if (!p->doc->error[0]) freak_json_error(p->doc, p->pos, "unterminated string");
failed:
    free(text); return NULL;
}
static bool freak_json_digit(unsigned char ch) { return ch >= '0' && ch <= '9'; }
static size_t freak_json_number_end(const unsigned char *data, size_t length, size_t start) {
    size_t i = start;
    if (i < length && data[i] == '-') i++;
    if (i == length) return start;
    if (data[i] == '0') i++;
    else if (data[i] >= '1' && data[i] <= '9') { do i++; while (i < length && freak_json_digit(data[i])); }
    else return start;
    if (i < length && data[i] == '.') {
        i++; size_t digits = i;
        while (i < length && freak_json_digit(data[i])) i++;
        if (i == digits) return start;
    }
    if (i < length && (data[i] == 'e' || data[i] == 'E')) {
        i++; if (i < length && (data[i] == '+' || data[i] == '-')) i++;
        size_t digits = i; while (i < length && freak_json_digit(data[i])) i++;
        if (i == digits) return start;
    }
    return i;
}
static uint32_t freak_json_parse_value(freak_json_parser *p, unsigned depth) {
    if (depth > FREAK_JSON_DEPTH_LIMIT) { freak_json_error(p->doc, p->pos, "nesting depth limit exceeded"); return 0; }
    freak_json_space(p); size_t start = p->pos;
    if (start == p->length) { freak_json_error(p->doc, start, "expected JSON value"); return 0; }
    unsigned char ch = p->data[p->pos];
    if (ch == '"') {
        size_t length; unsigned char *text = freak_json_parse_string(p, &length);
        if (!text) return 0;
        uint32_t index = freak_json_add_node(p->doc, 4, start);
        if (!index) { free(text); return 0; }
        p->doc->nodes[index - 1].text = text; p->doc->nodes[index - 1].text_length = length; return index;
    }
    if (ch == '[' || ch == '{') {
        int kind = ch == '[' ? 5 : 6; unsigned char close = ch == '[' ? ']' : '}';
        uint32_t index = freak_json_add_node(p->doc, kind, start); if (!index) return 0;
        p->pos++; freak_json_space(p);
        if (p->pos < p->length && p->data[p->pos] == close) { p->pos++; return index; }
        for (;;) {
            unsigned char *key = NULL; size_t key_length = 0, key_pos = p->pos;
            if (kind == 6) {
                if (p->pos == p->length || p->data[p->pos] != '"') {
                    freak_json_error(p->doc, p->pos, "expected quoted object key"); return 0;
                }
                key = freak_json_parse_string(p, &key_length); if (!key) return 0;
                freak_json_space(p);
                if (p->pos == p->length || p->data[p->pos] != ':') {
                    free(key); freak_json_error(p->doc, p->pos, "expected colon after object key"); return 0;
                }
                p->pos++;
            }
            uint32_t child = freak_json_parse_value(p, depth + 1);
            if (!child) { free(key); return 0; }
            if (!freak_json_attach(p->doc, index, child, key, key_length, key_pos)) return 0;
            freak_json_space(p);
            if (p->pos == p->length) { freak_json_error(p->doc, p->pos, "unterminated container"); return 0; }
            if (p->data[p->pos] == close) { p->pos++; return index; }
            if (p->data[p->pos] != ',') { freak_json_error(p->doc, p->pos, "expected comma or container end"); return 0; }
            p->pos++; freak_json_space(p);
        }
    }
    const char *literal = ch == 'n' ? "null" : ch == 't' ? "true" : ch == 'f' ? "false" : NULL;
    if (literal) {
        size_t length = strlen(literal);
        if (p->length - p->pos < length || memcmp(p->data + p->pos, literal, length)) {
            freak_json_error(p->doc, p->pos, "invalid JSON literal"); return 0;
        }
        p->pos += length; uint32_t index = freak_json_add_node(p->doc, ch == 'n' ? 1 : 2, start);
        if (index) p->doc->nodes[index - 1].boolean = ch == 't'; return index;
    }
    if (ch == '-' || freak_json_digit(ch)) {
        size_t end = freak_json_number_end(p->data, p->length, start);
        if (end == start) { freak_json_error(p->doc, start, "invalid JSON number grammar"); return 0; }
        if (!freak_json_text_budget(p->doc, end - start, FREAK_JSON_NUMBER_LIMIT, start)) return 0;
        uint32_t index = freak_json_add_node(p->doc, 3, start); if (!index) return 0;
        p->doc->nodes[index - 1].text = freak_json_copy(p->data + start, end - start);
        p->doc->nodes[index - 1].text_length = end - start; p->pos = end; return index;
    }
    freak_json_error(p->doc, start, "expected JSON value"); return 0;
}
static int64_t freak_json_parse(const unsigned char *data, size_t length) {
    int64_t ticket = freak_json_document_new(); freak_json_document *d = freak_json_require(ticket);
    if (length > FREAK_JSON_INPUT_LIMIT) { freak_json_error(d, 0, "input size limit exceeded"); return ticket; }
    if (length && !data) freak_json_fail("invalid input storage");
    freak_json_parser parser = {d, data, length, 0};
    uint32_t root = freak_json_parse_value(&parser, 1); freak_json_space(&parser);
    if (!d->error[0] && parser.pos != length) freak_json_error(d, parser.pos, "trailing junk after JSON value");
    if (!d->error[0]) d->root = root; return ticket;
}
int64_t freak_json_document_parse(freak_word source) { return freak_json_parse((const unsigned char *)source.data, source.length); }
int64_t freak_json_document_parse_bytes(int64_t bytes) {
    freak_byte_buffer_record *b = freak_byte_buffer_require(bytes, "JSON parse");
    return freak_json_parse(b->data, b->length);
}
int64_t freak_json_document_kind(int64_t doc, int64_t node) {
    freak_json_document *d = freak_json_require(doc);
    return node ? d->nodes[freak_json_index(d, node) - 1].kind : 0;
}
int64_t freak_json_document_count(int64_t doc, int64_t node) {
    freak_json_document *d = freak_json_require(doc); freak_json_node *n = &d->nodes[freak_json_index(d, node) - 1];
    if (n->kind != 5 && n->kind != 6) freak_json_fail("count requires array or object"); return (int64_t)n->count;
}
int64_t freak_json_document_array_get(int64_t doc, int64_t node, int64_t index) {
    freak_json_document *d = freak_json_require(doc); freak_json_node *n = freak_json_typed(d, node, 5);
    if (index < 0 || (uint64_t)index >= n->count) return 0; return freak_json_view(d, n->edges[index].child);
}
int64_t freak_json_document_object_get(int64_t doc, int64_t node, freak_word key) {
    freak_json_document *d = freak_json_require(doc); freak_json_node *n = freak_json_typed(d, node, 6);
    size_t i = freak_json_key_find(n, (const unsigned char *)key.data, key.length, freak_json_hash((const unsigned char *)key.data, key.length));
    return i == SIZE_MAX ? 0 : freak_json_view(d, n->edges[i].child);
}
int64_t freak_json_document_object_get_bytes(int64_t doc, int64_t node, int64_t key) {
    freak_byte_buffer_record *b = freak_byte_buffer_require(key, "JSON object lookup");
    freak_word view = {(char *)b->data, b->length, b->length, false};
    return freak_json_document_object_get(doc, node, view);
}
static int64_t freak_json_bytes(const unsigned char *data, size_t length) {
    int64_t ticket = freak_byte_buffer_with_capacity((int64_t)length);
    freak_byte_buffer_record *b = freak_byte_buffer_require(ticket, "JSON output");
    if (length) memcpy(b->data, data, length); b->length = length; return ticket;
}
int64_t freak_json_document_object_key_bytes(int64_t doc, int64_t node, int64_t index) {
    freak_json_document *d = freak_json_require(doc); freak_json_node *n = freak_json_typed(d, node, 6);
    if (index < 0 || (uint64_t)index >= n->count) freak_json_fail("object key index is out of bounds");
    return freak_json_bytes(n->edges[index].key, n->edges[index].key_length);
}
int64_t freak_json_document_bool_value(int64_t doc, int64_t node) { return freak_json_typed(freak_json_require(doc), node, 2)->boolean; }
static freak_word freak_json_text_word(freak_json_node *n) {
    if (n->text_length && memchr(n->text, 0, n->text_length)) freak_json_fail("NUL-containing string requires string_bytes");
    return freak_word_own((char *)freak_json_copy(n->text, n->text_length), n->text_length);
}
freak_word freak_json_document_number_text(int64_t doc, int64_t node) { return freak_json_text_word(freak_json_typed(freak_json_require(doc), node, 3)); }
freak_word freak_json_document_string_word(int64_t doc, int64_t node) { return freak_json_text_word(freak_json_typed(freak_json_require(doc), node, 4)); }
int64_t freak_json_document_string_bytes(int64_t doc, int64_t node) {
    freak_json_node *n = freak_json_typed(freak_json_require(doc), node, 4); return freak_json_bytes(n->text, n->text_length);
}
int64_t freak_json_document_make_null(int64_t doc) { freak_json_document *d = freak_json_require(doc); return freak_json_view(d, freak_json_add_node(d, 1, 0)); }
int64_t freak_json_document_make_bool(int64_t doc, int64_t value) {
    freak_json_document *d = freak_json_require(doc);
    if (value != 0 && value != 1) { freak_json_error(d, 0, "boolean constructor requires zero or one"); return 0; }
    uint32_t index = freak_json_add_node(d, 2, 0); if (index) d->nodes[index - 1].boolean = (int)value; return freak_json_view(d, index);
}
static int64_t freak_json_make_text(int64_t doc, const unsigned char *data, size_t length, int kind) {
    freak_json_document *d = freak_json_require(doc); if (d->error[0]) return 0;
    if (kind == 3 && (!length || freak_json_number_end(data, length, 0) != length)) {
        freak_json_error(d, 0, "invalid JSON number grammar"); return 0;
    }
    if (kind == 4 && !freak_system_utf8_valid((const char *)data, length)) {
        freak_json_error(d, 0, "string is not valid UTF-8"); return 0;
    }
    if (!freak_json_text_budget(d, length, kind == 3 ? FREAK_JSON_NUMBER_LIMIT : FREAK_JSON_STRING_LIMIT, 0)) return 0;
    uint32_t index = freak_json_add_node(d, kind, 0); if (!index) return 0;
    d->nodes[index - 1].text = freak_json_copy(data, length); d->nodes[index - 1].text_length = length; return freak_json_view(d, index);
}
int64_t freak_json_document_make_number(int64_t doc, freak_word text) { return freak_json_make_text(doc, (const unsigned char *)text.data, text.length, 3); }
int64_t freak_json_document_make_string(int64_t doc, freak_word text) { return freak_json_make_text(doc, (const unsigned char *)text.data, text.length, 4); }
int64_t freak_json_document_make_string_bytes(int64_t doc, int64_t bytes) {
    freak_byte_buffer_record *b = freak_byte_buffer_require(bytes, "JSON string constructor"); return freak_json_make_text(doc, b->data, b->length, 4);
}
int64_t freak_json_document_make_array(int64_t doc) { freak_json_document *d = freak_json_require(doc); return freak_json_view(d, freak_json_add_node(d, 5, 0)); }
int64_t freak_json_document_make_object(int64_t doc) { freak_json_document *d = freak_json_require(doc); return freak_json_view(d, freak_json_add_node(d, 6, 0)); }
static unsigned freak_json_height(freak_json_document *d, uint32_t index) {
    freak_json_node *n = &d->nodes[index - 1]; unsigned height = 1;
    for (size_t i = 0; i < n->count; i++) { unsigned child = 1 + freak_json_height(d, n->edges[i].child); if (child > height) height = child; }
    return height;
}
static bool freak_json_attachable(freak_json_document *d, uint32_t parent, uint32_t child) {
    if (d->error[0]) return false;
    if (d->nodes[child - 1].parent || d->root == child) {
        freak_json_error(d, 0, "child is already attached or is the root"); return false;
    }
    unsigned depth = 0;
    for (uint32_t i = parent; i; i = d->nodes[i - 1].parent) {
        if (i == child) { freak_json_error(d, 0, "construction would create a cycle"); return false; }
        depth++;
    }
    if (depth + freak_json_height(d, child) > FREAK_JSON_DEPTH_LIMIT) {
        freak_json_error(d, 0, "nesting depth limit exceeded"); return false;
    }
    return true;
}
int64_t freak_json_document_set_root(int64_t doc, int64_t node) {
    freak_json_document *d = freak_json_require(doc); uint32_t index = freak_json_index(d, node);
    if (d->error[0]) return 0;
    if (d->nodes[index - 1].parent) { freak_json_error(d, 0, "root must be an unattached node"); return 0; }
    d->root = index; return 1;
}
int64_t freak_json_document_array_append(int64_t doc, int64_t array, int64_t child) {
    freak_json_document *d = freak_json_require(doc); freak_json_typed(d, array, 5);
    uint32_t parent = freak_json_index(d, array), index = freak_json_index(d, child);
    if (!freak_json_attachable(d, parent, index)) return 0;
    return freak_json_attach(d, parent, index, NULL, 0, 0);
}
static int64_t freak_json_insert(int64_t doc, int64_t object, const unsigned char *key, size_t length, int64_t child) {
    freak_json_document *d = freak_json_require(doc); freak_json_typed(d, object, 6);
    uint32_t parent = freak_json_index(d, object), index = freak_json_index(d, child);
    if (!freak_json_attachable(d, parent, index)) return 0;
    if (!freak_system_utf8_valid((const char *)key, length)) { freak_json_error(d, 0, "object key is not valid UTF-8"); return 0; }
    if (!freak_json_text_budget(d, length, FREAK_JSON_STRING_LIMIT, 0)) return 0;
    return freak_json_attach(d, parent, index, freak_json_copy(key, length), length, 0);
}
int64_t freak_json_document_object_insert(int64_t doc, int64_t object, freak_word key, int64_t child) { return freak_json_insert(doc, object, (const unsigned char *)key.data, key.length, child); }
int64_t freak_json_document_object_insert_bytes(int64_t doc, int64_t object, int64_t key, int64_t child) {
    freak_byte_buffer_record *b = freak_byte_buffer_require(key, "JSON object key"); return freak_json_insert(doc, object, b->data, b->length, child);
}
/* Serializer uses bounded storage and emits escapes; it never asks callers to
   prepare quoted/escaped text. Numeric lexemes are emitted without conversion. */
typedef struct { unsigned char *data; size_t length, capacity; freak_json_document *doc; } freak_json_output;
static bool freak_json_emit(freak_json_output *out, const unsigned char *data, size_t length) {
    if (length > FREAK_JSON_OUTPUT_LIMIT - out->length) { freak_json_error(out->doc, 0, "serialized output limit exceeded"); return false; }
    size_t wanted = out->length + length;
    if (wanted > out->capacity) {
        size_t cap = out->capacity ? out->capacity : 128;
        while (cap < wanted) cap *= 2;
        unsigned char *grown = realloc(out->data, cap);
        if (!grown) freak_json_fail("out of memory serializing JSON"); out->data = grown; out->capacity = cap;
    }
    if (length) memcpy(out->data + out->length, data, length); out->length = wanted; return true;
}
static bool freak_json_emit_char(freak_json_output *out, unsigned char ch) { return freak_json_emit(out, &ch, 1); }
static bool freak_json_quote(freak_json_output *out, const unsigned char *text, size_t length) {
    static const unsigned char hex[] = "0123456789abcdef";
    if (!freak_json_emit_char(out, '"')) return false;
    size_t start = 0;
    for (size_t i = 0; i < length; i++) {
        unsigned char ch = text[i];
        if (ch >= 0x20 && ch != '"' && ch != '\\') continue;
        if (!freak_json_emit(out, text + start, i - start)) return false;
        if (ch == '"' || ch == '\\') {
            unsigned char escaped[2] = {'\\', ch}; if (!freak_json_emit(out, escaped, 2)) return false;
        } else {
            unsigned char escaped[6] = {'\\', 'u', '0', '0', hex[ch >> 4], hex[ch & 15]};
            if (!freak_json_emit(out, escaped, 6)) return false;
        }
        start = i + 1;
    }
    return freak_json_emit(out, text + start, length - start) && freak_json_emit_char(out, '"');
}
static bool freak_json_serialize_node(freak_json_output *out, uint32_t index) {
    freak_json_node *n = &out->doc->nodes[index - 1];
    if (n->kind == 1) return freak_json_emit(out, (const unsigned char *)"null", 4);
    if (n->kind == 2) return freak_json_emit(out, (const unsigned char *)(n->boolean ? "true" : "false"), n->boolean ? 4 : 5);
    if (n->kind == 3) return freak_json_emit(out, n->text, n->text_length);
    if (n->kind == 4) return freak_json_quote(out, n->text, n->text_length);
    if (!freak_json_emit_char(out, n->kind == 5 ? '[' : '{')) return false;
    for (size_t i = 0; i < n->count; i++) {
        if (i && !freak_json_emit_char(out, ',')) return false;
        if (n->kind == 6 && (!freak_json_quote(out, n->edges[i].key, n->edges[i].key_length) || !freak_json_emit_char(out, ':'))) return false;
        if (!freak_json_serialize_node(out, n->edges[i].child)) return false;
    }
    return freak_json_emit_char(out, n->kind == 5 ? ']' : '}');
}
static freak_json_output freak_json_serialize(int64_t doc) {
    freak_json_document *d = freak_json_require(doc); freak_json_output out = {NULL, 0, 0, d};
    if (d->error[0]) freak_json_fail("cannot serialize a failed document");
    if (!d->root) freak_json_fail("document has no root");
    if (!freak_json_serialize_node(&out, d->root)) { free(out.data); freak_json_fail("serialized output limit exceeded"); }
    return out;
}
int64_t freak_json_document_serialize_bytes(int64_t doc) {
    freak_json_output out = freak_json_serialize(doc); int64_t bytes = freak_json_bytes(out.data, out.length); free(out.data); return bytes;
}
freak_word freak_json_document_serialize_word(int64_t doc) {
    freak_json_output out = freak_json_serialize(doc);
    freak_word result = freak_word_own((char *)freak_json_copy(out.data, out.length), out.length); free(out.data); return result;
}
/* Scalar LLVM ABI adapters share the same document ownership model. */
#define FREAK_JSON_WRAP0(name) int64_t freak_llvm_json_document_##name(void) { return freak_json_document_##name(); }
#define FREAK_JSON_WRAP1(name) int64_t freak_llvm_json_document_##name(int64_t a) { return freak_json_document_##name(a); }
#define FREAK_JSON_WRAP2(name) int64_t freak_llvm_json_document_##name(int64_t a,int64_t b) { return freak_json_document_##name(a,b); }
#define FREAK_JSON_WRAP3(name) int64_t freak_llvm_json_document_##name(int64_t a,int64_t b,int64_t c) { return freak_json_document_##name(a,b,c); }
#define FREAK_JSON_WORD1(name) int64_t freak_llvm_json_document_##name(int64_t a) { return freak_llvm_word_take(freak_json_document_##name(a)); }
#define FREAK_JSON_WORD2(name) int64_t freak_llvm_json_document_##name(int64_t a,int64_t b) { return freak_llvm_word_take(freak_json_document_##name(a,b)); }
FREAK_JSON_WRAP0(new)
FREAK_JSON_WRAP1(parse_bytes) FREAK_JSON_WRAP1(ok) FREAK_JSON_WRAP1(error_position) FREAK_JSON_WRAP1(root)
FREAK_JSON_WRAP2(set_root) FREAK_JSON_WRAP2(kind) FREAK_JSON_WRAP2(count) FREAK_JSON_WRAP3(array_get)
FREAK_JSON_WRAP3(object_get_bytes) FREAK_JSON_WRAP3(object_key_bytes) FREAK_JSON_WRAP2(bool_value) FREAK_JSON_WRAP2(string_bytes)
FREAK_JSON_WRAP1(make_null) FREAK_JSON_WRAP2(make_bool) FREAK_JSON_WRAP2(make_string_bytes)
FREAK_JSON_WRAP1(make_array) FREAK_JSON_WRAP1(make_object) FREAK_JSON_WRAP3(array_append) FREAK_JSON_WRAP1(serialize_bytes)
FREAK_JSON_WORD1(error) FREAK_JSON_WORD2(number_text) FREAK_JSON_WORD2(string_word) FREAK_JSON_WORD1(serialize_word)
int64_t freak_llvm_json_document_parse(int64_t source) { return freak_json_document_parse(freak_llvm_word_view(source)); }
int64_t freak_llvm_json_document_object_get(int64_t doc,int64_t node,int64_t key) { return freak_json_document_object_get(doc,node,freak_llvm_word_view(key)); }
int64_t freak_llvm_json_document_make_number(int64_t doc,int64_t text) { return freak_json_document_make_number(doc,freak_llvm_word_view(text)); }
int64_t freak_llvm_json_document_make_string(int64_t doc,int64_t text) { return freak_json_document_make_string(doc,freak_llvm_word_view(text)); }
int64_t freak_llvm_json_document_object_insert(int64_t doc,int64_t node,int64_t key,int64_t child) { return freak_json_document_object_insert(doc,node,freak_llvm_word_view(key),child); }
int64_t freak_llvm_json_document_object_insert_bytes(int64_t doc,int64_t node,int64_t key,int64_t child) { return freak_json_document_object_insert_bytes(doc,node,key,child); }
void freak_llvm_json_document_release(int64_t doc) { freak_json_document_release(doc); }
#undef FREAK_JSON_WRAP0
#undef FREAK_JSON_WRAP1
#undef FREAK_JSON_WRAP2
#undef FREAK_JSON_WRAP3
#undef FREAK_JSON_WORD1
#undef FREAK_JSON_WORD2

#endif /* FREAK_V35_JSON_INCLUDED */
