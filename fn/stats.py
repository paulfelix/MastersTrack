import sys
import json
from urllib.parse import urlparse, parse_qs
import pymysql

conn = pymysql.connect(user='rankings', password='rankings', db='masterstrack', host='pfelix-mbpr.local')
cur = conn.cursor(pymysql.cursors.DictCursor)

select = """
    select * from Performances
    join Meets on Performances.meetID = Meets.meetID
"""

success_response = {
    'content_type': 'application/json',
    'protocol': {
        'status_code': 200,
        'headers': {
            'Access-Control-Allow-Origin': ['*']
        }
    }
}


def handle_request(request):
    params = get_query_params(request)
    results = run_query(params)
    response = make_response(params, results)
    sys.stdout.write(json.dumps(response))
    sys.stdout.flush()


def get_query_params(request):
    parsed_url = urlparse(request['protocol']['request_url'])
    params = parse_qs(parsed_url.query) or {}
    if request['body']:
        params.update(json.loads(request['body']))
    params = {k: v[0] for k, v in params.items()}
    return params


def run_query(params):
    where_clause = make_where_clause(params)
    sql = '%s where %s;' % (select, where_clause)
    print(sql, file=sys.stderr, flush=True)
    cur.execute(sql)
    results = {}
    for r in cur:
        perfs = results.get(r['year'])
        if perfs is None:
            perfs = results[r['year']] = []
        perfs.append(r['performance'])
    return [dict(year=k, performances=v) for k, v in results.items()]


def make_response(params, results):
    stats = compute_stats(results)
    data = dict(stats=stats)
    success_response['body'] = json.dumps(data)
    return success_response


def compute_stats(results):
    stats = []
    for r in results:
        year_stats = dict(year=r['year'])
        performances = sorted(r['performances'])
        count = len(performances)
        if count <= 1:
            quants = performances * 5
        else:
            quants = [
                performances[0],
                performances[int(count * 0.25)],
                performances[int(count * 0.5)],
                performances[int(count * 0.75)],
                performances[int(count * 0.95)]
            ]
        year_stats['quantiles'] = quants
        stats.append(year_stats)
    return stats


def make_where_clause(params):
    clause_list = []
    years = params['year'].split('-')
    if len(years) == 2:
        clause_list.append('Meets.year between %s and %s' % (years[0], years[1]))
    else:
        clause_list.append('Meets.year = %s' % years[0])
    clause_list.append('Meets.season = "%s"' % params['season'])
    clause_list.append('Performances.event = "%s"' % params['event'])
    clause_list.append('Performances.ageGroup = "%s"' % params['agegroup'])
    return ' and '.join(clause_list)


if __name__ == "__main__":
    while True:
        request = json.loads(sys.stdin.readline())
        handle_request(request)
