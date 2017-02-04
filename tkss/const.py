__author__ = 'Odedz'

DELTA = 0.2
BETA = 0.95


def decay(index_s1, index_s2):
    return BETA ** (index_s1 + index_s2)
