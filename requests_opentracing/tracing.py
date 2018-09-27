# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from traceback import format_exc

from opentracing.propagation import Format
from opentracing.ext import tags
import requests.sessions
import opentracing


class SessionTracing(requests.sessions.Session):

    def __init__(self, tracer=None, propagate=False, span_tags=None):
        self._tracer = tracer or opentracing.tracer
        self._propagate = propagate
        self._span_tags = span_tags or {}
        requests.sessions.Session.__init__(self)

    def request(self, method, url, *args, **kwargs):
        lower_method = method.lower()
        with self._tracer.start_active_span('requests.{}'.format(lower_method)) as scope:
            span = scope.span
            span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
            span.set_tag(tags.COMPONENT, 'requests')
            span.set_tag(tags.HTTP_METHOD, lower_method)
            span.set_tag(tags.HTTP_URL, url)
            for name, value in self._span_tags.items():
                span.set_tag(name, value)

            if self._propagate:
                headers = kwargs.setdefault('headers', {})
                try:
                    self._tracer.inject(span.context, Format.HTTP_HEADERS, headers)
                except opentracing.UnsupportedFormatException:
                    pass
            try:
                resp = requests.sessions.Session.request(self, method, url, *args, **kwargs)
                span.set_tag(tags.HTTP_STATUS_CODE, resp.status_code)
            except Exception:
                span.set_tag(tags.ERROR, True)
                span.set_tag('error.object', format_exc())
                raise

        return resp
