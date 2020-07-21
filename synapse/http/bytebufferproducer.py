# -*- coding: utf-8 -*-
# Copyright 2020 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from zope.interface.declarations import implementer

from twisted.internet import interfaces
from twisted.web.server import Request


@implementer(interfaces.IPullProducer)
class ByteBufferProducer:
    """IPullProducer which writes a byte buffer to the request."""

    buffer_size = 65536

    def __init__(self, request: Request, buf: bytes):
        self._request = request
        # we wrap the underlying buffer in a `memoryview` to support copy-less slicing.
        self._buf = memoryview(buf)
        self._offset = 0

    def start(self):
        self._request.registerProducer(self, False)

    def stopProducing(self):
        self._request = None
        self._buf.release()

    def resumeProducing(self):
        if not self._request:
            return

        offset = self._offset

        if offset >= len(self._buf):
            # we're done
            self._request.unregisterProducer()
            self._request.finish()
            self.stopProducing()
            return

        self._offset += self.buffer_size

        # this .write will spin the reactor, calling .doWrite and then
        # .resumeProducing again, so be prepared for a re-entrant call
        self._request.write(self._buf[offset : self.buffer_size].tobytes())
