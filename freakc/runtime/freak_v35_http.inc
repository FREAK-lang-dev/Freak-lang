#ifndef FREAK_V35_HTTP_INCLUDED
#define FREAK_V35_HTTP_INCLUDED 1
/* Bounded HTTP/1 request transport with a per-process event loop. Routing
   belongs to the application, which still sees one request at a time through
   next_request. Behind it the runtime accepts, reads, parses and writes every
   connection concurrently (epoll on Linux, kqueue on macOS/BSD, WSAPoll on
   Windows), keeps HTTP/1.1 connections alive, and can fan one listener out to
   worker processes for multi-core throughput. Included after the shared
   ByteBuffer/socket/word substrate. */
#if __has_include("third_party/llhttp/freak_amalgamation.inc")
#include "third_party/llhttp/freak_amalgamation.inc"
#else
#include "../../third_party/llhttp/freak_amalgamation.inc"
#endif
#ifndef _WIN32
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/resource.h>
#if defined(__linux__)
#include <sys/epoll.h>
#include <sys/prctl.h>
#define FREAK_HTTP_EPOLL 1
/* accept4 is declared only under _GNU_SOURCE; the symbol is in every libc. */
extern int accept4(int,struct sockaddr *,socklen_t *,int);
#elif defined(__APPLE__) || defined(__FreeBSD__) || defined(__OpenBSD__) || defined(__NetBSD__) || defined(__DragonFly__)
#include <sys/event.h>
#define FREAK_HTTP_KQUEUE 1
#else
#define FREAK_HTTP_POLL 1
#endif
#else
#define FREAK_HTTP_WSAPOLL 1
#endif

#define FREAK_HTTP_SERVER_DOMAIN UINT64_C(0x9000000000000000)
#define FREAK_HTTP_REQUEST_DOMAIN UINT64_C(0xb000000000000000)
#define FREAK_HTTP_DOMAIN_MASK UINT64_C(0xf000000000000000)
#define FREAK_HTTP_GENERATION_MAX UINT32_C(0x0fffffff)
#define FREAK_HTTP_MAX_WORKERS 256
#define FREAK_HTTP_EVENTS 256
#define FREAK_HTTP_SWEEP_MS 10
#ifdef _WIN32
#define FREAK_HTTP_POLL_IN POLLRDNORM
#define FREAK_HTTP_POLL_OUT POLLWRNORM
#else
#define FREAK_HTTP_POLL_IN POLLIN
#define FREAK_HTTP_POLL_OUT POLLOUT
#endif
enum { FREAK_HTTP_CONN_READ=1, FREAK_HTTP_CONN_QUEUED, FREAK_HTTP_CONN_APP, FREAK_HTTP_CONN_WRITE, FREAK_HTTP_CONN_DRAIN };
typedef struct { size_t line,headers,count,body,chunk_metadata,trailers; uint64_t header_ms,body_ms,idle_ms; } freak_http_limits;
typedef struct { unsigned char *data; size_t length,capacity; } freak_http_text;
typedef struct { freak_http_text name,value; bool trailer; } freak_http_header;
typedef struct freak_http_conn freak_http_conn;
typedef struct freak_http_request freak_http_request;
typedef struct freak_http_server {
    uint32_t generation;
    bool in_use,started,workers_set;
    atomic_bool stopping;
    freak_native_socket listener;
    int status,port,family,requested_port;
    int64_t active,ticket;
    freak_http_limits limits;
    uint64_t keep_alive_ms; size_t keep_alive_requests,max_connections;
    int workers,worker_index;
    /* Event loop. */
#if defined(FREAK_HTTP_EPOLL) || defined(FREAK_HTTP_KQUEUE)
    int poller;
#endif
    bool listener_armed;
    uint64_t accept_pause_until,next_sweep;
    freak_http_conn **conns; size_t conn_count,conn_capacity;
    freak_http_conn *graveyard,*hot;
    freak_http_request *ready_head,*ready_tail;
    /* Worker supervision. */
#ifdef _WIN32
    HANDLE job,parent_process;
    HANDLE children[FREAK_HTTP_MAX_WORKERS];
#else
    pid_t children[FREAK_HTTP_MAX_WORKERS];
    pid_t parent_pid;
#endif
    uint64_t respawn_after[FREAK_HTTP_MAX_WORKERS];
    char address[128];
    char error[192];
} freak_http_server;
struct freak_http_request {
    uint32_t slot;
    bool headers_done,message_done,line_done,chunk_line,expect_continue,responded,head_method,started,persistent;
    freak_native_socket socket;
    int status,response_status;
    int64_t server,body;
    freak_http_limits limits;
    uint64_t header_deadline,body_deadline,idle_deadline;
    size_t line_wire,header_wire,raw_wire,chunk_wire,trailer_wire;
    freak_http_text method,target;
    freak_http_header *headers,*response_headers;
    size_t header_count,header_capacity,response_count,response_capacity,response_wire;
    int current_header;
    llhttp_t parser;
    freak_http_conn *conn;
    freak_http_request *ready_next;
    char error[192];
};
struct freak_http_conn {
    freak_native_socket socket;
    freak_http_server *server;
    size_t index,served,drained;
    int state;
    bool readable,writable,close_after_write,drain_after_write,dead,hot;
    freak_http_request *request;
    freak_http_conn *grave_next,*hot_next;
    unsigned char *in,*out; size_t in_length,in_offset,out_length,out_offset;
    uint64_t idle_deadline,write_deadline,write_idle,drain_deadline;
};
typedef struct { uint32_t generation; freak_http_request *request; } freak_http_ticket;
typedef union { max_align_t alignment; struct { size_t size; } metadata; } freak_http_allocation;
static size_t freak_http_owned_bytes, freak_http_server_live, freak_http_request_live, freak_http_socket_live, freak_http_connection_live;
static freak_http_server **freak_http_servers;
static freak_http_ticket *freak_http_requests;
static size_t freak_http_server_slots,freak_http_server_capacity,freak_http_request_slots,freak_http_request_capacity;
static bool freak_http_cleanup_registered,freak_http_settings_ready;
static llhttp_settings_t freak_http_settings;
static unsigned char freak_http_scratch[65536];

static _Noreturn void freak_http_fail(const char *message) { fprintf(stderr,"FREAK: HTTP floor: %s\n",message); exit(1); }
static void *freak_http_allocate(size_t size) {
    if(size>SIZE_MAX-sizeof(freak_http_allocation) || size>SIZE_MAX-freak_http_owned_bytes) freak_http_fail("allocation overflow");
    freak_http_allocation *block=calloc(1,sizeof(*block)+(size?size:1));
    if(!block) freak_http_fail("out of memory");
    block->metadata.size=size; freak_http_owned_bytes+=size; return block+1;
}
static void freak_http_free(void *pointer) {
    if(!pointer) return;
    freak_http_allocation *block=(freak_http_allocation *)pointer-1;
    freak_http_owned_bytes-=block->metadata.size; free(block);
}
static size_t freak_http_size(const void *pointer) { return pointer?((const freak_http_allocation *)pointer-1)->metadata.size:0; }
static void *freak_http_grow(void *pointer,size_t size) {
    void *grown=freak_http_allocate(size);
    if(pointer) { size_t old=freak_http_size(pointer); memcpy(grown,pointer,old<size?old:size); freak_http_free(pointer); }
    return grown;
}
static void freak_http_close_socket(freak_native_socket *socket) {
    if(*socket!=FREAK_INVALID_NATIVE_SOCKET) { freak_tcp_socket_native_close(*socket); *socket=FREAK_INVALID_NATIVE_SOCKET; freak_http_socket_live--; }
}
static bool freak_http_nonblocking(freak_native_socket socket) {
#ifdef _WIN32
    u_long enabled=1;
    return ioctlsocket(socket,FIONBIO,&enabled)==0 && SetHandleInformation((HANDLE)socket,HANDLE_FLAG_INHERIT,0);
#else
    int flags=fcntl(socket,F_GETFL,0),fdflags=fcntl(socket,F_GETFD,0);
    return flags>=0 && fdflags>=0 && fcntl(socket,F_SETFL,flags|O_NONBLOCK)==0 && fcntl(socket,F_SETFD,fdflags|FD_CLOEXEC)==0;
#endif
}
static unsigned char freak_http_lower(unsigned char c) { return c>='A'&&c<='Z' ? (unsigned char)(c+('a'-'A')) : c; }
static bool freak_http_equal(const unsigned char *a,size_t length,const char *b) {
    if(strlen(b)!=length) return false;
    for(size_t i=0;i<length;i++) if(freak_http_lower(a[i])!=(unsigned char)b[i]) return false;
    return true;
}
static bool freak_http_token(unsigned char c) {
    return c!=0 && ((c>='0'&&c<='9')||(c>='a'&&c<='z')||(c>='A'&&c<='Z')||strchr("!#$%&'*+-.^_`|~",c)!=NULL);
}
static bool freak_http_hex(unsigned char c) { return (c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F'); }
static freak_http_server *freak_http_require_server(int64_t ticket) {
    uint64_t bits=(uint64_t)ticket; uint32_t slot=(uint32_t)bits,generation=(uint32_t)(bits>>32)&FREAK_HTTP_GENERATION_MAX;
    if((bits&FREAK_HTTP_DOMAIN_MASK)!=FREAK_HTTP_SERVER_DOMAIN || !slot || slot>freak_http_server_slots) freak_http_fail("invalid or stale server ticket");
    freak_http_server *server=freak_http_servers[slot-1];
    if(!server->in_use || server->generation!=generation) freak_http_fail("invalid or stale server ticket"); return server;
}
static freak_http_request *freak_http_require_request(int64_t ticket) {
    uint64_t bits=(uint64_t)ticket; uint32_t slot=(uint32_t)bits,generation=(uint32_t)(bits>>32)&FREAK_HTTP_GENERATION_MAX;
    if((bits&FREAK_HTTP_DOMAIN_MASK)!=FREAK_HTTP_REQUEST_DOMAIN || !slot || slot>freak_http_request_slots) freak_http_fail("invalid or stale request ticket");
    freak_http_ticket *entry=&freak_http_requests[slot-1];
    if(!entry->request || entry->generation!=generation) freak_http_fail("invalid or stale request ticket"); return entry->request;
}
static freak_http_server *freak_http_find_server(int64_t ticket) {
    uint64_t bits=(uint64_t)ticket; uint32_t slot=(uint32_t)bits;
    if((bits&FREAK_HTTP_DOMAIN_MASK)!=FREAK_HTTP_SERVER_DOMAIN || !slot || slot>freak_http_server_slots) return NULL;
    freak_http_server *server=freak_http_servers[slot-1];
    return server->in_use && server->generation==((bits>>32)&FREAK_HTTP_GENERATION_MAX) ? server : NULL;
}
static bool freak_http_stopping(const freak_http_server *server) { return atomic_load_explicit(&((freak_http_server *)server)->stopping,memory_order_acquire); }
static void freak_http_error(freak_http_request *request,int status,const char *message) {
    if(!request->status) { request->status=status; snprintf(request->error,sizeof(request->error),"%s",message); }
}
static void freak_http_text_append(freak_http_text *text,const void *bytes,size_t length,size_t limit) {
    if(length>limit-text->length) freak_http_fail("internal bounded text admission failed");
    size_t required=text->length+length+1;
    if(required>text->capacity) {
        size_t capacity=text->capacity?text->capacity:32;
        while(capacity<required) { if(capacity>(limit+1)/2) { capacity=limit+1; break; } capacity*=2; }
        text->data=freak_http_grow(text->data,capacity); text->capacity=capacity;
    }
    if(length) memcpy(text->data+text->length,bytes,length); text->length+=length; text->data[text->length]=0;
}
static freak_word freak_http_word(const unsigned char *bytes,size_t length) {
    if(!freak_byte_buffer_utf8_valid(bytes,length)) freak_http_fail("header value is binary; use the bytes getter");
    char *copy=freak_command_allocate(length+1,1); if(length) memcpy(copy,bytes,length); return freak_word_own(copy,length);
}
static int64_t freak_http_bytes(const unsigned char *bytes,size_t length) {
    int64_t ticket=freak_byte_buffer_with_capacity((int64_t)length);
    freak_byte_buffer_record *buffer=freak_byte_buffer_require(ticket,"HTTP bytes getter");
    if(length) memcpy(buffer->data,bytes,length); buffer->length=length; return ticket;
}
static void freak_http_release_headers(freak_http_header *headers,size_t count) {
    for(size_t i=0;i<count;i++) { freak_http_free(headers[i].name.data); freak_http_free(headers[i].value.data); } freak_http_free(headers);
}
/* Growable byte queue: the unread pipelined input or unsent output of a
   connection. Offsets keep partial progress without memmove per write. */
static void freak_http_queue_append(unsigned char **queue,size_t *length,size_t *offset,const void *bytes,size_t count) {
    if(!count) return;
    if(*offset && *offset==*length) { *offset=0; *length=0; }
    size_t capacity=freak_http_size(*queue);
    if(*length+count>capacity) {
        size_t live=*length-*offset;
        if(*offset && live+count<=capacity) { memmove(*queue,*queue+*offset,live); }
        else {
            size_t next=capacity?capacity:4096; while(next<live+count) { if(next>SIZE_MAX/2) freak_http_fail("queue overflow"); next*=2; }
            unsigned char *grown=freak_http_allocate(next); if(live) memcpy(grown,*queue+*offset,live); freak_http_free(*queue); *queue=grown;
        }
        *length=live; *offset=0;
    }
    memcpy(*queue+*length,bytes,count); *length+=count;
}
static void freak_http_free_request(freak_http_request *request) {
    freak_http_free(request->method.data); freak_http_free(request->target.data);
    freak_http_release_headers(request->headers,request->header_count);
    freak_http_release_headers(request->response_headers,request->response_count);
    if(request->body) freak_byte_buffer_release(request->body);
    if(request->slot) {
        freak_http_ticket *entry=&freak_http_requests[request->slot-1]; entry->request=NULL; freak_http_request_live--;
    }
    freak_http_free(request);
}
static int freak_http_on_method(llhttp_t *,const char *,size_t); static int freak_http_on_target(llhttp_t *,const char *,size_t);
static int freak_http_on_field(llhttp_t *,const char *,size_t); static int freak_http_on_value(llhttp_t *,const char *,size_t);
static int freak_http_on_value_complete(llhttp_t *); static int freak_http_on_headers(llhttp_t *);
static int freak_http_on_body(llhttp_t *,const char *,size_t); static int freak_http_on_chunk(llhttp_t *);
static int freak_http_on_chunk_complete(llhttp_t *); static int freak_http_on_complete(llhttp_t *);
static void freak_http_init_settings(void) {
    if(freak_http_settings_ready) return;
    llhttp_settings_t *settings=&freak_http_settings; llhttp_settings_init(settings);
    settings->on_method=freak_http_on_method; settings->on_url=freak_http_on_target;
    settings->on_header_field=freak_http_on_field; settings->on_header_value=freak_http_on_value;
    settings->on_header_value_complete=freak_http_on_value_complete; settings->on_headers_complete=freak_http_on_headers;
    settings->on_body=freak_http_on_body; settings->on_chunk_header=freak_http_on_chunk;
    settings->on_chunk_complete=freak_http_on_chunk_complete; settings->on_message_complete=freak_http_on_complete;
    freak_http_settings_ready=true;
}
static freak_http_request *freak_http_new_request(freak_http_server *server,freak_http_conn *conn) {
    freak_http_request *request=freak_http_allocate(sizeof(freak_http_request));
    request->socket=FREAK_INVALID_NATIVE_SOCKET; request->server=server->ticket; request->limits=server->limits;
    request->current_header=-1; request->response_status=200; request->conn=conn;
    freak_http_init_settings(); llhttp_init(&request->parser,HTTP_REQUEST,&freak_http_settings); request->parser.data=request;
    return request;
}
static int64_t freak_http_ticket_for(freak_http_request *request) {
    size_t slot=0;
    while(slot<freak_http_request_slots && (freak_http_requests[slot].request || freak_http_requests[slot].generation==FREAK_HTTP_GENERATION_MAX)) slot++;
    if(slot==freak_http_request_slots) {
        if(slot>=UINT32_MAX-1) freak_http_fail("request ticket table exhausted");
        if(slot==freak_http_request_capacity) { size_t next=freak_http_request_capacity?freak_http_request_capacity*2:16; freak_http_requests=freak_http_grow(freak_http_requests,next*sizeof(*freak_http_requests)); freak_http_request_capacity=next; }
        freak_http_request_slots++;
    }
    freak_http_ticket *entry=&freak_http_requests[slot]; entry->generation++; entry->request=request;
    request->slot=(uint32_t)(slot+1); freak_http_request_live++;
    if(!request->body) request->body=freak_byte_buffer_new();
    return (int64_t)(FREAK_HTTP_REQUEST_DOMAIN|((uint64_t)entry->generation<<32)|(slot+1));
}

/* ── Poller: one abstraction over epoll, kqueue and (WSA)poll ─────────── */
static bool freak_http_poller_open(freak_http_server *server) {
#if defined(FREAK_HTTP_EPOLL)
    server->poller=epoll_create1(EPOLL_CLOEXEC); return server->poller>=0;
#elif defined(FREAK_HTTP_KQUEUE)
    server->poller=kqueue(); if(server->poller<0) return false;
    int flags=fcntl(server->poller,F_GETFD,0); if(flags>=0) fcntl(server->poller,F_SETFD,flags|FD_CLOEXEC); return true;
#else
    (void)server; return true;
#endif
}
static void freak_http_poller_close(freak_http_server *server) {
#if defined(FREAK_HTTP_EPOLL) || defined(FREAK_HTTP_KQUEUE)
    if(server->poller>=0) { close(server->poller); server->poller=-1; }
#else
    (void)server;
#endif
}
/* Connections are edge-triggered for read and write once, for their whole
   life: state changes never cost a syscall. readable/writable remember an
   edge until a call reports would-block. */
static bool freak_http_poller_add(freak_http_conn *conn) {
#if defined(FREAK_HTTP_EPOLL)
    struct epoll_event event={0}; event.events=EPOLLIN|EPOLLOUT|EPOLLRDHUP|EPOLLET; event.data.ptr=conn;
    return epoll_ctl(conn->server->poller,EPOLL_CTL_ADD,conn->socket,&event)==0;
#elif defined(FREAK_HTTP_KQUEUE)
    struct kevent changes[2];
    EV_SET(&changes[0],conn->socket,EVFILT_READ,EV_ADD|EV_CLEAR,0,0,conn);
    EV_SET(&changes[1],conn->socket,EVFILT_WRITE,EV_ADD|EV_CLEAR,0,0,conn);
    return kevent(conn->server->poller,changes,2,NULL,0,NULL)==0;
#else
    (void)conn; return true;
#endif
}
static void freak_http_listener_arm(freak_http_server *server,bool armed) {
    if(server->listener_armed==armed || server->listener==FREAK_INVALID_NATIVE_SOCKET) return;
#if defined(FREAK_HTTP_EPOLL)
    if(armed) {
        struct epoll_event event={0}; event.events=EPOLLIN; event.data.ptr=NULL;
        /* Workers share one listener: wake one of them per connection. */
#ifdef EPOLLEXCLUSIVE
        if(server->workers>1) event.events|=EPOLLEXCLUSIVE;
#endif
        if(epoll_ctl(server->poller,EPOLL_CTL_ADD,server->listener,&event)!=0) return;
    } else epoll_ctl(server->poller,EPOLL_CTL_DEL,server->listener,NULL);
#elif defined(FREAK_HTTP_KQUEUE)
    struct kevent change; EV_SET(&change,server->listener,EVFILT_READ,armed?EV_ADD:EV_DELETE,0,0,NULL);
    if(kevent(server->poller,&change,1,NULL,0,NULL)!=0 && armed) return;
#endif
    server->listener_armed=armed;
}

static void freak_http_conn_destroy(freak_http_conn *conn) {
    if(conn->dead) return;
    freak_http_server *server=conn->server; conn->dead=true;
#if defined(FREAK_HTTP_EPOLL)
    if(server->poller>=0) epoll_ctl(server->poller,EPOLL_CTL_DEL,conn->socket,NULL);
#endif
    freak_http_close_socket(&conn->socket);
    if(conn->request) {
        freak_http_request *request=conn->request; conn->request=NULL; request->conn=NULL; request->socket=FREAK_INVALID_NATIVE_SOCKET;
        /* An internal parse state belongs to the connection; a queued one is
           still delivered, as a failed request, so the queue stays valid. */
        if(conn->state==FREAK_HTTP_CONN_QUEUED) { if(!request->status) freak_http_error(request,503,"HTTP connection closed"); }
        else if(!request->slot) freak_http_free_request(request);
    }
    size_t last=server->conn_count-1;
    if(conn->index!=last) { server->conns[conn->index]=server->conns[last]; server->conns[conn->index]->index=conn->index; }
    server->conn_count--; freak_http_connection_live--;
    freak_http_free(conn->in); freak_http_free(conn->out); conn->in=conn->out=NULL;
    conn->grave_next=server->graveyard; server->graveyard=conn;
}
static void freak_http_bury(freak_http_server *server) {
    if(!server->graveyard) return;
    freak_http_conn **link=&server->hot;
    while(*link) { if((*link)->dead) *link=(*link)->hot_next; else link=&(*link)->hot_next; }
    while(server->graveyard) { freak_http_conn *conn=server->graveyard; server->graveyard=conn->grave_next; freak_http_free(conn); }
}
static void freak_http_deliver(freak_http_server *server,freak_http_request *request) {
    request->ready_next=NULL;
    if(server->ready_tail) server->ready_tail->ready_next=request; else server->ready_head=request;
    server->ready_tail=request;
}

static void freak_http_cleanup(void) {
#if defined(FREAK_RUNTIME_OWNERSHIP_AUDIT) || defined(FREAK_C_RUNTIME_OWNERSHIP_AUDIT)
    if(freak_http_server_live || freak_http_request_live) { fprintf(stderr,"FREAK: ownership audit found live HTTP server/request owners\n"); _Exit(1); }
#endif
    for(size_t i=0;i<freak_http_server_slots;i++) {
        freak_http_server *server=freak_http_servers[i];
        if(server->in_use) {
            while(server->conn_count) freak_http_conn_destroy(server->conns[server->conn_count-1]);
            while(server->ready_head) { freak_http_request *request=server->ready_head; server->ready_head=request->ready_next; request->conn=NULL; if(!request->slot) freak_http_free_request(request); }
            freak_http_bury(server); freak_http_close_socket(&server->listener); freak_http_poller_close(server); freak_http_free(server->conns);
        }
        freak_http_free(server);
    }
    for(size_t i=0;i<freak_http_request_slots;i++) if(freak_http_requests[i].request) { freak_http_request *request=freak_http_requests[i].request; request->conn=NULL; freak_http_free_request(request); }
    freak_http_free(freak_http_requests); freak_http_free(freak_http_servers);
}
static void freak_http_register(void) {
    if(!freak_http_cleanup_registered) { if(atexit(freak_http_cleanup)) freak_http_fail("cannot register cleanup"); freak_http_cleanup_registered=true; }
}
static int64_t freak_http_new_server(void) {
    freak_http_register(); size_t slot=0;
    while(slot<freak_http_server_slots && (freak_http_servers[slot]->in_use || freak_http_servers[slot]->generation==FREAK_HTTP_GENERATION_MAX)) slot++;
    if(slot==freak_http_server_slots) {
        if(slot>=UINT32_MAX-1) freak_http_fail("server ticket table exhausted");
        if(slot==freak_http_server_capacity) { size_t next=freak_http_server_capacity?freak_http_server_capacity*2:16; freak_http_servers=freak_http_grow(freak_http_servers,next*sizeof(*freak_http_servers)); freak_http_server_capacity=next; }
        freak_http_servers[slot]=freak_http_allocate(sizeof(freak_http_server)); freak_http_server_slots++;
    }
    freak_http_server *server=freak_http_servers[slot]; uint32_t generation=server->generation+1; memset(server,0,sizeof(*server));
    server->generation=generation; server->in_use=true; atomic_init(&server->stopping,false); server->listener=FREAK_INVALID_NATIVE_SOCKET;
#if defined(FREAK_HTTP_EPOLL) || defined(FREAK_HTTP_KQUEUE)
    server->poller=-1;
#endif
    server->limits=(freak_http_limits){8192,32768,100,1048576,4096,8192,5000,15000,2000};
    server->keep_alive_ms=5000; server->keep_alive_requests=1000; server->max_connections=4096; server->workers=1;
    freak_http_server_live++;
    server->ticket=(int64_t)(FREAK_HTTP_SERVER_DOMAIN|((uint64_t)generation<<32)|(slot+1));
    return server->ticket;
}

/* ── Binding, including adoption of a listener a parent worker shared ─── */
#ifdef _WIN32
static bool freak_http_adopt_listener(freak_http_server *server,const char *address,int64_t port) {
    char inherited[512]; DWORD length=GetEnvironmentVariableA("FREAK_HTTP_WORKER_LISTENER",inherited,sizeof(inherited));
    if(!length || length>=sizeof(inherited)) return false;
    unsigned long long handle=0; int requested=0,actual=0,index=0,family=0; unsigned long parent=0; char bound[128]={0};
    if(sscanf(inherited,"%llu|%d|%d|%d|%d|%lu|%127s",&handle,&requested,&actual,&family,&index,&parent,bound)!=7) return false;
    if(requested!=port || strcmp(bound,address)!=0) return false;
    SetEnvironmentVariableA("FREAK_HTTP_WORKER_LISTENER",NULL);
    server->listener=(SOCKET)handle; freak_http_socket_live++;
    if(!freak_http_nonblocking(server->listener)) return false;
    server->port=actual; server->family=family; server->worker_index=index; server->workers=1; server->workers_set=true;
    server->parent_process=OpenProcess(SYNCHRONIZE,FALSE,(DWORD)parent);
    return true;
}
#endif
int64_t freak_http_server_bind(freak_word address,int64_t port,int64_t allow_non_loopback) {
    int64_t ticket=freak_http_new_server(); freak_http_server *server=freak_http_require_server(ticket);
    if(port<0 || port>65535 || (allow_non_loopback!=0 && allow_non_loopback!=1) || !address.data || !address.length || address.length>127 || memchr(address.data,0,address.length)) goto invalid;
    char name[128]; memcpy(name,address.data,address.length); name[address.length]=0;
    struct sockaddr_storage storage; memset(&storage,0,sizeof(storage)); int family; bool loopback;
    struct sockaddr_in *v4=(struct sockaddr_in *)&storage; struct sockaddr_in6 *v6=(struct sockaddr_in6 *)&storage;
    if(inet_pton(AF_INET,name,&v4->sin_addr)==1) { family=AF_INET; v4->sin_family=AF_INET; v4->sin_port=htons((uint16_t)port); loopback=(ntohl(v4->sin_addr.s_addr)>>24)==127; }
    else if(inet_pton(AF_INET6,name,&v6->sin6_addr)==1) { family=AF_INET6; v6->sin6_family=AF_INET6; v6->sin6_port=htons((uint16_t)port); static const unsigned char local[16]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1}; loopback=memcmp(&v6->sin6_addr,local,16)==0; }
    else goto invalid;
    if(!loopback && !allow_non_loopback) { snprintf(server->error,sizeof(server->error),"non-loopback bind requires explicit opt-in"); server->status=2; return ticket; }
    memcpy(server->address,name,address.length+1); server->family=family; server->requested_port=(int)port;
#ifdef _WIN32
    freak_wsa_init();
    if(freak_http_adopt_listener(server,name,port)) return ticket;
    if(server->listener!=FREAK_INVALID_NATIVE_SOCKET) goto failed;
#endif
    server->listener=socket(family,SOCK_STREAM,IPPROTO_TCP);
    if(server->listener==FREAK_INVALID_NATIVE_SOCKET) goto failed;
    freak_http_socket_live++;
    int enabled=1;
#ifdef _WIN32
    if(setsockopt(server->listener,SOL_SOCKET,SO_EXCLUSIVEADDRUSE,(const char *)&enabled,sizeof(enabled))!=0) goto failed;
#else
    if(setsockopt(server->listener,SOL_SOCKET,SO_REUSEADDR,&enabled,sizeof(enabled))!=0) goto failed;
#endif
    if(!freak_http_nonblocking(server->listener)) goto failed;
    size_t address_size=family==AF_INET?sizeof(*v4):sizeof(*v6);
    /* SOMAXCONN asks for the kernel's own ceiling (net.core.somaxconn on
       Linux); bursts queue in the kernel while the loop is busy. */
    if(bind(server->listener,(struct sockaddr *)&storage,(int)address_size)!=0 || listen(server->listener,SOMAXCONN)!=0) goto failed;
#ifdef _WIN32
    int actual_size=(int)sizeof(storage);
#else
    socklen_t actual_size=sizeof(storage);
#endif
    if(getsockname(server->listener,(struct sockaddr *)&storage,&actual_size)!=0) goto failed;
    server->port=family==AF_INET?ntohs(v4->sin_port):ntohs(v6->sin6_port); return ticket;
invalid:
    snprintf(server->error,sizeof(server->error),"bind requires a numeric IP address, valid port, and explicit non-loopback option"); server->status=2; return ticket;
failed:
    freak_http_close_socket(&server->listener); snprintf(server->error,sizeof(server->error),"could not bind/listen HTTP socket"); server->status=2; return ticket;
}
int64_t freak_http_server_open(int64_t port) { return freak_http_server_bind(freak_word_lit("127.0.0.1"),port,0); }
int64_t freak_http_server_status(int64_t ticket) { freak_http_server *server=freak_http_require_server(ticket); return freak_http_stopping(server)?1:server->status; }
freak_word freak_http_server_error(int64_t ticket) { return freak_word_copy_cstr(freak_http_require_server(ticket)->error); }
int64_t freak_http_server_local_port(int64_t ticket) { return freak_http_require_server(ticket)->port; }
static freak_http_server *freak_http_configurable(int64_t ticket) { freak_http_server *server=freak_http_require_server(ticket); if(server->active) freak_http_fail("cannot change options while a request is active"); return server; }
void freak_http_server_set_limits(int64_t ticket,int64_t line,int64_t headers,int64_t count,int64_t body) {
    freak_http_server *server=freak_http_configurable(ticket);
    if(line<16 || line>65536 || headers<16 || headers>1048576 || count<1 || count>4096 || body<0 || body>67108864) freak_http_fail("invalid HTTP size limits");
    server->limits.line=(size_t)line; server->limits.headers=(size_t)headers; server->limits.count=(size_t)count; server->limits.body=(size_t)body;
}
void freak_http_server_set_timeouts(int64_t ticket,int64_t header,int64_t body,int64_t idle) {
    freak_http_server *server=freak_http_configurable(ticket);
    if(header<1 || header>3600000 || body<1 || body>3600000 || idle<1 || idle>3600000) freak_http_fail("invalid HTTP timeouts");
    server->limits.header_ms=(uint64_t)header; server->limits.body_ms=(uint64_t)body; server->limits.idle_ms=(uint64_t)idle;
}
void freak_http_server_set_chunk_limits(int64_t ticket,int64_t metadata,int64_t trailers) {
    freak_http_server *server=freak_http_configurable(ticket);
    if(metadata<4 || metadata>1048576 || trailers<2 || trailers>1048576) freak_http_fail("invalid HTTP chunk limits");
    server->limits.chunk_metadata=(size_t)metadata; server->limits.trailers=(size_t)trailers;
}
void freak_http_server_set_keep_alive(int64_t ticket,int64_t idle_ms,int64_t max_requests) {
    freak_http_server *server=freak_http_configurable(ticket);
    if(idle_ms<1 || idle_ms>3600000 || max_requests<0 || max_requests>1000000000) freak_http_fail("invalid HTTP keep-alive options");
    server->keep_alive_ms=(uint64_t)idle_ms; server->keep_alive_requests=(size_t)max_requests;
}
void freak_http_server_set_max_connections(int64_t ticket,int64_t count) {
    freak_http_server *server=freak_http_configurable(ticket);
    if(count<1 || count>1048576) freak_http_fail("invalid HTTP connection limit");
    server->max_connections=(size_t)count;
}
void freak_http_server_set_workers(int64_t ticket,int64_t count) {
    freak_http_server *server=freak_http_configurable(ticket);
    if(count<0 || count>FREAK_HTTP_MAX_WORKERS) freak_http_fail("invalid HTTP worker count");
    if(server->started) freak_http_fail("workers must be set before the first next_request");
    if(server->worker_index) return; /* an adopted worker never spawns */
    server->workers=(int)count; server->workers_set=true;
}
int64_t freak_http_server_worker_index(int64_t ticket) { return freak_http_require_server(ticket)->worker_index; }
void freak_http_server_stop(int64_t ticket) { atomic_store_explicit(&freak_http_require_server(ticket)->stopping,true,memory_order_release); }

/* ── Worker processes ─────────────────────────────────────────────────── */
static int freak_http_cpu_count(void) {
#ifdef _WIN32
    SYSTEM_INFO info; GetSystemInfo(&info); return info.dwNumberOfProcessors>0?(int)info.dwNumberOfProcessors:1;
#else
    long count=sysconf(_SC_NPROCESSORS_ONLN); return count>0?(int)count:1;
#endif
}
static void freak_http_stop_children(freak_http_server *server) {
#ifdef _WIN32
    for(int i=1;i<FREAK_HTTP_MAX_WORKERS;i++) if(server->children[i]) { TerminateProcess(server->children[i],0); WaitForSingleObject(server->children[i],2000); CloseHandle(server->children[i]); server->children[i]=NULL; }
    if(server->job) { CloseHandle(server->job); server->job=NULL; }
    if(server->parent_process) { CloseHandle(server->parent_process); server->parent_process=NULL; }
#else
    bool any=false;
    for(int i=1;i<FREAK_HTTP_MAX_WORKERS;i++) if(server->children[i]>0) { kill(server->children[i],SIGTERM); any=true; }
    if(!any) return;
    uint64_t deadline=freak_command_now_ms()+2000;
    for(;;) {
        bool waiting=false;
        for(int i=1;i<FREAK_HTTP_MAX_WORKERS;i++) if(server->children[i]>0) {
            pid_t done=waitpid(server->children[i],NULL,WNOHANG);
            if(done==server->children[i] || (done<0 && errno==ECHILD)) server->children[i]=0; else waiting=true;
        }
        if(!waiting) return;
        if(freak_command_now_ms()>=deadline) {
            for(int i=1;i<FREAK_HTTP_MAX_WORKERS;i++) if(server->children[i]>0) { kill(server->children[i],SIGKILL); waitpid(server->children[i],NULL,0); server->children[i]=0; }
            return;
        }
        freak_time_sleep(5);
    }
#endif
}
#ifdef _WIN32
static bool freak_http_spawn_worker(freak_http_server *server,int index) {
    if(!server->job) {
        server->job=CreateJobObjectW(NULL,NULL); if(!server->job) return false;
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits; memset(&limits,0,sizeof(limits));
        limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        SetInformationJobObject(server->job,JobObjectExtendedLimitInformation,&limits,sizeof(limits));
    }
    char value[512]; snprintf(value,sizeof(value),"%llu|%d|%d|%d|%d|%lu|%s",(unsigned long long)server->listener,server->requested_port,server->port,server->family,index,(unsigned long)GetCurrentProcessId(),server->address);
    HANDLE handles[4]; int count=0; handles[count++]=(HANDLE)server->listener;
    HANDLE standard[3]={GetStdHandle(STD_INPUT_HANDLE),GetStdHandle(STD_OUTPUT_HANDLE),GetStdHandle(STD_ERROR_HANDLE)};
    for(int i=0;i<3;i++) { if(standard[i] && standard[i]!=INVALID_HANDLE_VALUE && SetHandleInformation(standard[i],HANDLE_FLAG_INHERIT,HANDLE_FLAG_INHERIT)) { bool seen=false; for(int j=0;j<count;j++) if(handles[j]==standard[i]) seen=true; if(!seen) handles[count++]=standard[i]; } else standard[i]=NULL; }
    if(!SetHandleInformation((HANDLE)server->listener,HANDLE_FLAG_INHERIT,HANDLE_FLAG_INHERIT)) return false;
    SIZE_T size=0; InitializeProcThreadAttributeList(NULL,1,0,&size);
    LPPROC_THREAD_ATTRIBUTE_LIST attributes=(LPPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(GetProcessHeap(),0,size);
    bool ok=attributes && InitializeProcThreadAttributeList(attributes,1,0,&size) && UpdateProcThreadAttribute(attributes,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,handles,count*sizeof(HANDLE),NULL,NULL);
    STARTUPINFOEXW startup; memset(&startup,0,sizeof(startup)); startup.StartupInfo.cb=sizeof(startup); startup.lpAttributeList=attributes;
    if(standard[0]||standard[1]||standard[2]) { startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES; startup.StartupInfo.hStdInput=standard[0]; startup.StartupInfo.hStdOutput=standard[1]; startup.StartupInfo.hStdError=standard[2]; }
    PROCESS_INFORMATION process; memset(&process,0,sizeof(process));
    wchar_t module[32768]; DWORD length=GetModuleFileNameW(NULL,module,32768);
    wchar_t *command=_wcsdup(GetCommandLineW());
    SetEnvironmentVariableA("FREAK_HTTP_WORKER_LISTENER",value);
    if(ok) ok=length>0 && length<32768 && command && CreateProcessW(module,command,NULL,NULL,TRUE,EXTENDED_STARTUPINFO_PRESENT|CREATE_SUSPENDED,NULL,NULL,&startup.StartupInfo,&process);
    SetEnvironmentVariableA("FREAK_HTTP_WORKER_LISTENER",NULL);
    SetHandleInformation((HANDLE)server->listener,HANDLE_FLAG_INHERIT,0);
    free(command); if(attributes) { DeleteProcThreadAttributeList(attributes); HeapFree(GetProcessHeap(),0,attributes); }
    if(!ok) return false;
    AssignProcessToJobObject(server->job,process.hProcess); ResumeThread(process.hThread); CloseHandle(process.hThread);
    server->children[index]=process.hProcess; return true;
}
#else
static void freak_http_become_child(freak_http_server *server,int index,pid_t parent) {
    server->worker_index=index; server->workers=1; server->parent_pid=parent;
    for(int i=0;i<FREAK_HTTP_MAX_WORKERS;i++) server->children[i]=0;
#ifdef __linux__
    prctl(PR_SET_PDEATHSIG,SIGTERM);
#endif
    if(getppid()!=parent) _exit(0);
    /* The epoll instance is shared with the parent until we drop our
       reference: close it before touching connections, so destroying them
       below cannot remove the parent's interest in its own sockets. */
#if defined(FREAK_HTTP_EPOLL)
    freak_http_poller_close(server);
#elif defined(FREAK_HTTP_KQUEUE)
    server->poller=-1; /* kqueues are not inherited across fork */
#endif
    /* Inherited connections belong to the parent: drop our copies quietly. */
    while(server->conn_count) freak_http_conn_destroy(server->conns[server->conn_count-1]);
    while(server->ready_head) { freak_http_request *request=server->ready_head; server->ready_head=request->ready_next; request->conn=NULL; if(!request->slot) freak_http_free_request(request); }
    server->ready_tail=NULL; server->hot=NULL; freak_http_bury(server);
    server->listener_armed=false;
    /* A respawned worker resumes inside a running loop: give it its own. */
    if(freak_http_poller_open(server)) freak_http_listener_arm(server,true);
}
static bool freak_http_spawn_worker(freak_http_server *server,int index) {
    fflush(NULL); pid_t parent=getpid(); pid_t child=fork();
    if(child<0) return false;
    if(child==0) { freak_http_become_child(server,index,parent); return true; }
    server->children[index]=child; return true;
}
#endif
static void freak_http_supervise(freak_http_server *server,uint64_t now) {
    if(server->worker_index) {
#ifdef _WIN32
        if(server->parent_process && WaitForSingleObject(server->parent_process,0)==WAIT_OBJECT_0) atomic_store_explicit(&server->stopping,true,memory_order_release);
#else
        if(server->parent_pid && getppid()!=server->parent_pid) atomic_store_explicit(&server->stopping,true,memory_order_release);
#endif
        return;
    }
    if(freak_http_stopping(server)) return;
    for(int i=1;i<server->workers && i<FREAK_HTTP_MAX_WORKERS;i++) {
#ifdef _WIN32
        if(server->children[i] && WaitForSingleObject(server->children[i],0)==WAIT_OBJECT_0) { CloseHandle(server->children[i]); server->children[i]=NULL; server->respawn_after[i]=now+1000; }
        if(!server->children[i] && now>=server->respawn_after[i]) { if(!freak_http_spawn_worker(server,i)) server->respawn_after[i]=now+1000; }
#else
        if(server->children[i]>0) { pid_t done=waitpid(server->children[i],NULL,WNOHANG); if(done==server->children[i] || (done<0 && errno==ECHILD)) { server->children[i]=0; server->respawn_after[i]=now+1000; } }
        if(!server->children[i] && now>=server->respawn_after[i]) {
            if(!freak_http_spawn_worker(server,i)) server->respawn_after[i]=now+1000;
            else if(server->worker_index) return; /* this is the new child */
        }
#endif
    }
}
static bool freak_http_start(freak_http_server *server) {
    server->started=true;
    if(!server->workers_set) {
        const char *requested=getenv("FREAK_HTTP_WORKERS");
        if(requested && *requested) { char *end=NULL; long count=strtol(requested,&end,10); if(end && !*end && count>=0 && count<=FREAK_HTTP_MAX_WORKERS) server->workers=(int)count; }
    }
    if(server->workers==0) server->workers=freak_http_cpu_count();
    if(server->workers>FREAK_HTTP_MAX_WORKERS) server->workers=FREAK_HTTP_MAX_WORKERS;
#ifndef _WIN32
    struct rlimit files;
    if(getrlimit(RLIMIT_NOFILE,&files)==0 && files.rlim_cur!=RLIM_INFINITY && files.rlim_cur<server->max_connections+64) {
        rlim_t wanted=(rlim_t)server->max_connections+64; if(files.rlim_max!=RLIM_INFINITY && wanted>files.rlim_max) wanted=files.rlim_max;
        if(wanted>files.rlim_cur) { files.rlim_cur=wanted; setrlimit(RLIMIT_NOFILE,&files); }
    }
#endif
    if(!server->worker_index) for(int i=1;i<server->workers;i++) {
        if(!freak_http_spawn_worker(server,i)) server->respawn_after[i]=freak_command_now_ms()+1000;
        else if(server->worker_index) break; /* child: stop spawning */
    }
#if defined(FREAK_HTTP_EPOLL) || defined(FREAK_HTTP_KQUEUE)
    if(server->poller<0 && !freak_http_poller_open(server)) return false;
#endif
    freak_http_listener_arm(server,true);
    return true;
}
void freak_http_server_close(int64_t ticket) {
    freak_http_server *server=freak_http_require_server(ticket); atomic_store_explicit(&server->stopping,true,memory_order_release);
    if(!server->worker_index) freak_http_stop_children(server);
#ifdef _WIN32
    else if(server->parent_process) { CloseHandle(server->parent_process); server->parent_process=NULL; }
#endif
    while(server->conn_count) freak_http_conn_destroy(server->conns[server->conn_count-1]);
    while(server->ready_head) { freak_http_request *request=server->ready_head; server->ready_head=request->ready_next; request->conn=NULL; if(!request->slot) freak_http_free_request(request); }
    server->ready_tail=NULL; freak_http_bury(server);
    freak_http_close_socket(&server->listener); freak_http_poller_close(server);
    freak_http_free(server->conns); server->conns=NULL; server->conn_capacity=0;
    for(size_t i=0;i<freak_http_request_slots;i++) {
        freak_http_request *request=freak_http_requests[i].request;
        if(request && request->server==ticket) { request->conn=NULL; request->socket=FREAK_INVALID_NATIVE_SOCKET; if(!request->responded) freak_http_error(request,503,"HTTP server closed"); }
    }
    server->in_use=false; freak_http_server_live--;
}

/* ── Wire parsing (llhttp callbacks; unchanged admission policy) ──────── */
static bool freak_http_valid_host(const unsigned char *value,size_t length) {
    if(!length || length>320) return false;
    size_t host_length=length,port_start=length;
    if(value[0]=='[') {
        size_t end=1; while(end<length && value[end]!=']') end++;
        if(end==length || end==1 || end>=128) return false;
        char address[128]; memcpy(address,value+1,end-1); address[end-1]=0; struct in6_addr parsed;
        if(inet_pton(AF_INET6,address,&parsed)!=1) return false;
        if(end+1<length) { if(value[end+1]!=':') return false; port_start=end+2; }
    } else {
        for(size_t i=0;i<length;i++) if(value[i]==':') { host_length=i; port_start=i+1; break; }
        if(!host_length || host_length>253) return false;
        size_t label=0;
        for(size_t i=0;i<host_length;i++) {
            unsigned char c=value[i];
            if(c=='.') { if(!label || value[i-1]=='-') return false; label=0; }
            else { if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='-'||c=='_') || (!label && c=='-') || ++label>63) return false; }
        }
        if(value[host_length-1]=='-') return false;
    }
    if(port_start<length) { unsigned port=0; for(size_t i=port_start;i<length;i++) { if(value[i]<'0'||value[i]>'9') return false; port=port*10+(value[i]-'0'); if(port>65535) return false; } if(!port) return false; }
    else if(port_start!=length || value[length-1]==':') return false;
    return true;
}
static void freak_http_trim(const freak_http_text *text,const unsigned char **bytes,size_t *length) {
    size_t begin=0,end=text->length; while(begin<end && (text->data[begin]==' '||text->data[begin]=='\t')) begin++;
    while(end>begin && (text->data[end-1]==' '||text->data[end-1]=='\t')) end--;
    *bytes=text->data?text->data+begin:NULL; *length=end-begin;
}
static int freak_http_on_method(llhttp_t *parser,const char *bytes,size_t length) {
    freak_http_request *request=parser->data;
    if(length>request->limits.line-request->method.length) { freak_http_error(request,414,"request line exceeds limit"); return -1; }
    freak_http_text_append(&request->method,bytes,length,request->limits.line); return 0;
}
static int freak_http_on_target(llhttp_t *parser,const char *bytes,size_t length) {
    freak_http_request *request=parser->data;
    if(length>request->limits.line-request->target.length) { freak_http_error(request,414,"request target exceeds limit"); return -1; }
    freak_http_text_append(&request->target,bytes,length,request->limits.line); return 0;
}
static int freak_http_on_field(llhttp_t *parser,const char *bytes,size_t length) {
    freak_http_request *request=parser->data;
    if(request->current_header<0) {
        if(request->header_count>=request->limits.count) { freak_http_error(request,431,"request has too many header fields"); return -1; }
        if(request->header_count==request->header_capacity) { size_t capacity=request->header_capacity?request->header_capacity*2:16; if(capacity>request->limits.count) capacity=request->limits.count; request->headers=freak_http_grow(request->headers,capacity*sizeof(*request->headers)); request->header_capacity=capacity; }
        request->current_header=(int)request->header_count++; request->headers[request->current_header].trailer=(parser->flags&F_TRAILING)!=0;
    }
    freak_http_text *name=&request->headers[request->current_header].name;
    if(length>request->limits.headers-name->length) { freak_http_error(request,431,"request header exceeds limit"); return -1; }
    freak_http_text_append(name,bytes,length,request->limits.headers);
    for(size_t i=name->length-length;i<name->length;i++) name->data[i]=freak_http_lower(name->data[i]); return 0;
}
static int freak_http_on_value(llhttp_t *parser,const char *bytes,size_t length) {
    freak_http_request *request=parser->data; if(request->current_header<0) { freak_http_error(request,400,"invalid header event"); return -1; }
    freak_http_text *value=&request->headers[request->current_header].value;
    if(length>request->limits.headers-value->length) { freak_http_error(request,431,"request header value exceeds limit"); return -1; }
    freak_http_text_append(value,bytes,length,request->limits.headers); return 0;
}
static bool freak_http_sensitive(const freak_http_text *name) {
    const char *blocked[]={"host","content-length","transfer-encoding","content-encoding","connection","expect","upgrade","authorization","proxy-authorization","cookie","trailer"};
    for(size_t i=0;i<sizeof(blocked)/sizeof(*blocked);i++) if(freak_http_equal(name->data,name->length,blocked[i])) return true; return false;
}
static int freak_http_on_value_complete(llhttp_t *parser) {
    freak_http_request *request=parser->data;
    if(request->current_header>=0) { freak_http_header *header=&request->headers[request->current_header]; if(header->trailer && freak_http_sensitive(&header->name)) { freak_http_error(request,400,"sensitive/framing trailer field is forbidden"); return -1; } }
    request->current_header=-1; return 0;
}
static int freak_http_on_headers(llhttp_t *parser) {
    freak_http_request *request=parser->data;
    if(parser->http_major!=1 || parser->http_minor>1) { freak_http_error(request,505,"HTTP version is unsupported"); return -1; }
    if(parser->method==HTTP_CONNECT || parser->upgrade || (parser->flags&F_UPGRADE)) { freak_http_error(request,501,"CONNECT and protocol upgrades are unsupported"); return -1; }
    if(!request->target.length || request->target.data[0]!='/') { freak_http_error(request,400,"only origin-form request targets are supported"); return -1; }
    for(size_t i=0;i<request->target.length;i++) {
        unsigned char c=request->target.data[i];
        if(c<33 || c>126 || c=='#' || (c=='%' && (i+2>=request->target.length || !freak_http_hex(request->target.data[i+1]) || !freak_http_hex(request->target.data[i+2])))) { freak_http_error(request,400,"invalid request target"); return -1; }
        if(c=='%') i+=2;
    }
    size_t hosts=0,lengths=0,transfers=0,expects=0;
    for(size_t i=0;i<request->header_count;i++) {
        freak_http_header *header=&request->headers[i]; const unsigned char *value; size_t length; freak_http_trim(&header->value,&value,&length);
        if(freak_http_equal(header->name.data,header->name.length,"host")) { hosts++; if(!freak_http_valid_host(value,length)) { freak_http_error(request,400,"invalid Host header"); return -1; } }
        if(freak_http_equal(header->name.data,header->name.length,"content-length")) lengths++;
        if(freak_http_equal(header->name.data,header->name.length,"transfer-encoding")) { transfers++; if(!freak_http_equal(value,length,"chunked")) { freak_http_error(request,501,"unsupported transfer coding"); return -1; } }
        if(freak_http_equal(header->name.data,header->name.length,"content-encoding") && !freak_http_equal(value,length,"identity")) { freak_http_error(request,501,"unsupported content coding"); return -1; }
        if(freak_http_equal(header->name.data,header->name.length,"expect")) { expects++; if(!freak_http_equal(value,length,"100-continue")) { freak_http_error(request,417,"unsupported expectation"); return -1; } request->expect_continue=true; }
    }
    if(hosts>1 || (parser->http_minor==1 && hosts!=1)) { freak_http_error(request,400,"HTTP/1.1 requires exactly one Host header"); return -1; }
    if(lengths>1 || transfers>1 || (lengths && transfers)) { freak_http_error(request,400,"ambiguous request framing"); return -1; }
    if(expects>1) { freak_http_error(request,417,"duplicate expectation"); return -1; }
    if((parser->flags&F_CONTENT_LENGTH) && parser->content_length>request->limits.body) { freak_http_error(request,413,"request body exceeds limit"); return -1; }
    request->headers_done=true; request->chunk_line=(parser->flags&F_CHUNKED)!=0; request->persistent=llhttp_should_keep_alive(parser)!=0; return 0;
}
static size_t freak_http_body_length(freak_http_request *request) { return request->body?freak_byte_buffer_require(request->body,"HTTP decoded body")->length:0; }
static int freak_http_on_body(llhttp_t *parser,const char *bytes,size_t length) {
    freak_http_request *request=parser->data;
    if(length>request->limits.body-freak_http_body_length(request)) { freak_http_error(request,413,"decoded request body exceeds limit"); return -1; }
    if(!request->body) request->body=freak_byte_buffer_new();
    freak_byte_buffer_append_bytes(freak_byte_buffer_require(request->body,"HTTP decoded body"),(const uint8_t *)bytes,length); return 0;
}
static int freak_http_on_chunk(llhttp_t *parser) {
    freak_http_request *request=parser->data;
    if(parser->content_length>request->limits.body-freak_http_body_length(request)) { freak_http_error(request,413,"chunk exceeds remaining request body limit"); return -1; }
    request->chunk_line=false; return 0;
}
static int freak_http_on_chunk_complete(llhttp_t *parser) { freak_http_request *request=parser->data; request->chunk_line=(parser->flags&F_TRAILING)==0; return 0; }
static int freak_http_on_complete(llhttp_t *parser) { freak_http_request *request=parser->data; request->message_done=true; request->persistent=request->persistent && llhttp_should_keep_alive(parser)!=0; return HPE_PAUSED; }

static const char *freak_http_reason(int status) {
    switch(status) { case 200:return "OK";case 201:return "Created";case 204:return "No Content";case 205:return "Reset Content";case 304:return "Not Modified";case 400:return "Bad Request";case 404:return "Not Found";case 405:return "Method Not Allowed";case 408:return "Request Timeout";case 413:return "Content Too Large";case 414:return "URI Too Long";case 417:return "Expectation Failed";case 431:return "Request Header Fields Too Large";case 500:return "Internal Server Error";case 501:return "Not Implemented";case 503:return "Service Unavailable";case 505:return "HTTP Version Not Supported";default:return "Response"; }
}

/* ── Connection I/O ───────────────────────────────────────────────────── */
static bool freak_http_would_block(void) {
#ifdef _WIN32
    return WSAGetLastError()==WSAEWOULDBLOCK;
#else
    return errno==EAGAIN || errno==EWOULDBLOCK;
#endif
}
static long freak_http_send_some(freak_native_socket socket,const unsigned char *data,size_t length) {
    size_t wanted=length>INT_MAX?INT_MAX:length;
    for(;;) {
#ifdef _WIN32
        int sent=send(socket,(const char *)data,(int)wanted,0);
#else
        ssize_t sent=send(socket,(const char *)data,wanted,freak_tcp_socket_send_flags());
#endif
        if(sent<0 && freak_tcp_socket_error_is_interrupted()) continue;
        if(sent<0 && freak_http_would_block()) return 0;
        if(sent<=0) return -1;
        return (long)sent;
    }
}
static long freak_http_recv_some(freak_native_socket socket,unsigned char *data,size_t length) {
    for(;;) {
#ifdef _WIN32
        int received=recv(socket,(char *)data,(int)length,0);
#else
        ssize_t received=recv(socket,data,length,0);
#endif
        if(received<0 && freak_tcp_socket_error_is_interrupted()) continue;
        if(received<0 && freak_http_would_block()) return -2;
        if(received<0) return -1;
        return (long)received;
    }
}
/* Write as much queued output as the socket takes. false: connection failed. */
static bool freak_http_flush(freak_http_conn *conn) {
    while(conn->out_offset<conn->out_length && conn->writable) {
        long sent=freak_http_send_some(conn->socket,conn->out+conn->out_offset,conn->out_length-conn->out_offset);
        if(sent<0) return false;
        if(sent==0) { conn->writable=false; break; }
        conn->out_offset+=(size_t)sent; conn->write_idle=freak_command_now_ms()+conn->server->limits.idle_ms;
    }
    if(conn->out_offset==conn->out_length) { conn->out_offset=conn->out_length=0; }
    return true;
}
static void freak_http_queue_out(freak_http_conn *conn,const void *bytes,size_t length) { freak_http_queue_append(&conn->out,&conn->out_length,&conn->out_offset,bytes,length); }
static void freak_http_begin_read(freak_http_conn *conn,uint64_t now) {
    conn->request=freak_http_new_request(conn->server,conn); conn->state=FREAK_HTTP_CONN_READ;
    conn->idle_deadline=now+(conn->served?conn->server->keep_alive_ms:conn->server->limits.idle_ms);
}
static void freak_http_reject(freak_http_conn *conn) {
    freak_http_server *server=conn->server; freak_http_request *request=conn->request;
    conn->request=NULL; request->conn=NULL; request->socket=FREAK_INVALID_NATIVE_SOCKET;
    freak_http_deliver(server,request);
    if(freak_http_stopping(server)) { freak_http_conn_destroy(conn); return; }
    const char *reason=freak_http_reason(request->status); char response[512];
    int size=snprintf(response,sizeof(response),"HTTP/1.1 %d %s\r\nContent-Length: %zu\r\nContent-Type: text/plain; charset=utf-8\r\nConnection: close\r\n\r\n%s%s",request->status,reason,strlen(reason)+1,request->head_method?"":reason,request->head_method?"":"\n");
    if(size<=0 || (size_t)size>=sizeof(response)) { freak_http_conn_destroy(conn); return; }
    conn->in_length=conn->in_offset=0;
    uint64_t now=freak_command_now_ms();
    freak_http_queue_out(conn,response,(size_t)size); conn->close_after_write=true; conn->drain_after_write=true;
    conn->state=FREAK_HTTP_CONN_WRITE; conn->write_deadline=now+request->limits.idle_ms; conn->write_idle=now+request->limits.idle_ms;
}
/* Feed bytes one at a time so every wire budget is exact. Returns consumed. */
static size_t freak_http_feed(freak_http_conn *conn,const unsigned char *bytes,size_t length,uint64_t tick) {
    freak_http_request *request=conn->request;
    if(!request->started) { request->started=true; request->header_deadline=tick+request->limits.header_ms; }
    request->idle_deadline=tick+request->limits.idle_ms;
    size_t i=0;
    for(;i<length && !request->status && !request->message_done;i++) {
        if(tick>=(request->headers_done?request->body_deadline:request->header_deadline)) { freak_http_error(request,408,"absolute HTTP request deadline exceeded"); break; }
        size_t raw_limit=request->limits.body*16+request->limits.line+request->limits.headers+request->limits.chunk_metadata+request->limits.trailers;
        if(++request->raw_wire>raw_limit) { freak_http_error(request,413,"raw HTTP request exceeds framing budget"); break; }
        bool was_headers=request->headers_done;
        if(!was_headers) {
            if(!request->line_done) { if(++request->line_wire>request->limits.line) { freak_http_error(request,414,"request line exceeds limit"); break; } }
            else if(++request->header_wire>request->limits.headers) { freak_http_error(request,431,"request headers exceed limit"); break; }
        } else if(request->parser.flags&F_TRAILING) {
            if(++request->trailer_wire>request->limits.trailers) { freak_http_error(request,431,"request trailers exceed limit"); break; }
        } else if(request->chunk_line && ++request->chunk_wire>request->limits.chunk_metadata) { freak_http_error(request,413,"chunk framing/extensions exceed metadata limit"); break; }
        llhttp_errno_t parsed=llhttp_execute(&request->parser,(const char *)bytes+i,1);
        if(parsed!=HPE_OK && !(parsed==HPE_PAUSED && request->message_done)) { if(!request->status) freak_http_error(request,400,"malformed HTTP request framing"); break; }
        /* llhttp can recognize HEAD before its token ends. Only an accepted
           space confirms the method for a later parse/deadline rejection. */
        if(bytes[i]==' ' && llhttp_get_method(&request->parser)==HTTP_HEAD) request->head_method=true;
        if(!request->line_done && bytes[i]=='\n') request->line_done=true;
        if(!was_headers && request->headers_done) {
            request->body_deadline=tick+request->limits.body_ms;
            if(request->expect_continue && !request->message_done && ((request->parser.flags&F_CHUNKED)||request->parser.content_length)) {
                static const char interim[]="HTTP/1.1 100 Continue\r\n\r\n";
                freak_http_queue_out(conn,interim,sizeof(interim)-1);
            }
        }
    }
    return i;
}
static void freak_http_conclude(freak_http_conn *conn) {
    freak_http_request *request=conn->request;
    if(request->status) freak_http_reject(conn);
    else if(request->message_done) { conn->state=FREAK_HTTP_CONN_QUEUED; freak_http_deliver(conn->server,request); }
}
static void freak_http_after_write(freak_http_conn *conn,uint64_t now) {
    if(!conn->close_after_write) { conn->served++; freak_http_begin_read(conn,now); return; }
    if(conn->drain_after_write && !freak_http_stopping(conn->server)) {
#ifdef _WIN32
        if(shutdown(conn->socket,SD_SEND)!=0) { freak_http_conn_destroy(conn); return; }
#else
        if(shutdown(conn->socket,SHUT_WR)!=0) { freak_http_conn_destroy(conn); return; }
#endif
        /* Flush the complete reply before closing with unread trickle input.
           A peer cannot extend this fixed grace period or the discard budget. */
        uint64_t grace=conn->server->limits.idle_ms<50?conn->server->limits.idle_ms:50;
        conn->state=FREAK_HTTP_CONN_DRAIN; conn->drain_deadline=now+grace; conn->drained=0; return;
    }
    freak_http_conn_destroy(conn);
}
static void freak_http_mark_hot(freak_http_conn *conn) {
    if(conn->hot || conn->dead) return; conn->hot=true; conn->hot_next=conn->server->hot; conn->server->hot=conn;
}
static void freak_http_service(freak_http_conn *conn) {
    int round=0;
    for(;round<64 && !conn->dead;round++) {
        if(conn->out_offset<conn->out_length && conn->writable && !freak_http_flush(conn)) { freak_http_conn_destroy(conn); return; }
        uint64_t now=freak_command_now_ms();
        switch(conn->state) {
        case FREAK_HTTP_CONN_WRITE:
            if(conn->out_offset<conn->out_length) return;
            freak_http_after_write(conn,now); continue;
        case FREAK_HTTP_CONN_READ: {
            if(conn->in_offset<conn->in_length) {
                size_t used=freak_http_feed(conn,conn->in+conn->in_offset,conn->in_length-conn->in_offset,now);
                conn->in_offset+=used; if(conn->in_offset==conn->in_length) conn->in_offset=conn->in_length=0;
                if(conn->request->status || conn->request->message_done) { freak_http_conclude(conn); continue; }
            }
            if(!conn->readable) return;
            long received=freak_http_recv_some(conn->socket,freak_http_scratch,sizeof(freak_http_scratch));
            if(received==-2) { conn->readable=false; return; }
            if(received<=0) {
                conn->readable=false;
                if(!conn->request->started) { freak_http_conn_destroy(conn); return; }
                freak_http_error(conn->request,400,received==0?"incomplete HTTP request or reset peer":"HTTP socket read failed");
                freak_http_conclude(conn); continue;
            }
            size_t used=freak_http_feed(conn,freak_http_scratch,(size_t)received,now);
            if(used<(size_t)received && !conn->request->status) freak_http_queue_append(&conn->in,&conn->in_length,&conn->in_offset,freak_http_scratch+used,(size_t)received-used);
            if(conn->request->status || conn->request->message_done) freak_http_conclude(conn);
            continue;
        }
        case FREAK_HTTP_CONN_DRAIN: {
            if(!conn->readable) return;
            size_t wanted=65536-conn->drained; if(wanted>sizeof(freak_http_scratch)) wanted=sizeof(freak_http_scratch);
            long received=freak_http_recv_some(conn->socket,freak_http_scratch,wanted);
            if(received==-2) { conn->readable=false; return; }
            if(received<=0) { freak_http_conn_destroy(conn); return; }
            conn->drained+=(size_t)received; if(conn->drained>=65536) { freak_http_conn_destroy(conn); return; }
            continue;
        }
        default: return; /* QUEUED/APP: the application's turn */
        }
    }
    /* Out of budget with an edge still pending: revisit without waiting. */
    if(!conn->dead) freak_http_mark_hot(conn);
}
static void freak_http_accept(freak_http_server *server) {
    for(int accepted=0;accepted<64;accepted++) {
        if(server->conn_count>=server->max_connections) { freak_http_listener_arm(server,false); return; }
#if defined(__linux__)
        freak_native_socket socket_value=accept4(server->listener,NULL,NULL,SOCK_NONBLOCK|SOCK_CLOEXEC);
#else
        freak_native_socket socket_value=accept(server->listener,NULL,NULL);
#endif
        if(socket_value==FREAK_INVALID_NATIVE_SOCKET) {
            if(freak_tcp_socket_error_is_interrupted()) continue;
            if(freak_http_would_block()) return;
#ifndef _WIN32
            if(errno==ECONNABORTED || errno==EPROTO) continue;
#else
            if(WSAGetLastError()==WSAECONNRESET) continue;
#endif
            /* Out of descriptors or memory: back off instead of spinning. */
            freak_http_listener_arm(server,false); server->accept_pause_until=freak_command_now_ms()+50; return;
        }
        freak_http_socket_live++;
        freak_tcp_socket_configure_no_sigpipe(socket_value);
#if defined(__linux__)
        bool configured=true;
#else
        bool configured=freak_http_nonblocking(socket_value);
#endif
        int enabled=1; setsockopt(socket_value,IPPROTO_TCP,TCP_NODELAY,(const char *)&enabled,sizeof(enabled));
        if(!configured) { freak_http_close_socket(&socket_value); continue; }
        freak_http_conn *conn=freak_http_allocate(sizeof(freak_http_conn));
        conn->socket=socket_value; conn->server=server; conn->readable=true; conn->writable=true;
        if(server->conn_count==server->conn_capacity) { size_t next=server->conn_capacity?server->conn_capacity*2:64; server->conns=freak_http_grow(server->conns,next*sizeof(*server->conns)); server->conn_capacity=next; }
        conn->index=server->conn_count; server->conns[server->conn_count++]=conn; freak_http_connection_live++;
        freak_http_begin_read(conn,freak_command_now_ms());
        if(!freak_http_poller_add(conn)) { freak_http_conn_destroy(conn); continue; }
        freak_http_service(conn);
    }
}
static void freak_http_sweep(freak_http_server *server,uint64_t now) {
    for(size_t i=server->conn_count;i>0;i--) {
        freak_http_conn *conn=server->conns[i-1];
        switch(conn->state) {
        case FREAK_HTTP_CONN_READ: {
            freak_http_request *request=conn->request;
            if(!request->started) { if(now>=conn->idle_deadline) freak_http_conn_destroy(conn); break; }
            uint64_t deadline=request->headers_done?request->body_deadline:request->header_deadline;
            if(now>=deadline || now>=request->idle_deadline) {
                freak_http_error(request,408,"HTTP request deadline exceeded"); freak_http_reject(conn); if(!conn->dead) freak_http_service(conn);
            }
            break;
        }
        case FREAK_HTTP_CONN_WRITE: if(now>=conn->write_deadline || now>=conn->write_idle) freak_http_conn_destroy(conn); break;
        case FREAK_HTTP_CONN_DRAIN: if(now>=conn->drain_deadline) freak_http_conn_destroy(conn); break;
        default: break;
        }
    }
    if(!server->listener_armed && now>=server->accept_pause_until && server->conn_count<server->max_connections) freak_http_listener_arm(server,true);
    freak_http_supervise(server,now);
}
/* One wait for readiness plus the resulting work. false: the poller failed. */
static bool freak_http_poll_once(freak_http_server *server) {
    uint64_t now=freak_command_now_ms();
    int timeout=server->conn_count?FREAK_HTTP_SWEEP_MS:50;
    if(server->ready_head || server->hot) timeout=0;
#if defined(FREAK_HTTP_EPOLL)
    struct epoll_event events[FREAK_HTTP_EVENTS];
    int ready=epoll_wait(server->poller,events,FREAK_HTTP_EVENTS,timeout);
    if(ready<0 && errno!=EINTR) return false;
    for(int i=0;i<ready;i++) {
        freak_http_conn *conn=events[i].data.ptr;
        if(!conn) { freak_http_accept(server); continue; }
        if(conn->dead) continue;
        if(events[i].events&(EPOLLIN|EPOLLRDHUP|EPOLLHUP|EPOLLERR)) conn->readable=true;
        if(events[i].events&(EPOLLOUT|EPOLLHUP|EPOLLERR)) conn->writable=true;
        freak_http_service(conn);
    }
#elif defined(FREAK_HTTP_KQUEUE)
    struct kevent events[FREAK_HTTP_EVENTS]; struct timespec wait={timeout/1000,(long)(timeout%1000)*1000000L};
    int ready=kevent(server->poller,NULL,0,events,FREAK_HTTP_EVENTS,&wait);
    if(ready<0 && errno!=EINTR) return false;
    for(int i=0;i<ready;i++) {
        freak_http_conn *conn=events[i].udata;
        if(!conn) { if(events[i].filter==EVFILT_READ) freak_http_accept(server); continue; }
        if(conn->dead) continue;
        if(events[i].filter==EVFILT_READ) conn->readable=true;
        if(events[i].filter==EVFILT_WRITE) conn->writable=true;
        if(events[i].flags&(EV_EOF|EV_ERROR)) { conn->readable=true; conn->writable=true; }
    }
    for(int i=0;i<ready;i++) { freak_http_conn *conn=events[i].udata; if(conn && !conn->dead) freak_http_service(conn); }
#else
    /* Level-triggered (WSA)poll emulates the edges: ask only for readiness a
       connection is waiting on. */
    size_t capacity=server->conn_count+1;
#ifdef _WIN32
    WSAPOLLFD *descriptors=freak_http_allocate(capacity*sizeof(WSAPOLLFD));
#else
    struct pollfd *descriptors=freak_http_allocate(capacity*sizeof(struct pollfd));
#endif
    freak_http_conn **owners=freak_http_allocate(capacity*sizeof(freak_http_conn *)); size_t count=0;
    if(server->listener_armed) { descriptors[count].fd=server->listener; descriptors[count].events=FREAK_HTTP_POLL_IN; owners[count++]=NULL; }
    for(size_t i=0;i<server->conn_count;i++) {
        freak_http_conn *conn=server->conns[i]; short events=0;
        if((conn->state==FREAK_HTTP_CONN_READ || conn->state==FREAK_HTTP_CONN_DRAIN) && !conn->readable) events|=FREAK_HTTP_POLL_IN;
        if(conn->out_offset<conn->out_length && !conn->writable) events|=FREAK_HTTP_POLL_OUT;
        if(!events) continue;
        descriptors[count].fd=conn->socket; descriptors[count].events=events; descriptors[count].revents=0; owners[count++]=conn;
    }
    int ready;
#ifdef _WIN32
    if(!count) { Sleep((DWORD)timeout); ready=0; }
    else ready=WSAPoll(descriptors,(ULONG)count,timeout);
    if(ready<0 && WSAGetLastError()!=WSAEINTR) { freak_http_free(descriptors); freak_http_free(owners); return false; }
#else
    ready=poll(descriptors,(nfds_t)count,timeout);
    if(ready<0 && errno!=EINTR) { freak_http_free(descriptors); freak_http_free(owners); return false; }
#endif
    for(size_t i=0;ready>0 && i<count;i++) {
        short revents=descriptors[i].revents; if(!revents) continue;
        freak_http_conn *conn=owners[i];
        if(!conn) { freak_http_accept(server); continue; }
        if(conn->dead) continue;
        if(revents&(FREAK_HTTP_POLL_IN|POLLHUP|POLLERR)) conn->readable=true;
        if(revents&(FREAK_HTTP_POLL_OUT|POLLHUP|POLLERR)) conn->writable=true;
        freak_http_service(conn);
    }
    freak_http_free(descriptors); freak_http_free(owners);
#endif
    freak_http_conn *hot=server->hot; server->hot=NULL;
    while(hot) { freak_http_conn *conn=hot; hot=conn->hot_next; conn->hot=false; if(!conn->dead) freak_http_service(conn); }
    now=freak_command_now_ms();
    if(now>=server->next_sweep) { server->next_sweep=now+FREAK_HTTP_SWEEP_MS; freak_http_sweep(server,now); }
    freak_http_bury(server);
    return true;
}
int64_t freak_http_server_next_request(int64_t server_ticket) {
    freak_http_server *server=freak_http_require_server(server_ticket); if(server->active) freak_http_fail("release the active request before accepting another");
    bool usable=!server->status && !freak_http_stopping(server);
    if(usable && !server->started && !freak_http_start(server)) { freak_http_request *failed=freak_http_new_request(server,NULL); int64_t ticket=freak_http_ticket_for(failed); server->active=ticket; freak_http_error(failed,500,"could not wait for HTTP connection"); return ticket; }
    for(;;) {
        if(server->status || freak_http_stopping(server)) {
            freak_http_request *failed=freak_http_new_request(server,NULL); int64_t ticket=freak_http_ticket_for(failed); server->active=ticket;
            freak_http_error(failed,503,server->status?"HTTP server is stopped or failed":"HTTP server stopped"); return ticket;
        }
        if(server->ready_head) {
            freak_http_request *request=server->ready_head; server->ready_head=request->ready_next; if(!server->ready_head) server->ready_tail=NULL;
            int64_t ticket=freak_http_ticket_for(request); server->active=ticket;
            if(request->conn) { request->conn->state=FREAK_HTTP_CONN_APP; request->socket=request->conn->socket; }
            return ticket;
        }
        if(!freak_http_poll_once(server)) {
            freak_http_request *failed=freak_http_new_request(server,NULL); int64_t ticket=freak_http_ticket_for(failed); server->active=ticket;
            freak_http_error(failed,500,"could not wait for HTTP connection"); return ticket;
        }
    }
}

int64_t freak_http_server_request_status(int64_t ticket) { return freak_http_require_request(ticket)->status; }
freak_word freak_http_server_request_error(int64_t ticket) { return freak_word_copy_cstr(freak_http_require_request(ticket)->error); }
static freak_http_request *freak_http_parsed(int64_t ticket) { freak_http_request *request=freak_http_require_request(ticket); if(!request->message_done || request->status) freak_http_fail("request metadata requires a successfully parsed request"); return request; }
freak_word freak_http_server_request_method(int64_t ticket) { freak_http_request *request=freak_http_parsed(ticket); return freak_http_word(request->method.data,request->method.length); }
freak_word freak_http_server_request_target(int64_t ticket) { freak_http_request *request=freak_http_parsed(ticket); return freak_http_word(request->target.data,request->target.length); }
freak_word freak_http_server_request_path(int64_t ticket) { freak_http_request *request=freak_http_parsed(ticket); size_t end=0; while(end<request->target.length && request->target.data[end]!='?') end++; return freak_http_word(request->target.data,end); }
freak_word freak_http_server_request_query(int64_t ticket) { freak_http_request *request=freak_http_parsed(ticket); size_t begin=0; while(begin<request->target.length && request->target.data[begin]!='?') begin++; if(begin<request->target.length) begin++; return freak_http_word(request->target.data+begin,request->target.length-begin); }
int64_t freak_http_server_request_header_count(int64_t ticket) { return (int64_t)freak_http_parsed(ticket)->header_count; }
static freak_http_header *freak_http_header_at(int64_t ticket,int64_t index) { freak_http_request *request=freak_http_parsed(ticket); if(index<0 || (uint64_t)index>=request->header_count) freak_http_fail("request header index out of bounds"); return &request->headers[index]; }
freak_word freak_http_server_request_header_name(int64_t ticket,int64_t index) { freak_http_header *header=freak_http_header_at(ticket,index); return freak_http_word(header->name.data,header->name.length); }
freak_word freak_http_server_request_header_value(int64_t ticket,int64_t index) { freak_http_header *header=freak_http_header_at(ticket,index); return freak_http_word(header->value.data,header->value.length); }
int64_t freak_http_server_request_header_value_bytes(int64_t ticket,int64_t index) { freak_http_header *header=freak_http_header_at(ticket,index); return freak_http_bytes(header->value.data,header->value.length); }
int64_t freak_http_server_request_header_is_trailer(int64_t ticket,int64_t index) { return freak_http_header_at(ticket,index)->trailer?1:0; }
int64_t freak_http_server_request_header_find(int64_t ticket,freak_word name,int64_t start) {
    freak_http_request *request=freak_http_parsed(ticket); if(start<0 || name.length>request->limits.headers || (name.length&&!name.data)) freak_http_fail("invalid request header lookup");
    for(size_t i=(size_t)start;i<request->header_count;i++) { freak_http_text *candidate=&request->headers[i].name; if(candidate->length!=name.length) continue; bool match=true; for(size_t j=0;j<name.length;j++) if(candidate->data[j]!=freak_http_lower((unsigned char)name.data[j])) { match=false; break; } if(match) return (int64_t)i; } return -1;
}
int64_t freak_http_server_request_body(int64_t ticket) { freak_http_request *request=freak_http_parsed(ticket); freak_byte_buffer_record *body=freak_byte_buffer_require(request->body,"HTTP body getter"); const unsigned char *data=body->data; size_t length=body->length; return freak_http_bytes(data,length); }
static bool freak_http_respondable(freak_http_request *request) { if(!request->message_done || request->status || request->responded || !request->conn) { snprintf(request->error,sizeof(request->error),"request cannot receive another response"); return false; } return true; }
int64_t freak_http_server_response_status(int64_t ticket,int64_t status) { freak_http_request *request=freak_http_require_request(ticket); if(!freak_http_respondable(request) || status<200 || status>599) { snprintf(request->error,sizeof(request->error),"response status must be 200 through 599"); return 0; } request->response_status=(int)status; return 1; }
int64_t freak_http_server_response_header(int64_t ticket,freak_word name,freak_word value) {
    freak_http_request *request=freak_http_require_request(ticket); if(!freak_http_respondable(request)) return 0;
    if(!name.length || !name.data || name.length>127 || (value.length&&!value.data) || value.length>request->limits.headers) goto invalid;
    for(size_t i=0;i<name.length;i++) if(!freak_http_token((unsigned char)name.data[i])) goto invalid;
    for(size_t i=0;i<value.length;i++) if((unsigned char)value.data[i]<32 && value.data[i]!='\t' || (unsigned char)value.data[i]==127) goto invalid;
    const char *blocked[]={"content-length","transfer-encoding","connection","trailer","upgrade","keep-alive","proxy-connection"};
    for(size_t i=0;i<sizeof(blocked)/sizeof(*blocked);i++) if(freak_http_equal((const unsigned char *)name.data,name.length,blocked[i])) goto invalid;
    if(request->response_count>=request->limits.count || name.length+value.length+4>request->limits.headers-request->response_wire) goto invalid;
    if(request->response_count==request->response_capacity) { size_t capacity=request->response_capacity?request->response_capacity*2:16; if(capacity>request->limits.count) capacity=request->limits.count; request->response_headers=freak_http_grow(request->response_headers,capacity*sizeof(*request->response_headers)); request->response_capacity=capacity; }
    freak_http_header *header=&request->response_headers[request->response_count++];
    freak_http_text_append(&header->name,name.data,name.length,request->limits.headers); freak_http_text_append(&header->value,value.data,value.length,request->limits.headers);
    request->response_wire+=name.length+value.length+4; return 1;
invalid:
    snprintf(request->error,sizeof(request->error),"invalid, framing-owned, or oversized response header"); return 0;
}
/* Queue the response and write what the socket takes now; the event loop
   finishes the rest while the application handles the next request.
   1 means the complete response was accepted for delivery. */
static int64_t freak_http_send(freak_http_request *request,const unsigned char *body,size_t length,const char *type) {
    if(!freak_http_respondable(request)) return 0;
    if(request->response_status!=205 && length>request->limits.body) { snprintf(request->error,sizeof(request->error),"response body exceeds configured limit"); return 0; }
    freak_http_conn *conn=request->conn; freak_http_server *server=conn->server;
    bool keep=server->keep_alive_requests>0 && request->persistent && conn->served+1<server->keep_alive_requests && !freak_http_stopping(server);
    freak_http_text wire={0}; char first[256]; size_t limit=request->limits.headers+1024;
    int count=snprintf(first,sizeof(first),"HTTP/1.1 %d %s\r\nConnection: %s\r\n",request->response_status,freak_http_reason(request->response_status),keep?"keep-alive":"close");
    freak_http_text_append(&wire,first,(size_t)count,limit);
    if(request->response_status!=204) { count=snprintf(first,sizeof(first),"Content-Length: %zu\r\n",request->response_status==205?0:length); freak_http_text_append(&wire,first,(size_t)count,limit); }
    bool content_type=false;
    for(size_t i=0;i<request->response_count;i++) {
        freak_http_header *header=&request->response_headers[i]; if(freak_http_equal(header->name.data,header->name.length,"content-type")) content_type=true;
        freak_http_text_append(&wire,header->name.data,header->name.length,limit); freak_http_text_append(&wire,": ",2,limit);
        freak_http_text_append(&wire,header->value.data,header->value.length,limit); freak_http_text_append(&wire,"\r\n",2,limit);
    }
    if(!content_type) { freak_http_text_append(&wire,"Content-Type: ",14,limit); freak_http_text_append(&wire,type,strlen(type),limit); freak_http_text_append(&wire,"\r\n",2,limit); }
    freak_http_text_append(&wire,"\r\n",2,limit);
    bool omit=request->response_status==204 || request->response_status==205 || request->response_status==304 || freak_http_equal(request->method.data,request->method.length,"head");
    if(omit) length=0;
    request->responded=true; conn->request=NULL; request->conn=NULL; request->socket=FREAK_INVALID_NATIVE_SOCKET;
    uint64_t now=freak_command_now_ms();
    conn->state=FREAK_HTTP_CONN_WRITE; conn->close_after_write=!keep; conn->drain_after_write=false;
    conn->write_deadline=now+request->limits.body_ms; conn->write_idle=now+request->limits.idle_ms;
    /* Small bodies travel in the header's segment; large ones are written in
       place and only their unsent tail is copied. */
    bool failed=false;
    if(length<=16384) { freak_http_queue_out(conn,wire.data,wire.length); if(length) freak_http_queue_out(conn,body,length); failed=!freak_http_flush(conn); }
    else {
        freak_http_queue_out(conn,wire.data,wire.length); failed=!freak_http_flush(conn);
        size_t offset=0;
        while(!failed && conn->out_offset==conn->out_length && conn->writable && offset<length) {
            long sent=freak_http_send_some(conn->socket,body+offset,length-offset);
            if(sent<0) failed=true; else if(sent==0) conn->writable=false; else offset+=(size_t)sent;
        }
        if(!failed && offset<length) freak_http_queue_out(conn,body+offset,length-offset);
    }
    freak_http_free(wire.data);
    if(failed) { freak_http_conn_destroy(conn); freak_http_bury(server); snprintf(request->error,sizeof(request->error),"could not send complete HTTP response"); return 0; }
    freak_http_service(conn); freak_http_bury(server);
    return 1;
}
int64_t freak_http_server_send_bytes(int64_t ticket,int64_t body_ticket) { freak_http_request *request=freak_http_require_request(ticket); freak_byte_buffer_record *body=freak_byte_buffer_require(body_ticket,"HTTP response body"); if(body->status!=FREAK_BYTE_BUFFER_OK) { snprintf(request->error,sizeof(request->error),"response ByteBuffer has a pending error"); return 0; } return freak_http_send(request,body->data,body->length,"application/octet-stream"); }
int64_t freak_http_server_send_text(int64_t ticket,freak_word body) { freak_http_request *request=freak_http_require_request(ticket); if(!freak_byte_buffer_utf8_valid((const uint8_t *)body.data,body.length)) { snprintf(request->error,sizeof(request->error),"text response requires NUL-free UTF-8"); return 0; } return freak_http_send(request,(const unsigned char *)body.data,body.length,"text/plain; charset=utf-8"); }
void freak_http_server_request_release(int64_t ticket) {
    freak_http_request *request=freak_http_require_request(ticket);
    freak_http_server *server=freak_http_find_server(request->server);
    if(server && server->active==ticket) server->active=0;
    /* Released without a response: the connection cannot be reused. */
    if(request->conn) { freak_http_conn *conn=request->conn; conn->request=NULL; request->conn=NULL; freak_http_conn_destroy(conn); if(server) freak_http_bury(server); }
    freak_http_free_request(request);
}
int64_t freak_http_server_live_servers(void) { return (int64_t)freak_http_server_live; }
int64_t freak_http_server_live_requests(void) { return (int64_t)freak_http_request_live; }
int64_t freak_http_server_live_sockets(void) { return (int64_t)freak_http_socket_live; }
int64_t freak_http_server_live_connections(void) { return (int64_t)freak_http_connection_live; }
int64_t freak_http_server_retained_bytes(void) {
    uint64_t bytes=freak_http_owned_bytes;
    for(size_t i=0;i<freak_http_request_slots;i++) if(freak_http_requests[i].request && freak_http_requests[i].request->body) bytes+=freak_byte_buffer_require(freak_http_requests[i].request->body,"HTTP retained-byte count")->capacity;
    if(bytes>INT64_MAX) freak_http_fail("retained-byte counter overflow"); return (int64_t)bytes;
}

/* Scalar LLVM adapters share every parser/socket/owner path above. */
int64_t freak_llvm_http_server_open(int64_t port) { return freak_http_server_open(port); }
int64_t freak_llvm_http_server_bind(int64_t address, int64_t port, int64_t allow_non_loopback) { return freak_http_server_bind(freak_llvm_word_view(address), port, allow_non_loopback); }
int64_t freak_llvm_http_server_status(int64_t server) { return freak_http_server_status(server); }
int64_t freak_llvm_http_server_error(int64_t server) { return freak_llvm_word_take(freak_http_server_error(server)); }
int64_t freak_llvm_http_server_local_port(int64_t server) { return freak_http_server_local_port(server); }
void freak_llvm_http_server_set_limits(int64_t server, int64_t line_bytes, int64_t header_bytes, int64_t header_count, int64_t body_bytes) { freak_http_server_set_limits(server, line_bytes, header_bytes, header_count, body_bytes); }
void freak_llvm_http_server_set_timeouts(int64_t server, int64_t header_ms, int64_t body_ms, int64_t idle_ms) { freak_http_server_set_timeouts(server, header_ms, body_ms, idle_ms); }
void freak_llvm_http_server_set_chunk_limits(int64_t server, int64_t chunk_metadata_bytes, int64_t trailer_bytes) { freak_http_server_set_chunk_limits(server, chunk_metadata_bytes, trailer_bytes); }
void freak_llvm_http_server_set_keep_alive(int64_t server, int64_t idle_ms, int64_t max_requests) { freak_http_server_set_keep_alive(server, idle_ms, max_requests); }
void freak_llvm_http_server_set_max_connections(int64_t server, int64_t count) { freak_http_server_set_max_connections(server, count); }
void freak_llvm_http_server_set_workers(int64_t server, int64_t count) { freak_http_server_set_workers(server, count); }
int64_t freak_llvm_http_server_worker_index(int64_t server) { return freak_http_server_worker_index(server); }
void freak_llvm_http_server_stop(int64_t server) { freak_http_server_stop(server); }
void freak_llvm_http_server_close(int64_t server) { freak_http_server_close(server); }
int64_t freak_llvm_http_server_next_request(int64_t server) { return freak_http_server_next_request(server); }
int64_t freak_llvm_http_server_request_status(int64_t request) { return freak_http_server_request_status(request); }
int64_t freak_llvm_http_server_request_error(int64_t request) { return freak_llvm_word_take(freak_http_server_request_error(request)); }
int64_t freak_llvm_http_server_request_method(int64_t request) { return freak_llvm_word_take(freak_http_server_request_method(request)); }
int64_t freak_llvm_http_server_request_target(int64_t request) { return freak_llvm_word_take(freak_http_server_request_target(request)); }
int64_t freak_llvm_http_server_request_path(int64_t request) { return freak_llvm_word_take(freak_http_server_request_path(request)); }
int64_t freak_llvm_http_server_request_query(int64_t request) { return freak_llvm_word_take(freak_http_server_request_query(request)); }
int64_t freak_llvm_http_server_request_header_count(int64_t request) { return freak_http_server_request_header_count(request); }
int64_t freak_llvm_http_server_request_header_name(int64_t request, int64_t index) { return freak_llvm_word_take(freak_http_server_request_header_name(request, index)); }
int64_t freak_llvm_http_server_request_header_value(int64_t request, int64_t index) { return freak_llvm_word_take(freak_http_server_request_header_value(request, index)); }
int64_t freak_llvm_http_server_request_header_value_bytes(int64_t request, int64_t index) { return freak_http_server_request_header_value_bytes(request, index); }
int64_t freak_llvm_http_server_request_header_is_trailer(int64_t request, int64_t index) { return freak_http_server_request_header_is_trailer(request, index); }
int64_t freak_llvm_http_server_request_header_find(int64_t request, int64_t name, int64_t start) { return freak_http_server_request_header_find(request, freak_llvm_word_view(name), start); }
int64_t freak_llvm_http_server_request_body(int64_t request) { return freak_http_server_request_body(request); }
int64_t freak_llvm_http_server_response_status(int64_t request, int64_t status) { return freak_http_server_response_status(request, status); }
int64_t freak_llvm_http_server_response_header(int64_t request, int64_t name, int64_t value) { return freak_http_server_response_header(request, freak_llvm_word_view(name), freak_llvm_word_view(value)); }
int64_t freak_llvm_http_server_send_bytes(int64_t request, int64_t body) { return freak_http_server_send_bytes(request, body); }
int64_t freak_llvm_http_server_send_text(int64_t request, int64_t body) { return freak_http_server_send_text(request, freak_llvm_word_view(body)); }
void freak_llvm_http_server_request_release(int64_t request) { freak_http_server_request_release(request); }
int64_t freak_llvm_http_server_live_servers(void) { return freak_http_server_live_servers(); }
int64_t freak_llvm_http_server_live_requests(void) { return freak_http_server_live_requests(); }
int64_t freak_llvm_http_server_live_sockets(void) { return freak_http_server_live_sockets(); }
int64_t freak_llvm_http_server_retained_bytes(void) { return freak_http_server_retained_bytes(); }

#endif
