#!/usr/bin/env python
"""
Flask application that streams html content

Example usage downloading 16Kb but using different block sizes:
/streamhtml?nblocks=16&block_size=1024
/streamhtml?nblocks=328&block_size=512

"""
import sys
import random
import string
import time
import os
from datetime import datetime
import flask


app = flask.Flask(__name__)

# valid set of chars used for block of data
LETTERS = string.ascii_lowercase

# switch to figure out if python2/3
is_python3 = False
if sys.version_info > (3, 0):
    is_python3 = True


def random_string(stringLength=40, ending='<br>\n'):
    """Generate a random string of fixed length """
    return ''.join(random.choice(LETTERS) for i in range(stringLength - len(ending))) + ending


@app.route("/")
def entry_point():
    """ simple entry for test """
    return "<h1>streamhtml entry point</h1>"


@app.before_request
def start_timing():
    """ begins timing of single request """
    started = datetime.now()

    # put variables in app context (threadlocal for each request)
    ctx = app.app_context()
    flask.g.id = random.randint(1, 65535)
    flask.g.started = started

@app.after_request
def set_response_headers(response):
  """ Ensures no cache """
  response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
  response.headers['Pragma'] = 'no-cache'
  response.headers['Expires'] = '0'
  return response

@app.teardown_request
def end_timing(error=None):
    """ end timing of single request """
    finished = datetime.now()

    # retrieve params from request context
    block_size = flask.request.args.get('block_size', default=1024, type=int)
    nblocks = flask.request.args.get('nblocks', default=10, type=int)
    sleep_ms = flask.request.args.get('sleep_ms', default=0, type=int)
    use_static_data = flask.request.args.get('use_static_data', default=0, type=int)

    # retrieve params from app context (threadlocal for each request)
    id = flask.g.id
    started = flask.g.started
    delta = (finished - started)
    milliseconds = delta.microseconds / 1000.0

    # show final stats of request
    print("request={},nblocks={},block_size={},sleep_ms={},duration={}ms".format(
        flask.g.id, nblocks, block_size, sleep_ms, milliseconds)
         )


@app.route('/streamhtml')
def stream_html():
    """ streams down html data """

    block_size = flask.request.args.get('block_size', default=1024, type=int)
    nblocks = flask.request.args.get('nblocks', default=10, type=int)
    sleep_ms = flask.request.args.get('sleep_ms', default=0, type=int)
    use_static_data = flask.request.args.get('use_static_data', default=0, type=int)

    # pregenerate block of random data
    static_data = random_string(block_size)

    def generate(staticdata):
        """ create and return data in small parts """

        # python3 made 'range' performant,
        # whereas python2 needs you to specify xrange for effiency with large sets
        xrangefunc = range
        if not is_python3:
            xrangefunc = xrange

        for counter in xrangefunc(nblocks):
            time.sleep(sleep_ms / 1000)
            if use_static_data:
                yield static_data
            else:
                yield random_string(block_size)

    return flask.Response(flask.stream_with_context(generate(static_data)), mimetype='text/html')


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
