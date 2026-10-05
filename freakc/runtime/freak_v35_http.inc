#ifndef FREAK_V35_HTTP_INCLUDED
#define FREAK_V35_HTTP_INCLUDED 1
/* Synchronous, bounded HTTP/1 request transport. Routing belongs to the
   application. Included after the shared ByteBuffer/socket/word substrate. */
#if __has_include("third_party/llhttp/freak_amalgamation.inc")
#include "third_party/llhttp/freak_amalgamation.inc"
#else
#include "../../third_party/llhttp/freak_amalgamation.inc"
#endif
#ifndef _WIN32
#include <arpa/inet.h>
#include <netinet/in.h>
#endif

#define FREAK_HTTP_SERVER_DOMAIN UINT64_C(0x9000000000000000)
#define FREAK_HTTP_REQUEST_DOMAIN UINT64_C(0xb000000000000000)
#define FREAK_HTTP_DOMAIN_MASK UINT64_C(0xf000000000000000)
#define FREAK_HTTP_GENERATION_MAX UINT32_C(0x0fffffff)
typedef struct { size_t line,headers,count,body,chunk_metadata,trailers; uint64_t header_ms,body_ms,idle_ms; } freak_http_limits;
typedef struct { unsigned char *data; size_t length,capacity; } freak_http_text;
typedef struct { freak_http_text name,value; bool trailer; } freak_http_header;
typedef struct {
    uint32_t generation;
    bool in_use;
    atomic_bool stopping;
    freak_native_socket listener;
    int status,port;
    int64_t active;
    freak_http_limits limits;
    char error[192];
} freak_http_server;
typedef struct {
    uint32_t generation;
    bool in_use,headers_done,message_done,line_done,chunk_line,expect_continue,responded;
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
    llhttp_settings_t settings;
    char error[192];
} freak_http_request;
typedef union { max_align_t alignment; struct { size_t size; } metadata; } freak_http_allocation;
static size_t freak_http_owned_bytes, freak_http_server_live, freak_http_request_live, freak_http_socket_live;
static freak_http_server **freak_http_servers;
static freak_http_request **freak_http_requests;
static size_t freak_http_server_slots,freak_http_server_capacity,freak_http_request_slots,freak_http_request_capacity;
static bool freak_http_cleanup_registered;

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
static void *freak_http_grow(void *pointer,size_t size) {
    void *grown=freak_http_allocate(size);
    if(pointer) { size_t old=((freak_http_allocation *)pointer-1)->metadata.size; memcpy(grown,pointer,old<size?old:size); freak_http_free(pointer); }
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
    freak_http_request *request=freak_http_requests[slot-1];
    if(!request->in_use || request->generation!=generation) freak_http_fail("invalid or stale request ticket"); return request;
}
static freak_http_server *freak_http_find_server(int64_t ticket) {
    uint64_t bits=(uint64_t)ticket; uint32_t slot=(uint32_t)bits;
    if((bits&FREAK_HTTP_DOMAIN_MASK)!=FREAK_HTTP_SERVER_DOMAIN || !slot || slot>freak_http_server_slots) return NULL;
    freak_http_server *server=freak_http_servers[slot-1];
    return server->in_use && server->generation==((bits>>32)&FREAK_HTTP_GENERATION_MAX) ? server : NULL;
}
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
static void freak_http_dispose_request(freak_http_request *request) {
    freak_http_close_socket(&request->socket);
    freak_http_server *server=freak_http_find_server(request->server);
    if(server) server->active=0;
    freak_http_free(request->method.data); freak_http_free(request->target.data);
    freak_http_release_headers(request->headers,request->header_count);
    freak_http_release_headers(request->response_headers,request->response_count);
    freak_byte_buffer_release(request->body);
    uint32_t generation=request->generation; memset(request,0,sizeof(*request)); request->generation=generation;
    request->socket=FREAK_INVALID_NATIVE_SOCKET; freak_http_request_live--;
}
static void freak_http_cleanup(void) {
#if defined(FREAK_RUNTIME_OWNERSHIP_AUDIT) || defined(FREAK_C_RUNTIME_OWNERSHIP_AUDIT)
    if(freak_http_server_live || freak_http_request_live) { fprintf(stderr,"FREAK: ownership audit found live HTTP server/request owners\n"); _Exit(1); }
#endif
    for(size_t i=0;i<freak_http_request_slots;i++) { if(freak_http_requests[i]->in_use) freak_http_dispose_request(freak_http_requests[i]); freak_http_free(freak_http_requests[i]); }
    for(size_t i=0;i<freak_http_server_slots;i++) { if(freak_http_servers[i]->in_use) freak_http_close_socket(&freak_http_servers[i]->listener); freak_http_free(freak_http_servers[i]); }
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
    server->limits=(freak_http_limits){8192,32768,100,1048576,4096,8192,5000,15000,2000}; freak_http_server_live++;
    return (int64_t)(FREAK_HTTP_SERVER_DOMAIN|((uint64_t)generation<<32)|(slot+1));
}
static int64_t freak_http_new_request(int64_t server_ticket) {
    size_t slot=0;
    while(slot<freak_http_request_slots && (freak_http_requests[slot]->in_use || freak_http_requests[slot]->generation==FREAK_HTTP_GENERATION_MAX)) slot++;
    if(slot==freak_http_request_slots) {
        if(slot>=UINT32_MAX-1) freak_http_fail("request ticket table exhausted");
        if(slot==freak_http_request_capacity) { size_t next=freak_http_request_capacity?freak_http_request_capacity*2:16; freak_http_requests=freak_http_grow(freak_http_requests,next*sizeof(*freak_http_requests)); freak_http_request_capacity=next; }
        freak_http_requests[slot]=freak_http_allocate(sizeof(freak_http_request)); freak_http_request_slots++;
    }
    freak_http_request *request=freak_http_requests[slot]; uint32_t generation=request->generation+1; memset(request,0,sizeof(*request));
    request->generation=generation; request->in_use=true; request->socket=FREAK_INVALID_NATIVE_SOCKET;
    request->server=server_ticket; request->limits=freak_http_require_server(server_ticket)->limits;
    request->body=freak_byte_buffer_new(); request->current_header=-1; request->response_status=200; freak_http_request_live++;
    return (int64_t)(FREAK_HTTP_REQUEST_DOMAIN|((uint64_t)generation<<32)|(slot+1));
}

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
#ifdef _WIN32
    freak_wsa_init();
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
    if(bind(server->listener,(struct sockaddr *)&storage,(int)address_size)!=0 || listen(server->listener,16)!=0) goto failed;
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
int64_t freak_http_server_status(int64_t ticket) { freak_http_server *server=freak_http_require_server(ticket); return atomic_load_explicit(&server->stopping,memory_order_acquire)?1:server->status; }
freak_word freak_http_server_error(int64_t ticket) { return freak_word_clone(freak_word_lit(freak_http_require_server(ticket)->error)); }
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
void freak_http_server_stop(int64_t ticket) { atomic_store_explicit(&freak_http_require_server(ticket)->stopping,true,memory_order_release); }
void freak_http_server_close(int64_t ticket) {
    freak_http_server *server=freak_http_require_server(ticket); atomic_store_explicit(&server->stopping,true,memory_order_release);
    freak_http_close_socket(&server->listener);
    for(size_t i=0;i<freak_http_request_slots;i++) if(freak_http_requests[i]->in_use && freak_http_requests[i]->server==ticket) {
        freak_http_request *request=freak_http_requests[i]; freak_http_close_socket(&request->socket);
        if(!request->responded) freak_http_error(request,503,"HTTP server closed");
    }
    server->in_use=false; freak_http_server_live--;
}

static int freak_http_wait_socket(freak_http_server *server,freak_native_socket socket,bool write,uint64_t deadline,uint64_t idle) {
    for(;;) {
        if(atomic_load_explicit(&server->stopping,memory_order_acquire)) return -2;
        uint64_t now=freak_command_now_ms(); if(now>=deadline || now>=idle) return 0;
        uint64_t left=deadline-now; if(idle-now<left) left=idle-now; int delay=(int)(left<50?left:50);
#ifdef _WIN32
        fd_set read_set,write_set,error_set; FD_ZERO(&read_set); FD_ZERO(&write_set); FD_ZERO(&error_set);
        if(write) FD_SET(socket,&write_set); else FD_SET(socket,&read_set); FD_SET(socket,&error_set);
        struct timeval timeout={delay/1000,(delay%1000)*1000};
        int ready=select(0,&read_set,&write_set,&error_set,&timeout);
#else
        struct pollfd descriptor={socket,write?POLLOUT:POLLIN,0}; int ready=poll(&descriptor,1,delay);
#endif
        if(ready>0) return 1;
        if(ready<0 && !freak_tcp_socket_error_is_interrupted()) return -1;
    }
}
static bool freak_http_send_all(freak_http_request *request,const void *data,size_t length,uint64_t deadline) {
    freak_http_server *server=freak_http_find_server(request->server); if(!server) return false;
    size_t offset=0; uint64_t idle=freak_command_now_ms()+request->limits.idle_ms;
    while(offset<length) {
        if(freak_http_wait_socket(server,request->socket,true,deadline,idle)!=1) return false;
        size_t wanted=length-offset; if(wanted>INT_MAX) wanted=INT_MAX;
#ifdef _WIN32
        int sent=send(request->socket,(const char *)data+offset,(int)wanted,0);
#else
        ssize_t sent=send(request->socket,(const char *)data+offset,wanted,freak_tcp_socket_send_flags());
#endif
        if(sent<0 && (freak_tcp_socket_error_is_interrupted() || freak_tcp_socket_error_is_timeout())) continue;
        if(sent<=0) return false;
        offset+=(size_t)sent; idle=freak_command_now_ms()+request->limits.idle_ms;
    }
    return true;
}
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
    request->headers_done=true; request->chunk_line=(parser->flags&F_CHUNKED)!=0; return 0;
}
static int freak_http_on_body(llhttp_t *parser,const char *bytes,size_t length) {
    freak_http_request *request=parser->data; freak_byte_buffer_record *body=freak_byte_buffer_require(request->body,"HTTP decoded body");
    if(length>request->limits.body-body->length) { freak_http_error(request,413,"decoded request body exceeds limit"); return -1; }
    freak_byte_buffer_append_bytes(body,(const uint8_t *)bytes,length); return 0;
}
static int freak_http_on_chunk(llhttp_t *parser) {
    freak_http_request *request=parser->data; freak_byte_buffer_record *body=freak_byte_buffer_require(request->body,"HTTP chunk size");
    if(parser->content_length>request->limits.body-body->length) { freak_http_error(request,413,"chunk exceeds remaining request body limit"); return -1; }
    request->chunk_line=false; return 0;
}
static int freak_http_on_chunk_complete(llhttp_t *parser) { freak_http_request *request=parser->data; request->chunk_line=(parser->flags&F_TRAILING)==0; return 0; }
static int freak_http_on_complete(llhttp_t *parser) { ((freak_http_request *)parser->data)->message_done=true; return HPE_PAUSED; }

static const char *freak_http_reason(int status) {
    switch(status) { case 200:return "OK";case 201:return "Created";case 204:return "No Content";case 304:return "Not Modified";case 400:return "Bad Request";case 404:return "Not Found";case 405:return "Method Not Allowed";case 408:return "Request Timeout";case 413:return "Content Too Large";case 414:return "URI Too Long";case 417:return "Expectation Failed";case 431:return "Request Header Fields Too Large";case 500:return "Internal Server Error";case 501:return "Not Implemented";case 503:return "Service Unavailable";case 505:return "HTTP Version Not Supported";default:return "Response"; }
}
static void freak_http_reject(freak_http_request *request) {
    if(request->socket==FREAK_INVALID_NATIVE_SOCKET) return;
    const char *reason=freak_http_reason(request->status); char response[512];
    int size=snprintf(response,sizeof(response),"HTTP/1.1 %d %s\r\nContent-Length: %zu\r\nContent-Type: text/plain; charset=utf-8\r\nConnection: close\r\n\r\n%s\n",request->status,reason,strlen(reason)+1,reason);
    if(size>0 && (size_t)size<sizeof(response)) (void)freak_http_send_all(request,response,(size_t)size,freak_command_now_ms()+request->limits.idle_ms);
    freak_http_close_socket(&request->socket);
}
int64_t freak_http_server_next_request(int64_t server_ticket) {
    freak_http_server *server=freak_http_require_server(server_ticket); if(server->active) freak_http_fail("release the active request before accepting another");
    int64_t ticket=freak_http_new_request(server_ticket); freak_http_request *request=freak_http_require_request(ticket); server->active=ticket;
    if(server->status || atomic_load_explicit(&server->stopping,memory_order_acquire)) { freak_http_error(request,503,"HTTP server is stopped or failed"); return ticket; }
    for(;;) {
        int ready=freak_http_wait_socket(server,server->listener,false,UINT64_MAX,UINT64_MAX);
        if(ready!=1) { freak_http_error(request,ready==-2?503:500,ready==-2?"HTTP server stopped":"could not wait for HTTP connection"); return ticket; }
        request->socket=accept(server->listener,NULL,NULL);
        if(request->socket==FREAK_INVALID_NATIVE_SOCKET) { if(freak_tcp_socket_error_is_interrupted() || freak_tcp_socket_error_is_timeout()) continue; freak_http_error(request,500,"could not accept HTTP connection"); return ticket; }
        freak_http_socket_live++; break;
    }
    freak_tcp_socket_configure_no_sigpipe(request->socket);
    if(!freak_http_nonblocking(request->socket)) { freak_http_error(request,500,"could not configure HTTP connection"); freak_http_reject(request); return ticket; }
    llhttp_settings_init(&request->settings);
    request->settings.on_method=freak_http_on_method; request->settings.on_url=freak_http_on_target;
    request->settings.on_header_field=freak_http_on_field; request->settings.on_header_value=freak_http_on_value;
    request->settings.on_header_value_complete=freak_http_on_value_complete; request->settings.on_headers_complete=freak_http_on_headers;
    request->settings.on_body=freak_http_on_body; request->settings.on_chunk_header=freak_http_on_chunk;
    request->settings.on_chunk_complete=freak_http_on_chunk_complete; request->settings.on_message_complete=freak_http_on_complete;
    llhttp_init(&request->parser,HTTP_REQUEST,&request->settings); request->parser.data=request;
    uint64_t now=freak_command_now_ms(); request->header_deadline=now+request->limits.header_ms; request->idle_deadline=now+request->limits.idle_ms;
    unsigned char bytes[4096];
    while(!request->status && !request->message_done) {
        uint64_t deadline=request->headers_done?request->body_deadline:request->header_deadline;
        int ready=freak_http_wait_socket(server,request->socket,false,deadline,request->idle_deadline);
        if(ready!=1) { freak_http_error(request,ready==-2?503:ready==0?408:400,ready==-2?"HTTP server stopped":ready==0?"HTTP request deadline exceeded":"HTTP socket read failed"); break; }
#ifdef _WIN32
        int received=recv(request->socket,(char *)bytes,sizeof(bytes),0);
#else
        ssize_t received=recv(request->socket,bytes,sizeof(bytes),0);
#endif
        if(received<0 && (freak_tcp_socket_error_is_interrupted() || freak_tcp_socket_error_is_timeout())) continue;
        if(received<=0) { freak_http_error(request,400,"incomplete HTTP request or reset peer"); break; }
        request->idle_deadline=freak_command_now_ms()+request->limits.idle_ms;
        for(size_t i=0;i<(size_t)received && !request->status && !request->message_done;i++) {
            uint64_t tick=freak_command_now_ms();
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
            if(!request->line_done && bytes[i]=='\n') request->line_done=true;
            if(!was_headers && request->headers_done) {
                request->body_deadline=freak_command_now_ms()+request->limits.body_ms;
                if(request->expect_continue && !request->message_done && ((request->parser.flags&F_CHUNKED)||request->parser.content_length)) {
                    static const char interim[]="HTTP/1.1 100 Continue\r\n\r\n";
                    if(!freak_http_send_all(request,interim,sizeof(interim)-1,request->body_deadline)) { freak_http_error(request,400,"could not send 100 Continue"); break; }
                }
            }
        }
    }
    if(request->status) freak_http_reject(request); return ticket;
}

int64_t freak_http_server_request_status(int64_t ticket) { return freak_http_require_request(ticket)->status; }
freak_word freak_http_server_request_error(int64_t ticket) { return freak_word_clone(freak_word_lit(freak_http_require_request(ticket)->error)); }
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
static bool freak_http_respondable(freak_http_request *request) { if(!request->message_done || request->status || request->responded || request->socket==FREAK_INVALID_NATIVE_SOCKET) { snprintf(request->error,sizeof(request->error),"request cannot receive another response"); return false; } return true; }
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
static int64_t freak_http_send(freak_http_request *request,const unsigned char *body,size_t length,const char *type) {
    if(!freak_http_respondable(request)) return 0;
    if(length>request->limits.body) { snprintf(request->error,sizeof(request->error),"response body exceeds configured limit"); return 0; }
    freak_http_text wire={0}; char first[256];
    int count=snprintf(first,sizeof(first),"HTTP/1.1 %d %s\r\nConnection: close\r\n",request->response_status,freak_http_reason(request->response_status));
    freak_http_text_append(&wire,first,(size_t)count,request->limits.headers+1024);
    if(request->response_status!=204) { count=snprintf(first,sizeof(first),"Content-Length: %zu\r\n",length); freak_http_text_append(&wire,first,(size_t)count,request->limits.headers+1024); }
    bool content_type=false;
    for(size_t i=0;i<request->response_count;i++) {
        freak_http_header *header=&request->response_headers[i]; if(freak_http_equal(header->name.data,header->name.length,"content-type")) content_type=true;
        freak_http_text_append(&wire,header->name.data,header->name.length,request->limits.headers+1024); freak_http_text_append(&wire,": ",2,request->limits.headers+1024);
        freak_http_text_append(&wire,header->value.data,header->value.length,request->limits.headers+1024); freak_http_text_append(&wire,"\r\n",2,request->limits.headers+1024);
    }
    if(!content_type) { freak_http_text_append(&wire,"Content-Type: ",14,request->limits.headers+1024); freak_http_text_append(&wire,type,strlen(type),request->limits.headers+1024); freak_http_text_append(&wire,"\r\n",2,request->limits.headers+1024); }
    freak_http_text_append(&wire,"\r\n",2,request->limits.headers+1024);
    uint64_t deadline=freak_command_now_ms()+request->limits.body_ms;
    bool sent=freak_http_send_all(request,wire.data,wire.length,deadline);
    bool omit=request->response_status==204 || request->response_status==304 || freak_http_equal(request->method.data,request->method.length,"head");
    if(sent && !omit && length) sent=freak_http_send_all(request,body,length,deadline);
    freak_http_free(wire.data); freak_http_close_socket(&request->socket); request->responded=true;
    if(!sent) snprintf(request->error,sizeof(request->error),"could not send complete HTTP response before deadline"); return sent?1:0;
}
int64_t freak_http_server_send_bytes(int64_t ticket,int64_t body_ticket) { freak_http_request *request=freak_http_require_request(ticket); freak_byte_buffer_record *body=freak_byte_buffer_require(body_ticket,"HTTP response body"); if(body->status!=FREAK_BYTE_BUFFER_OK) { snprintf(request->error,sizeof(request->error),"response ByteBuffer has a pending error"); return 0; } return freak_http_send(request,body->data,body->length,"application/octet-stream"); }
int64_t freak_http_server_send_text(int64_t ticket,freak_word body) { freak_http_request *request=freak_http_require_request(ticket); if(!freak_byte_buffer_utf8_valid((const uint8_t *)body.data,body.length)) { snprintf(request->error,sizeof(request->error),"text response requires NUL-free UTF-8"); return 0; } return freak_http_send(request,(const unsigned char *)body.data,body.length,"text/plain; charset=utf-8"); }
void freak_http_server_request_release(int64_t ticket) { freak_http_dispose_request(freak_http_require_request(ticket)); }
int64_t freak_http_server_live_servers(void) { return (int64_t)freak_http_server_live; }
int64_t freak_http_server_live_requests(void) { return (int64_t)freak_http_request_live; }
int64_t freak_http_server_live_sockets(void) { return (int64_t)freak_http_socket_live; }
int64_t freak_http_server_retained_bytes(void) {
    uint64_t bytes=freak_http_owned_bytes;
    for(size_t i=0;i<freak_http_request_slots;i++) if(freak_http_requests[i]->in_use) bytes+=freak_byte_buffer_require(freak_http_requests[i]->body,"HTTP retained-byte count")->capacity;
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
