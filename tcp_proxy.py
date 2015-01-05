#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
import sys
import socket
import struct

import tornado.ioloop
import tornado.tcpserver
import tornado.tcpclient
#import tornado.web

from tornado import gen

import functools


class TCPProxyHandler(tornado.tcpserver.TCPServer):
    @gen.coroutine
    def handle_stream(self, stream, address):
        factory = tornado.tcpclient.TCPClient()
        if stream.socket.family == socket.AF_INET:
            #print stream.socket.getsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, 16)
            dst = stream.socket.getsockopt(socket.SOL_IP, 80, 16)
            srv_port, srv_ip = struct.unpack('!2xH4s8x', dst)
            srv_ip = socket.inet_ntoa(srv_ip)
            if cmp((srv_ip, srv_port), stream.socket.getsockname()) == 0:
                print "ignore not nated stream"
                stream.close()
                return
            try:
                remote = yield factory.connect(srv_ip, srv_port)
                Relay(stream, remote)
            except:
                print 'connect error'
                stream.close()
                return
        else:
            print 'Unsupported protocol family'
            return


class Relay(object):
    def __init__(self, local, remote):
        self.local = local
        self.remote = remote

        self.local.set_nodelay(True)
        self.remote.set_nodelay(True)

        self.local.set_close_callback(self.on_local_close)
        self.remote.set_close_callback(self.on_remote_close)

        self.local.read_bytes(65536, callback=self.on_local_read, partial=True)
        self.remote.read_bytes(65536, callback=self.on_remote_read, partial=True)


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

    def on_local_read(self, data):
        self.remote.write(data, callback = self.on_remote_write)

    def on_local_write(self):
        #if shouldclose:
        #    self.local.close()
        #else:
        if self.remote.closed():
            print 'remote closed, cancel relay'
            return
        self.remote.read_bytes(65536, callback=self.on_remote_read, partial=True)


    def on_remote_read(self, data):
        if self.remote.closed():
            print 'remote read %d, but should close' % len(data)
        self.local.write(data, callback = self.on_local_write)

    def on_remote_write(self):
        if self.local.closed():
            print 'local closed, cancel relay'
            return
        self.local.read_bytes(65536, callback=self.on_local_read, partial=True)





def main():
    #tornado.netutil.Resolver.configure('tornado.netutil.ThreadedResolver')
    #tornado.netutil.Resolver.configure('tornado.platform.caresresolver.CaresResolver')
    server = TCPProxyHandler()
    #server.listen(8888, address='127.0.0.1') # iptables can't DNAT to 127.0.0.1:8888
    server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    if sys.platform == 'linux2':
        import os, pwd
        os.setuid(pwd.getpwnam('nobody').pw_uid)
    main()

