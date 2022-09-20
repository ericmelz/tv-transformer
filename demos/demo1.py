import os

import tvdb_v4_official


def demo1():
    print('hey')
    api_key = os.environ.get('TVDB_API_KEY')
    pin = os.environ.get('TVDB_PIN')
    print(f'api key is {api_key}')
    print(f'PIN is {pin}')
    tvdb = tvdb_v4_official.TVDB(api_key, pin)

    # fetching several pages of series info
    series_list = []
    for j in range(5):  # Pages are numbered from 0
        series_list += tvdb.get_all_series(j)

    # fetching a series given an id
    series = tvdb.get_series(121361)

    # fetching a season's episode list
    series = tvdb.get_series_extended(121361)
    for season in sorted(series['seasons'], key=lambda x: (x['type']['name'], x['number'])):
        if season['type']['name'] == 'Aired Order' and season['number'] == 1:
            season = tvdb.get_season_extended(season['id'])
            break
        else:
            season = None

    # if season is not None:
    #     for episode in season['episodes']:
    #         print(f'{episode["name"]}')

    # fetch a page of episodes from a series by season_type (type is "default" if unspecified)
    info = tvdb.get_series_episodes(121361, page=0)
    # print(info['series'])

    # for ep in info['episodes']:
    #     print(ep)

    # fetching a movie
    movie = tvdb.get_movie(31)  # avengers

    # access a movie's characters
    movie = tvdb.get_movie_extended(31)
    # for c in movie['characters']:
    #     print(c)

    # fetching a person record
    person = tvdb.get_person_extended(movie['characters'][0]['peopleId'])
    # print(person)

    # using If-Modified-Since parameter
    series = tvdb.get_series_extended(393199, if_modified_since="Wed, 30 Jun 2022 07:28:00 GMT")
    print(series)


def get_plex_name(tvdb, series_name, episode_name):
    results = tvdb.search(series_name, type='series')
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


def demo2():
    print('demo2')
    api_key = os.environ.get('TVDB_API_KEY')
    pin = os.environ.get('TVDB_PIN')
    tvdb = tvdb_v4_official.TVDB(api_key, pin)
    series_name = 'Foodography'
    episode_name = 'Olive Oil'
    # episode_name = 'Los Angeles'
    # series_name = 'Build it Bigger'
    # episode_name = 'Hong Kong Bridge'
    plex_name = get_plex_name(tvdb, series_name, episode_name)
    print(plex_name)


if __name__ == '__main__':
    demo2()
