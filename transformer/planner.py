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


def get_series_names(dirname='/Volumes/EricRandiShare/iTunes_Library/TV Shows'):
    dirs = os.listdir(dirname)
    print(dirs)
    return dirs


if __name__ == '__main__':
    series_names = get_series_names()