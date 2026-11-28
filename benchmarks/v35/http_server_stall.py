# Keep N connections stalled half-way through a request header for <seconds>:
#   http_server_stall.py <port> <N> <seconds>
# The server evicts a stalled connection at its header/idle deadline, so a
# closed one is replaced at once: N stay stalled for the whole window.
# Prints "stalled <N>" once all N are open.
import selectors,socket,sys,time
port,n,hold=int(sys.argv[1]),int(sys.argv[2]),float(sys.argv[3])
sel=selectors.DefaultSelector();opened=0
def stall():
    global opened
    s=socket.create_connection(('127.0.0.1',port));s.sendall(b'GET /api/v1/hello/Ada HTTP/1.1\r\nHost: x\r\n')
    s.setblocking(False);sel.register(s,selectors.EVENT_READ);opened+=1
for _ in range(n):stall()
print(f'stalled {n}',flush=True)
end=time.monotonic()+hold
while (left:=end-time.monotonic())>0:
    for key,_ in sel.select(timeout=min(left,0.5)):
        try:data=key.fileobj.recv(4096)
        except BlockingIOError:continue
        except OSError:data=b''
        if not data:sel.unregister(key.fileobj);key.fileobj.close();stall()
print(f'opened {opened} connections in total',flush=True)
