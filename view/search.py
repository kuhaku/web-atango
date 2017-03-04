import random
from collections import defaultdict, Counter
from elasticsearch import Elasticsearch
from flask import Blueprint, render_template, Markup, request
from lib import file_io, kuzuha
from . import parse_log

app = Blueprint('search', __name__, template_folder='templates')
elasticsearch_setting = file_io.read('atango.json')['elasticsearch']

@app.route("/sw/search/", methods=['GET'])
def search():
    query = request.args.get('query')
    es = Elasticsearch([elasticsearch_setting])
    if query:
        es_query = {
            'match': {
                request.args.get('field'): {
                    'query': query.split(),
                    'operator': request.args.get('op'),
                    'minimum_should_match': '85%'
                }
            }
        }
    else:
        es_query = {"match_all": {}}
    sort_order = []
    for item in ('_score', 'quoted_by', 'dt'):
        if request.args.get(item):
            sort_order.append((item, request.args.get(item)))
    sort_item = kuzuha._build_sort(sort_order)
    body = {
        "query": {
            "filtered": {
                "query": es_query,
            }
        },
        'size': request.args.get('limit')
    }
    if sort_item:
        body.update({'sort': sort_item})
    results = es.search(index='qwerty', body=body, _source=True, request_timeout=30)
    results = map(lambda x: parse_log(x['_source']), results['hits']['hits'])
    results = '<hr>'.join(results)
    sort_order = dict(sort_order)
    return render_template('search.html', query=query, results=Markup(results), sort_order=sort_order)
