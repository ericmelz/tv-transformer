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
import re
from collections import Counter

import tvdb_v4_official


def get_tvdb_episodes_for_series(tvdb, series_id):
    series = tvdb.get_series_extended(series_id)
    result = []
    for series_season in sorted(series['seasons'], key=lambda x: (x['type']['name'], x['number'])):
        if series_season['type']['name'] == 'Aired Order':
            season = tvdb.get_season_extended(series_season['id'])
            for episode in season['episodes']:
                episode_name = episode['name']
                episode_id = f'S{series_season["number"]:02}E{episode["number"]:02}'
                result.append((episode_id, episode_name))
    return result


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
        result = results[i]
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
    return series_names


def make_histogram_for_sentence(sentence):
    """
    Given a sentence, produce a histogram of term counts.
    Canonicalize the terms by stripping special characters and lower-casing everything
    :param sentence: english sentence
    :return: dictionary of term counts
    """
    s = sentence.lower()
    s = re.sub('[^A-Za-z0-9]', ' ', s)
    tokens = s.split()
    histogram = Counter(tokens)
    return histogram


def compute_scores(query, candidates):
    """
    Given a sorted list of candidates of the form (episodeId, episodeName)
    (sorted by episodeId nums)
    return a list of (episodeId, episodeName, originalIdx, score) for each candidate, in
    descending order by score.  originalIdx is the index of candidate
    :param query: sentence
    :param candidates: sorted list of (season+episode id, episode name) tuples, sorted by season+episode
    :return: list of (season+episode id, episode name, score) tuples in original sorted oder
    """
    query_hist = make_histogram_for_sentence(query)
    result = []
    for i, candidate in enumerate(candidates):
        candidate_hist = make_histogram_for_sentence(candidate[1])
        score = compute_score(query_hist, candidate_hist)
        result.append((candidate[0], candidate[1], i, score))
    return sorted(result, key=lambda x: -x[3])


def compute_candidate_histograms(candidates):
    """
    Given a sorted list of candidates of the form (seasonId, name), sorted by seasonId
    Return a list of the form (seasonId, name, hist), where hist is the candidate's histogram
    :param query:
    :param candidates:
    :return:
    """
    return [(seasonId, episode_name, make_histogram_for_sentence(episode_name))
            for seasonId, episode_name in candidates]


def compute_score(query, candidate):
    """
    query and candidate are histograms of counts per term
    basically dictionaries where keys are terms and values are counts of the term
    we compute intersection over union
    intersection is sum over each term
      compute min(query[term], candidate[term])
    union is sum over each term
      compute max(query[term], candidate[term])
    score = intersection / union

    :param query: histogram of terms to counts
    :param candidate: histogram of terms to counts
    :return: score between 0 and 1 indicating simalrity of query to candidate
    """
    query_terms = set(query.keys())
    candidate_terms = set(candidate.keys())
    intersect_terms = query_terms.intersection(candidate_terms)
    union_terms = query_terms.union(candidate_terms)
    numerator = sum([min(query[term], candidate[term]) for term in intersect_terms])
    denominator = sum([max(query[term], candidate[term]) for term in union_terms])
    score = numerator / denominator
    return score


def get_episodes_for_series(tvdb, src_dir, series_dir, series_name, series_id):
    # todo generate a tuple of the original name (including extension) and the episode name (including extension)
    # todo if not a perfect match, generate partial matches and offer None of the above, querying user
    tvdb_episodes = get_tvdb_episodes_for_series(tvdb, series_id)
    tvdb_episodes = sorted(tvdb_episodes)
    print(f'Episodes for {series_name}:')
    for episode in tvdb_episodes:
        print(f'  {episode}')
    episodes = []
    src_path_base = f'{src_dir}/{series_dir}'
    return episodes


def plan(src_dir='/Volumes/EricRandiShare/iTunes_Library/TV Shows', dest_dir='/Volumes/video/TV Shows'):
    api_key = os.environ.get('TVDB_API_KEY')
    pin = os.environ.get('TVDB_PIN')
    tvdb = tvdb_v4_official.TVDB(api_key, pin)
    series = get_series_from_src(tvdb, src_dir)
    mappings = []
    for series_dir, series_name, series_id in series:
        episodes = get_episodes_for_series(tvdb, src_dir, series_dir, series_name, series_id)
        for filename, episode_name in episodes:
            src = f'{src_dir}/{series_dir}/{filename}'
            dest = f'{dest_dir}/{series_name}/{episode_name}'
            mapping = {'src': src, 'dest': dest}
            mappings.append(mapping)
    return series


if __name__ == '__main__':
    print(plan())
