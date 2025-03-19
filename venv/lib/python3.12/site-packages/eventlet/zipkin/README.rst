eventlet.zipkin
===============

`Zipkin <http://twitter.github.io/zipkin/>`_ is a distributed tracing system developed at Twitter.
This package provides a WSGI application using eventlet
with tracing facility that complies with Zipkin.

Why use it?
From the http://twitter.github.io/zipkin/:

"Collecting traces helps developers gain deeper knowledge about how
certain requests perform in a distributed system. Let's say we're having
problems with user requests timing out. We can look up traced requests
that timed out and display it in the web UI. We'll be able to quickly
find the service responsible for adding the unexpected response time. If
the service has been annotated adequately we can also find out where in
that service the issue is happening."


Screenshot
----------

Zipkin web ui screenshots obtained when applying this module to
`OpenStack swift <https://github.com/openstack/swift>`_  are in example/.


Requirement
-----------

A eventlet.zipkin needs `python scribe client <https://pypi.python.org/pypi/facebook-scribe/>`_
and `thrift <https://thrift.apache.org/>`_ (>=0.9),
because the zipkin collector speaks `scribe <https://github.com/facebookarchive/scribe>`_ protocol.
Below command will install both scribe client and thrift.

Install facebook-scribe:

::

    pip install facebook-scribe

**Python**: ``2.7`` (Because the current Python Thrift release doesn't support Python 3)


How to use
----------

Add tracing facility to your application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Apply the monkey patch before you start wsgi server.

.. code:: python

    # Add only 2 lines to your code
    from eventlet.zipkin import patcher
    patcher.enable_trace_patch()

    # existing code
    from eventlet import wsgi
    wsgi.server(sock, app)

You can pass some parameters to ``enable_trace_patch()``

* host: Scribe daemon IP address (default: '127.0.0.1')
* port: Scribe daemon port (default: 9410)
* trace_app_log: A Boolean indicating if the tracer will trace application log together or not. This facility assume that your application uses python standard logging library. (default: False)
* sampling_rate: A Float value (0.0~1.0) that indicates the tracing frequency. If you specify 1.0, all requests are traced and sent to Zipkin collecotr. If you specify 0.1, only 1/10 requests are traced. (defult: 1.0)


(Option) Annotation API
~~~~~~~~~~~~~~~~~~~~~~~
If you want to record additional information,
you can use below API from anywhere in your code.

.. code:: python

   from eventlet.zipkin import api

   api.put_annotation('Cache miss for %s' % request)
   api.put_key_value('key', 'value')




Zipkin simple setup
-------------------

::

    $ git clone https://github.com/twitter/zipkin.git
    $ cd zipkin
    # Open 3 terminals
    (terminal1) $ bin/collector
    (terminal2) $ bin/query
    (terminal3) $ bin/web

Access http://localhost:8080 from your browser.


(Option) fluentd
----------------
If you want to buffer the tracing data for performance,
`fluentd scribe plugin <http://docs.fluentd.org/articles/in_scribe>`_ is available.
Since ``out_scribe plugin`` extends `Buffer Plugin <http://docs.fluentd.org/articles/buffer-plugin-overview>`_ ,
you can customize buffering parameters in the manner of fluentd.
Scribe plugin is included in td-agent by default.


Sample: ``/etc/td-agent/td-agent.conf``

::

   # in_scribe
   <source>
     type scribe
     port 9999
   </source>

   # out_scribe
   <match zipkin.**>
     type scribe
     host Zipkin_collector_IP
     port 9410
     flush_interval 60s
     buffer_chunk_limit 256m
   </match>

| And, you need to specify ``patcher.enable_trace_patch(port=9999)`` for in_scribe.
| In this case, trace data is passed like below.
| Your application => Local fluentd in_scribe (9999) => Local fluentd out_scribe <buffering> =====> Remote zipkin collector (9410)

