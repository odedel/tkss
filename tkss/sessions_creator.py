import random
import os
import pandas
import datetime

import const

__author__ = 'Odedz'

class QueryDistanceMatrix(object):

    def __init__(self, size):
        self._size = size
        self._matrix = {}
        for r in xrange(self._size):
            self._matrix[r] = {r: 1}

    def __repr__(self):
        return self._matrix

    def __str__(self):
        s = ''
        for first_query in xrange(self._size):
            query_result = []
            for second_query in xrange(self._size):
                if first_query in self._matrix.keys() and second_query in self._matrix[first_query].keys():
                    query_result.append(self._matrix[first_query][second_query])
                else:
                    query_result.append(None)
            s += str(query_result) + os.linesep
        return s[:-1]

    def __len__(self):
        return self._size

    def __getitem__(self, cor):
        first_query, second_query = cor

        if first_query >= self._size or second_query >= self._size:
            raise ValueError

        if first_query in self._matrix and second_query in self._matrix[first_query]:
            return self._matrix[first_query][second_query]

        return self._gen_distance(first_query, second_query)

    def eager_evaluation(self):
        for first_query in self._matrix.iterkeys():
            for second_query in self._matrix.iterkeys():
                if first_query not in self._matrix or second_query not in self._matrix[second_query]:
                    self._gen_distance(first_query, second_query)

    def pretty_print(self):
        print pandas.DataFrame(self._matrix)

    def _gen_distance(self, first_query, second_query):
        while True:
            candidate_distance = random.random()

            for third_query, second_to_third_distance in self._matrix[second_query].iteritems():
                if third_query in self._matrix[first_query].keys():
                    first_to_third_distance = self._matrix[first_query][third_query]
                    if candidate_distance + second_to_third_distance < first_to_third_distance:
                        continue

            for third_query, first_to_third_distance in self._matrix[first_query].iteritems():
                if third_query in self._matrix[second_query].keys():
                    third_to_second_distance = self._matrix[second_query][third_query]
                    if first_to_third_distance + third_to_second_distance < candidate_distance:
                        continue

            self._matrix[first_query][second_query] = candidate_distance
            self._matrix[second_query][first_query] = candidate_distance

            return candidate_distance


def similarity(query_similarity_matrix, s1, s2, size_s1=None, size_s2=None, result=None):
    if not size_s1:
        size_s1 = len(s1)
    if not size_s2:
        size_s2 = len(s2)
    if not result:
        result = {}

    if not s1 or not s2:
        result[len(s1), len(s2)] = 0
        return result

    if (len(s1), len(s2)) in result:
        return result

    # Recursive calls
    result = similarity(query_similarity_matrix, s1[:-1], s2[:-1], size_s1, size_s2, result)
    result = similarity(query_similarity_matrix, s1[:-1], s2, size_s1, size_s2, result)
    result = similarity(query_similarity_matrix, s1, s2[:-1], size_s1, size_s2, result)

    # Current step calculations
    result[(len(s1), len(s2))] = max(result[(len(s1)-1, len(s2)-1)] + query_similarity_matrix[s1[-1], s2[-1]] * const.decay(size_s1-len(s1), size_s2-len(s2)),
                                     result[len(s1)-1, len(s2)] - const.DELTA,
                                     result[len(s1), len(s2)-1] - const.DELTA,
                                     0)
    return result


def pretty_print_result(result):
    result_dict = {}
    for i, j in result.iterkeys():
        if i not in result_dict:
            result_dict[i] = {}
        result_dict[i][j] = result[(i, j)]
    print pandas.DataFrame(result_dict)


if __name__ == '__main__':
    top_k = []

    matrix = QueryDistanceMatrix(500)
    matrix.eager_evaluation()

    sessions = [[] for i in range(const.NUMBER_OF_SESSIONS)]

    for i in range(len(matrix)):
        sessions[random.randint(0, len(sessions)-1)].append(i)
    for index, session in enumerate(sessions):
        print 'Session ', index, ': ', session

    s_cur = sessions[0]

    print 'Started'
    start = datetime.datetime.now()

    for index, session in enumerate(sessions):
        similarity_score = similarity(matrix, s_cur, session, len(s_cur), len(session))[len(s_cur), len(session)]
        if len(top_k) < const.K:
            top_k.append((index, similarity_score))
        elif similarity_score > top_k[-1][1]:
            top_k = top_k[:-1] + [(index, similarity_score)]
            top_k.sort(cmp=lambda x, y: -1 if x[1] > y[1] else 1 if x[1] < y[1] else 0)

    print datetime.datetime.now() - start

    print top_k