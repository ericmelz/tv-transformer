"""
Create a mapping from from originals to plexified videos.

Mapping is in format of [{src:'/path/to/src1', dest:'/path/to/dest1'} ... ]

Strategy:
---------
loop through top-level dirs
for a dir, use api to identify tv series
if there are multiple series, query to select correct series
example of ambiguous series: 30-minute meals (there's one with Jamie Oliver)

gather all episodes `eps` for the series

under the dir, there are episode name
foreach episode name,
match the episode against `eps`
if there's an exact match, use it
if there's not an exact match, generate best guesses and query user to select

Matching alg:
strip out special chars

"""
import os

import tvdb_v4_official


def get_plex_name(tvdb, series_name, episode_name):
    results = tvdb.search(series_name, type='series')
    if len(results) > 1:
        print(f'{[series["name"] for series in results]}')
        result = results[1]  # hacky
    else:
        result = results[0]
    tvdb_id = int(result['tvdb_id'])

    # fetching a season's episode list
    series = tvdb.get_series_extended(tvdb_id)
    series_name = series['name']
    for series_season in sorted(series['seasons'], key=lambda x: (x['type']['name'], x['number'])):
        if series_season['type']['name'] == 'Aired Order':
            season = tvdb.get_season_extended(series_season['id'])
            for episode in season['episodes']:
                if episode['name'] == episode_name:
                    return f'{series_name} - S{series_season["number"]:02}E{episode["number"]:02} - {episode["name"]}'


def get_series(tvdb, candidate):
    results = tvdb.search(candidate, type='series')
    if len(results) == 0:
        return None
    if len(results) > 1:
        print(f'Select a series that matches "{candidate}"')
        for i, series in enumerate(results):
            print(f'{i}) {series["name"]}')
        print(f'{len(results)}) None of the above')
        i = int(input())
        if i == len(results):
            return None
        result = results[i]  # hacky
    else:
        result = results[0]
    return candidate, result['name'], result['tvdb_id']


def get_series_from_src(tvdb, src_dir):
    dirs = os.listdir(src_dir)
    print(dirs)
    series_names = []
    for directory in dirs:
        series = get_series(tvdb, directory)
        if series is not None:
            series_names.append(series)
        else:
            print(f"***WARNING: COULDN'T FIND SERIES MATCHING {directory}.  Skipping...")
        break  # for testing
    return seriesE


def get_episodes_for_series(tvdb, src_dir, dirname, series_name, series_id):
    # todo generate a tuple of the original name (including extension) and the episode name (including extension)
    # todo if not a perfect match, generate partial matches and offer None of the above, querying user
    episodes = []
    src_dir = f'{src_dir}/{dirname}'
    return episodes


def plan(src_dir='/Volumes/EricRandiShare/iTunes_Library/TV Shows', dest_dir='/Volumes/video/TV Shows'):
    api_key = os.environ.get('TVDB_API_KEY')
    pin = os.environ.get('TVDB_PIN')
    tvdb = tvdb_v4_official.TVDB(api_key, pin)
    series = get_series_from_src(tvdb, src_dir)
    mappings = []
    for dirname, series_name, series_id in series:
        episodes = get_episodes_for_series(tvdb, src_dir, dirname, series_name, series_id)
        for filename, episode_name in episodes:
            src = f'{src_dir}/{dirname}/{filename}'
            dest = f'{dest_dir}/{series_name}/{episode_name}'
            mapping = {'src': src, 'dest': dest}
            mappings.append(mapping)
    return series


if __name__ == '__main__':
    result = plan()
    print(result)
