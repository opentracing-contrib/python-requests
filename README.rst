####################
Requests OpenTracing
####################

This package enables tracing http requests in a `Requests`_ ``Session`` via `The OpenTracing Project`_. 
Once a production system contends with real concurrency or splits into many services, crucial (and
formerly easy) tasks become difficult: user-facing latency optimization, root-cause analysis of backend
errors, communication about distinct pieces of a now-distributed system, etc. Distributed tracing
follows a request on its journey from inception to completion from mobile/browser all the way to the
microservices. 

As core services and libraries adopt OpenTracing, the application builder is no longer burdened with
the task of adding basic tracing instrumentation to their own code. In this way, developers can build
their applications with the tools they prefer and benefit from built-in tracing instrumentation.
OpenTracing implementations exist for major distributed tracing systems and can be bound or swapped
with a one-line configuration change.

If you want to learn more about the underlying Python API, visit the Python `source code`_.

.. _Requests: http://docs.python-requests.org/en/master/
.. _The OpenTracing Project: http://opentracing.io/
.. _source code: https://github.com/signalfx/python-requests/

Installation
============

Run the following command:

.. code-block:: 

    $ pip install requests-opentracing

Usage
=====

The provided ``requests.Session`` subclass allows the tracing of http methods using the OpenTracing API.
All that it requires is for a ``SessionTracing`` instance to be initialized using an instance
of an OpenTracing tracer and treated as a standard Requests session.

Initialize
----------

``SessionTracing`` takes the ``Tracer`` instance that is supported by OpenTracing and an optional
dictionary of desired tags for each created span. You can also specify whether you'd like your
current trace context to be propagated via http headers with your client request.  To create a
``SessionTracing`` object, you can either pass in a tracer object directly or default to the
``opentracing.tracer`` global tracer that's set elsewhere in your application:

.. code-block:: python

    from requests_opentracing import SessionTracing

    opentracing_tracer = # some OpenTracing tracer implementation
    traced_session = SessionTracing(opentracing_tracer, propagate=False,  # propagation allows distributed tracing in
                                    span_tags=dict(my_helpful='tag'))     # upstream services you control (True by default).
    resp = traced_session.get(my_url)

or

.. code-block:: python

    from requests_opentracing import SessionTracing
    import opentracing
    import requests

    opentracing.tracer = # some OpenTracing tracer implementation
    traced_session = SessionTracing()  # default to opentracing.tracer

You can now monkeypatch the ``requests.Session`` and ``requests.sessions.Session`` objects to point to the
``SessionTracing`` subclass for easier initialization:

.. code-block:: python

    from requests_opentracing import monkeypatch_requests

    monkeypatch_requests()


    from requests import Session

    opentracing_tracer = # some OpenTracing tracer implementation
    traced_session = Session(opentracing_tracer, propagate=False,  # Same arguments as provided to SessionTracing
                             span_tags=dict(my_helpful='tag'))
    resp = traced_session.get(my_url)

Further Information
===================

If you're interested in learning more about the OpenTracing standard, please visit
`opentracing.io`_ or `join the mailing list`_. If you would like to implement OpenTracing
in your project and need help, feel free to send us a note at `community@opentracing.io`_.

.. _opentracing.io: http://opentracing.io/
.. _join the mailing list: http://opentracing.us13.list-manage.com/subscribe?u=180afe03860541dae59e84153&id=19117aa6cd
.. _community@opentracing.io: community@opentracing.io
