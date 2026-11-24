# Hold N connections that sent half a request header: http_server_stall.py <port> <N> <seconds>
import socket,sys,time
n=int(sys.argv[2]);port=int(sys.argv[1]);socks=[]
for i in range(n):
    s=socket.create_connection(('127.0.0.1',port));s.sendall(b'GET /api/v1/hello/Ada HTTP/1.1\r\nHost: x\r\n');socks.append(s)
time.sleep(float(sys.argv[3]))
