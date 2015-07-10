#!/usr/bin/env python
import re
import time
import requests
import lxml.etree
import lxml.html

from hashlib import sha1
from flask import Flask, request
from flask import render_template

app = Flask(__name__)
app.debug = True

# http://lxml.de/1.3/extensions.htmlimport re
#from lxml import etree
ns = lxml.etree.FunctionNamespace('http://allmychanges.com/functions')
ns.prefix = 'amch'
#ns = lxml.etree.FunctionNamespace(None)

#namespaces = {'amch': 'http://allmychanges.com/functions'}
def sub(context, pattern, replacement, text):
    print 'SUBSTITUTE'
    return re.sub(pattern, replacement, text[0])
ns['re.sub'] = sub

def match(context, pattern, text):
    return re.match(pattern, text[0]) is not None
ns['re.match'] = match


sessions = {}

@app.route("/")
def index():
    url = request.args.get('url')

    if url:
        session_id = sha1(str(time.time())).hexdigest()
        sessions[session_id] = {'url': url}
        return render_template('index.html', session_id=session_id)
    return render_template('index.html')


def html_document_fromstring(text):
    """Accepts unicode strings and uses special hack
    to make sure lxml dont find charset encoding.
    """
    # the hack :)
    if isinstance(text, unicode):
        match = re.search(ur'encoding=[\'"](?P<encoding>.*?)[\'"] ?\?>',
                          text[:200],
                          flags=re.IGNORECASE)
        if match is not None:
            encoding = match.group('encoding')
            text = text.encode(encoding)
    return lxml.html.document_fromstring(text)


@app.route('/p/<session_id>')
def preview(session_id):
    session = sessions[session_id]
    url =  session['url']
    response = requests.get(url).content

    xslt =  session.get('xslt')
    if xslt:
        parsed = html_document_fromstring(response)
        transform = lxml.etree.XSLT(lxml.etree.XML(xslt))
        parsed = transform(parsed)
        response = lxml.html.tostring(parsed)

    return response


@app.route('/xslt/<session_id>', methods=['POST'])
def save_xslt(session_id):
    session = sessions[session_id]
    xslt = request.form['xslt'].strip()
    session['xslt'] = xslt
    return 'OK'



if __name__ == "__main__":
    app.run()
