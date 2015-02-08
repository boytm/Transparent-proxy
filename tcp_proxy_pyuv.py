#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
import sys
import socket
import struct

import pyuv

import functools


class TCPProxyHandler(object):
    def __init__(self, stream):
        sock = socket.fromfd(stream.fileno(), socket.AF_INET, socket.SOCK_STREAM)
        #print stream.socket.getsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, 16)
        dst = sock.getsockopt(socket.SOL_IP, 80, 16) 
        srv_port, srv_ip = struct.unpack('!2xH4s8x', dst)
        srv_ip = socket.inet_ntoa(srv_ip)
        if cmp((srv_ip, srv_port), stream.getsockname()) == 0:
            print "ignore not NATed stream"
            stream.close()
            return
        try:
            factory = pyuv.TCP(stream.loop)
            remote = factory.connect((srv_ip, srv_port), self.OnConnect)
        except:
            print 'connect error'
            stream.close()
        
        sock.close()

    def OnConnect(self, tcp_handle, error):
        if error:
            print("connect error %d" % error)
            tcp_handle.close()
            return
        
        Relay(self.stream, tcp_handle)


class Relay(object):
    def __init__(self, local, remote):
        self.local = local
        self.remote = remote

        self.local.nodelay(True)
        self.remote.nodelay(True)

        #self.local.set_close_callback(self.on_local_close)
        #self.remote.set_close_callback(self.on_remote_close)

        self.local.start_read(self.on_local_read)
        self.remote.start_read(self.on_remote_read)


    def on_local_close(self):
        print 'detect local close'
        if self.local.error:
            print self.local.error

        if not self.remote.writing():
            self.remote.close()

    def on_remote_close(self):
        print 'detect remote close'
        if self.remote.error:
            print self.remote.error

        if not self.local.writing():
            self.local.close()

    def on_local_read(self, data, error):
        if error:
            print 'local read %d, but should close' % len(data)
            self.local.close()
        if data:
            self.remote.write(data, self.on_remote_write)
            self.local.stop_read()

    def on_local_write(self, error):
        if error:
            print 'remote closed, cancel relay'
            return
        self.remote.start_read(self.on_remote_read)


    def on_remote_read(self, data, error):
        if error:
            print 'remote read %d, but should close' % len(data)
            self.remote.close()
        if data:
            self.local.write(data, self.on_local_write)
            self.remote.stop_read()

    def on_remote_write(self, error):
        if error:
            print 'local closed, cancel relay'
            return
        self.local.start_read(self.on_local_read)


clients = []

def on_connection(server, error):
    client = pyuv.TCP(server.loop)
    server.accept(client)
    
    TCPProxyHandler(client)

def main():
    loop = pyuv.Loop.default_loop()
    
    server = pyuv.TCP(loop)
    server.bind(("0.0.0.0", 8888))
    server.listen(on_connection)
    
    #signal_h = pyuv.Signal(loop)
    #signal_h.start(signal_cb, signal.SIGINT)
    
    loop.run()
    print("Stopped!")

if __name__ == "__main__":
    if sys.platform == 'linux2':
        import os, pwd
        os.setuid(pwd.getpwnam('nobody').pw_uid)
    main()

