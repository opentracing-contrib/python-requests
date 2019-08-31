# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from collections import namedtuple

from opentracing.mocktracer import MockTracer
from opentracing.ext import tags as ext_tags
import requests.sessions
import opentracing
import pytest
import mock

from requests_opentracing.tracing import SessionTracing, monkeypatch_requests


def stubbed_request(method, url, *args, **kwargs):
    response = namedtuple('response', 'method url status_code headers')
    return response(method, url, 200, kwargs.get('headers', {}))


validate_monkeypatch = pytest.mark.parametrize("use_builtin_session", [True, False])


@pytest.fixture(autouse=True)
def monkeypatched_session(request):
    original_session = requests.Session
    try:
        if request.getfixturevalue("use_builtin_session"):
            monkeypatch_requests()

        yield original_session
    finally:
        requests.Session = original_session
        requests.sessions.Session = original_session


class TestSessionTracing(object):

    @validate_monkeypatch
    def test_sources_tracer(self, use_builtin_session):
        session_cls = requests.Session if use_builtin_session else SessionTracing

        tracer = MockTracer()
        assert session_cls(tracer)._tracer is tracer

    @validate_monkeypatch
    def test_sources_global_tracer_by_default(self, use_builtin_session):
        session_cls = requests.Session if use_builtin_session else SessionTracing

        assert session_cls()._tracer is opentracing.tracer

    @validate_monkeypatch
    def test_sources_propagate(self, use_builtin_session):
        session_cls = requests.Session if use_builtin_session else SessionTracing

        assert session_cls()._propagate is False
        assert session_cls(propagate=True)._propagate is True
        assert session_cls(propagate=False)._propagate is False

    @validate_monkeypatch
    def test_sources_span_tags(self, use_builtin_session):
        session_cls = requests.Session if use_builtin_session else SessionTracing

        assert session_cls()._span_tags == {}
        desired_tags = dict(one=123)
        assert session_cls(span_tags=desired_tags)._span_tags is desired_tags

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch',
                                        'head', 'delete', 'options'))
    @validate_monkeypatch
    def test_request_without_propagate(self, method, use_builtin_session, monkeypatched_session):
        session_cls = requests.Session if use_builtin_session else SessionTracing

        tracer = MockTracer()
        tracing = session_cls(tracer, False, span_tags=dict(one=123))
        with mock.patch.object(monkeypatched_session, 'request', stubbed_request):
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
    @validate_monkeypatch
    def test_request_with_propagate(self, method, use_builtin_session, monkeypatched_session):
        session_cls = requests.Session if use_builtin_session else SessionTracing

        tracer = MockTracer()
        tracing = session_cls(tracer, True, span_tags=dict(one=123))
        with mock.patch.object(monkeypatched_session, 'request', stubbed_request):
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
