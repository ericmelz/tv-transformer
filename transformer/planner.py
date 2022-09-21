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


SHOWS_TO_PROCESS = 10


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
        for i, series in list(enumerate(results))[:10]:
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
    series_names = []
    count = 0
    for directory in dirs:
        series = get_series(tvdb, directory)
        if series is not None:
            series_names.append(series)
        else:
            print(f"***WARNING: COULDN'T FIND SERIES MATCHING {directory}.  Skipping...")
        count += 1
        if count == SHOWS_TO_PROCESS:
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


def generate_mapping(src_path_base, src_episode_name, extension, dest_path_base, series_name, episode_id, episode_name):
    result = dict()
    result['src'] = f'{src_path_base}/{src_episode_name}{extension}'
    result['dest'] = f'{dest_path_base}/{series_name} - {episode_id} - {episode_name}{extension}'
    return result


def get_episodes_for_series(tvdb, src_dir, series_dir, series_name, series_id, dest_dir):
    """
    generate a list of pairs of the original name (including extension) and the episode name (including extension)
    :param tvdb:
    :param src_dir:
    :param series_dir:
    :param series_name:
    :param series_id:
    :param dest_dir:
    :return: list of pairs, mapping src file to dest file
    """
    # todo if not a perfect match, generate partial matches and offer None of the above, querying user
    tvdb_episodes = get_tvdb_episodes_for_series(tvdb, series_id)
    if not tvdb_episodes:
        raise Exception(f"Couldn't find any episodes for series {series_name}")
    tvdb_episodes = sorted(tvdb_episodes)
    tvdb_episodes = compute_candidate_histograms(tvdb_episodes)
    mappings = []
    rejects = []
    src_path_base = f'{src_dir}/{series_dir}'
    dest_path_base = f'{dest_dir}/{series_name}'
    src_episode_files = os.listdir(src_path_base)
    subdir_files = []
    # Handle case where subdirs can contain seasons
    for src_episode_file in src_episode_files:
        if os.path.isdir(f'{src_path_base}/{src_episode_file}'):
            subdir_files.extend(os.listdir(f'{src_path_base}/{src_episode_file}'))
    if len(subdir_files) > 0:
        src_episode_files = subdir_files
    for src_episode_file in src_episode_files:
        src_episode_name, extension = os.path.splitext(src_episode_file)
        scores = compute_scores(src_episode_name, tvdb_episodes)
        if scores[0][-1] == 1.0:
            episode_id, episode_name, idx, score = scores[0]
            mapping = generate_mapping(src_path_base, src_episode_name, extension, dest_path_base, series_name,
                                       episode_id, episode_name)
            mappings.append(mapping)
        else:
            print(f"Select episode for imperfectly matched episode '{series_name}' - '{src_episode_name}'")
            for i, (episode_id, episode_name, idx, score) in list(enumerate(scores))[:10]:
                print(f'{i}) {episode_id} - {episode_name}')
            print(f'{len(scores)}) None of the above')
            i = int(input())
            if i != len(scores):
                episode_id, episode_name, idx, score = scores[i]
                mapping = generate_mapping(src_path_base, src_episode_name, extension, dest_path_base, series_name,
                                           episode_id, episode_name)
                mappings.append(mapping)
            else:
                rejects.append(f'{src_path_base}/{src_episode_file}')

    return mappings, rejects


def plan(src_dir='/Volumes/EricRandiShare/iTunes_Library/TV Shows', dest_dir='/Volumes/video/TV Shows'):
    api_key = os.environ.get('TVDB_API_KEY')
    pin = os.environ.get('TVDB_PIN')
    tvdb = tvdb_v4_official.TVDB(api_key, pin)
    series = get_series_from_src(tvdb, src_dir)
    mappings = []
    rejects = []
    for series_dir, series_name, series_id in series:
        episode_mappings, episode_rejects = get_episodes_for_series(tvdb, src_dir, series_dir, series_name, series_id, dest_dir)
        mappings.extend(episode_mappings)
        rejects.extend(episode_rejects)
    return mappings, rejects


if __name__ == '__main__':
    main_mappings, main_rejects = plan()
    print('Mappings:')
    for mapping in main_mappings:
        print(mapping)
    print('\nRejects:')
    for reject in main_rejects:
        print(reject)
