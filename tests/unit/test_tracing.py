# Copyright (C) 2018-2019 SignalFx, Inc. All rights reserved.
from collections import namedtuple

from opentracing.mocktracer import MockTracer
from opentracing.ext import tags as ext_tags
import requests.sessions
import opentracing
import pytest
import mock

from requests_opentracing.tracing import SessionTracing, monkeypatch_requests


def stubbed_request(_, method, url, *args, **kwargs):
    response = namedtuple('response', 'method url status_code headers')
    return response(method, url, 200, kwargs.get('headers', {}))


@pytest.fixture
def original_session():
    yield requests.sessions.Session


@pytest.fixture(params=(True, False))
def session_cls(request):
    if request.param:
        original_session = requests.Session
        try:
            monkeypatch_requests()
            yield requests.Session
        finally:
            requests.Session = original_session
            requests.sessions.Session = original_session
    else:
        yield SessionTracing


class TestSessionTracing(object):

    def test_sources_tracer(self, session_cls):
        tracer = MockTracer()
        assert session_cls(tracer)._tracer is tracer
        assert session_cls(tracer)._get_tracer() is tracer

    def test_sources_global_tracer_by_default(self, session_cls):
        assert session_cls()._tracer is None
        assert session_cls()._get_tracer() is opentracing.tracer

    def test_sources_propagate(self, session_cls):
        assert session_cls()._propagate is True
        assert session_cls(propagate=True)._propagate is True
        assert session_cls(propagate=False)._propagate is False

    def test_sources_span_tags(self, session_cls):
        assert session_cls()._span_tags == {}
        desired_tags = dict(one=123)
        assert session_cls(span_tags=desired_tags)._span_tags is desired_tags

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch',
                                        'head', 'delete', 'options'))
    def test_request_without_propagate(self, method, original_session, session_cls):
        tracer = MockTracer()
        tracing = session_cls(tracer, False, span_tags=dict(one=123))
        with mock.patch.object(original_session, 'request', stubbed_request):
            response = getattr(tracing, method)('my_url')

        assert len(tracer.finished_spans()) == 1
        span = tracer.finished_spans()[0]
        assert span.operation_name == 'requests.{}'.format(method)
        tags = span.tags
        assert tags['one'] == 123
        assert tags[ext_tags.COMPONENT] == 'requests'
        assert tags[ext_tags.SPAN_KIND] == ext_tags.SPAN_KIND_RPC_CLIENT
        assert tags[ext_tags.HTTP_STATUS_CODE] == 200
        assert tags[ext_tags.HTTP_METHOD] == method
        assert tags[ext_tags.HTTP_URL] == 'my_url'

        assert 'ot-tracer-spanid' not in response.headers
        assert 'ot-tracer-traceid' not in response.headers

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch',
                                        'head', 'delete', 'options'))
    def test_request_with_propagate(self, method, original_session, session_cls):
        tracer = MockTracer()
        tracing = session_cls(tracer, True, span_tags=dict(one=123))
        with mock.patch.object(original_session, 'request', stubbed_request):
            response = getattr(tracing, method)('my_url')

        assert len(tracer.finished_spans()) == 1
        span = tracer.finished_spans()[0]
        assert span.operation_name == 'requests.{}'.format(method)
        tags = span.tags
        assert tags['one'] == 123
        assert tags[ext_tags.COMPONENT] == 'requests'
        assert tags[ext_tags.SPAN_KIND] == ext_tags.SPAN_KIND_RPC_CLIENT
        assert tags[ext_tags.HTTP_STATUS_CODE] == 200
        assert tags[ext_tags.HTTP_METHOD] == method
        assert tags[ext_tags.HTTP_URL] == 'my_url'

        assert response.headers['ot-tracer-spanid'] == '{0:x}'.format(span.context.span_id)
        assert response.headers['ot-tracer-traceid'] == '{0:x}'.format(span.context.trace_id)
