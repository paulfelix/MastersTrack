import argparse
import requests
import warnings
import re
from collections import namedtuple
from datetime import datetime
from html.parser import HTMLParser
import pytimeparse
import pymysql

warnings.filterwarnings('ignore', '.*"Duplicate entry .*')

mastersrankings_url = 'https://www.mastersrankings.com/rankings/'

param_name_map = {
    'agegroup': 'x10',
    'season': 'x2',
    'event': 'x7',
    'gender': 'x4',
    'year': 'x1'
}

RankEntry = namedtuple(
    'RankEntry',
    'performance, wind, age_grading, athlete_id, athlete_name, extra, country, meet_id, meet_info')

x_arg_pattern = re.compile('x[89]=')


def main(args):
    for query in iter_querys(args):
        print(query)
        html = read_rankings_data(query)
        performances = parse_html(query, html)
        import_into_db(query, performances)
        print('performances: %d' % len(performances))


def iter_querys(args):
    def years():
        if '-' in args.years:
            y1, y2 = args.years.split('-')
            return range(int(y1), int(y2)+1)
        else:
            return args.years.split(',')

    def agegroups():
        if '-' in args.agegroups:
            a1, a2 = args.agegroups.split('-')
            return range(int(a1), int(a2)+5, 5)
        else:
            return args.agegroups.split(',')

    def events():
        return args.events.split(',')

    for year in years():
        for agegroup in agegroups():
            for event in events():
                yield dict(
                    season=args.season,
                    gender=args.gender,
                    year=year,
                    agegroup=args.gender+str(agegroup),
                    event=event
                )


def read_rankings_data(query):
    params = {param_name_map[k]: v for k, v in query.items()}
    params[param_name_map['gender']] = 'Men' if query['gender'] == 'M' else 'Women'
    r = requests.get(mastersrankings_url, params=params, headers={'Cookie': cookie})
    return r.text


def parse_html(query, html):
    parser = RankingsParser(query)
    parser.feed(html)
    return parser.get_performances()


def import_into_db(query, performances):
    importer = DBImporter()
    importer.import_performances(query, performances)


class RankingsParser(HTMLParser):
    def __init__(self, query):
        HTMLParser.__init__(self)
        self._query = query
        self._in_rankentry = False
        self._performances = []
        self._current_entry = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr' and attrs.get('class') == 'ranktablerow':
            self._in_rankentry = True
            self._current_entry = []
        elif tag == 'input' and self._in_rankentry:
            self._current_entry.append(attrs.get('value'))
        elif tag == 'a' and self._in_rankentry:
            info = attrs.get('href') or ''
            if x_arg_pattern.search(info):
                info = x_arg_pattern.split(info)[1]
            self._current_entry.append(info)

    def handle_endtag(self, tag):
        if tag == 'tr' and self._in_rankentry:
            self._store_current_entry()
            self._in_rankentry = False

    def get_performances(self):
        return self._performances

    def _store_current_entry(self):
        try:
            if len(self._current_entry) == 8:
                self._current_entry.insert(1, None)  # Add empty wind field
            rank_entry = RankEntry(*self._current_entry)
        except Exception:
            print(self._current_entry)
            raise

        try:
            parsed = dict(
                athleteID=rank_entry.athlete_id,
                meetID=rank_entry.meet_id,
                year=int(self._query['year']),
                performance=rank_entry.performance,
                wind=rank_entry.wind
            )

            name, age = rank_entry.athlete_name.rsplit(' (', 1)
            name_parts = name.split(' ')
            if name_parts[-1] in ['Sr.', 'Jr.', 'III']:
                parsed['firstName'] = ' '.join(name_parts[:-2])
                parsed['lastName'] = ' '.join(name_parts[-2:])
            else:
                parsed['firstName'] = ' '.join(name_parts[:-1])
                parsed['lastName'] = name_parts[-1]
            age = int(age[:-1])
            parsed['birthYear'] = parsed['year'] - age - 1

            place, dates = rank_entry.meet_info.split(' on ')

            place = place.split(', ')
            parsed['country'] = place[-1]
            parsed['city'] = place[0]
            if len(place) > 2:
                parsed['state'] = place[1]

            dates = dates.split(' - ')
            parsed['startDate'] = datetime.strptime(dates[0], '%d %b %y')
            if len(dates) == 2:
                parsed['endDate'] = datetime.strptime(dates[1], '%d %b %y')
        except Exception:
            print(rank_entry)
            raise

        self._performances.append(parsed)
        self._current_entry = []


class DBImporter:
    def import_performances(self, query, performances):
        self._query = query

        conn = pymysql.connect(user='root', db='masterstrack')
        self._cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            for performance in performances:
                self._import_athlete(performance)
                self._import_meet(performance)
                self._import_performance(performance)
        except Exception:
            print(performance)
            raise
        finally:
            self._cursor.close()

    def _import_athlete(self, performance):
        sql = """
            INSERT IGNORE INTO Athletes VALUES (%s,%s,%s,%s,%s);
        """
        self._cursor.execute(sql, (
            performance['athleteID'],
            performance['firstName'],
            performance['lastName'],
            self._query['gender'],
            performance['birthYear']
        ))
        self._cursor.connection.commit()

    def _import_meet(self, performance):
        sql = """
            INSERT IGNORE INTO Meets VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
        """
        self._cursor.execute(sql, (
            performance['meetID'],
            self._query['season'],
            performance['year'],
            performance['startDate'],
            performance.get('endDate'),
            performance['city'],
            performance.get('state'),
            performance['country'],
        ))
        self._cursor.connection.commit()

    def _import_performance(self, performance):
        sql = """
            INSERT IGNORE INTO Performances VALUES (%s,%s,%s,%s,%s,%s);
        """
        try:
            perf = float(performance['performance'])
        except (TypeError, ValueError):
            perf = pytimeparse.parse(performance['performance'])

        self._cursor.execute(sql, (
            performance['meetID'],
            performance['athleteID'],
            self._query['agegroup'],
            self._query['event'],
            perf,
            performance['wind']
        ))
        self._cursor.connection.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-s', '--season', default='Indoor', choices=['Indoor', 'Outdoor'])
    parser.add_argument('-g', '--gender', default='M', choices=['M', 'W'])
    parser.add_argument('-y', '--years', default='2014')
    parser.add_argument('-a', '--agegroups', default='50', help='(eg., 50-100)')
    parser.add_argument('-e', '--events', default='60', help='(eg., 60,200)')
    args = parser.parse_args()
    main(args)
