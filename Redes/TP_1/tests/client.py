#!/usr/bin/env python3

import argparse
import resource
import logging
import re
import time
import select
import socket
import sys


BUFSZ = 4096


def create_parser():
    desc = """Client controller for testing"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--script",
        dest="scriptfn",
        metavar="FILE",
        type=str,
        required=True,
        help="File with control script",
    )
    return parser


class Controller:
    MAX_CLIENTS = 10
    RE_CONNECT = re.compile(r"^!connect (?P<cid>\d+) (?P<port>\d+) (?P<outfn>[\w.-]+)$")
    RE_SLEEP = re.compile(r"^!sleep (?P<secs>\d+(?:\.\d*)?)$")
    RE_SEND = re.compile(r"^!s(?P<cid>\d+) (?P<msg>.+)$")

    def __init__(self, scriptfn: str):
        self.scriptfd = open(scriptfn, "r")
        self.sockets = [None] * Controller.MAX_CLIENTS
        self.files = [None] * Controller.MAX_CLIENTS
        self.joinbufs = [""] * Controller.MAX_CLIENTS

    def run(self):
        for line in self.scriptfd:
            self._handle(line)
        self.scriptfd.close()

    def _handle(self, line):
        if Controller.RE_CONNECT.match(line):
            # Use assignment expressions instead when Python 3.8 comes
            m = Controller.RE_CONNECT.match(line)
            cid = int(m.group("cid"))
            assert self.sockets[cid] is None
            addr = "127.0.0.1"
            port = int(m.group("port"))
            self.sockets[cid] = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            self.sockets[cid].connect((addr, port))
            self.files[cid] = open(m.group("outfn"), "w")
            logging.debug("cid %d connected", cid)
        if Controller.RE_SLEEP.match(line):
            m = Controller.RE_SLEEP.match(line)
            secs = float(m.group("secs"))
            logging.debug("sleeping %f secs", secs)
            time.sleep(secs)
            self._dump_messages()
        if Controller.RE_SEND.match(line):
            m = Controller.RE_SEND.match(line)
            cid = int(m.group("cid"))
            assert self.sockets[cid] is not None
            msg = m.group("msg") + "\n"
            msg = self.joinbufs[cid] + msg
            self.joinbufs[cid] = ""
            logging.debug("sending [%s]", msg.rstrip())
            self.sockets[cid].send(msg.encode("ascii"))

    def _dump_messages(self):
        logging.debug("dumping messages")
        sockets = list(s for s in self.sockets if s is not None)
        rs, _ws, _xs = select.select(sockets, [], sockets, 0.0)
        assert not _ws and not _xs
        for cid, s in enumerate(self.sockets):
            if s is None or s not in rs:
                continue
            # This assumes we get the whole message in one go.
            # This implementation is insufficient for the server.
            msg = s.recv(BUFSZ)
            if not msg:
                self._close_client(cid)
            else:
                self.files[cid].write(msg.decode("ascii"))

    def _close_client(self, cid):
        self.sockets[cid].close()
        self.sockets[cid] = None
        self.files[cid].close()
        self.files[cid] = None
        self.joinbufs[cid] = ""


def main():
    resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 35, 1 << 35))
    logging.basicConfig(
        filename="client.log", format="%(levelname)s %(message)s", level=logging.DEBUG
    )

    parser = create_parser()
    opts = parser.parse_args()

    controller = Controller(opts.scriptfn)
    controller.run()


if __name__ == "__main__":
    sys.exit(main())
