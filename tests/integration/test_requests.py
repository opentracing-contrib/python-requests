# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from random import randint
import sys

from opentracing.mocktracer import MockTracer
from opentracing.ext import tags as ext_tags
import docker
import pytest

from requests_opentracing import SessionTracing
import requests


server_port = 5678
server = 'http://localhost:{}'.format(server_port)


@pytest.fixture(scope='session')
def echo_container():
    session = docker.from_env()
    echo = session.containers.run('hashicorp/http-echo:latest', '-text="hello world"',
                                  ports={'5678/tcp': server_port}, detach=True)
    try:
        yield echo
    finally:
        echo.remove(force=True, v=True)


class TestSessionTracing(object):

    @pytest.fixture
    def session_tracing(self, echo_container):
        tracer = MockTracer()
        session = SessionTracing(tracer, propagate=True, span_tags=dict(custom='tag'))
        return tracer, session

    @pytest.fixture
    def tracer(self, session_tracing):
        return session_tracing[0]

    @pytest.fixture
    def session(self, session_tracing):
        return session_tracing[1]

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch',
                                        'head', 'delete', 'options'))
    def test_successful_requests(self, tracer, session, method):
        trace_id = randint(0, sys.maxsize)
        with tracer.start_active_span('root') as root_scope:
            root_scope.span.context.trace_id = trace_id
            response = getattr(session, method)(server)
        request = response.request
        spans = tracer.finished_spans()
        assert len(spans) == 2
        req_span, root_span = spans
        assert req_span.operation_name == 'requests.{}'.format(method)

        tags = req_span.tags
        assert tags['custom'] == 'tag'
        assert tags[ext_tags.COMPONENT] == 'requests'
        assert tags[ext_tags.SPAN_KIND] == ext_tags.SPAN_KIND_RPC_CLIENT
        assert tags[ext_tags.HTTP_STATUS_CODE] == 200
        assert tags[ext_tags.HTTP_METHOD] == method
        assert tags[ext_tags.HTTP_URL] == server
        assert ext_tags.ERROR not in tags

        assert request.headers['ot-tracer-spanid'] == '{0:x}'.format(req_span.context.span_id)
        assert request.headers['ot-tracer-traceid'] == '{0:x}'.format(trace_id)

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch',
                                        'head', 'delete', 'options'))
    def test_unsuccessful_requests(self, tracer, session, method):
        invalid_server = 'https://localhost:123456789'
        with tracer.start_active_span('root'):
            with pytest.raises(requests.ConnectionError) as ce:
                getattr(session, method)(invalid_server)
        spans = tracer.finished_spans()
        assert len(spans) == 2
        req_span, root_span = spans
        assert req_span.operation_name == 'requests.{}'.format(method)

        tags = req_span.tags
        assert tags['custom'] == 'tag'
        assert tags[ext_tags.COMPONENT] == 'requests'
        assert tags[ext_tags.SPAN_KIND] == ext_tags.SPAN_KIND_RPC_CLIENT
        assert ext_tags.HTTP_STATUS_CODE not in tags
        assert tags[ext_tags.HTTP_METHOD] == method
        assert tags[ext_tags.HTTP_URL] == invalid_server
        assert tags[ext_tags.ERROR] is True
        assert str(ce.value) in tags['error.object']
