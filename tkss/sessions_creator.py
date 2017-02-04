import random
import os
import pandas
import datetime
import collections

import const

__author__ = 'Odedz'

class QueryDistanceMatrix(object):

    def __init__(self, size):
        self._size = size
        self._matrix = {}
        for r in xrange(self._size):
            self._matrix[r] = {r: 0}

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


def similarity(query_distance_matrix, s1, s2, size_s1=None, size_s2=None, result=None):
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
    result = similarity(query_distance_matrix, s1[:-1], s2[:-1], size_s1, size_s2, result)
    result = similarity(query_distance_matrix, s1[:-1], s2, size_s1, size_s2, result)
    result = similarity(query_distance_matrix, s1, s2[:-1], size_s1, size_s2, result)

    # Current step calculations
    result[(len(s1), len(s2))] = max(result[(len(s1)-1, len(s2)-1)] + (1-query_distance_matrix[s1[-1], s2[-1]]) * const.decay(size_s1-len(s1), size_s2-len(s2)),
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


Entry = collections.namedtuple("Entry", ["session", "query", "score", "iteration"])


def top_k_computation(s_cur, sessions, size, iteration=None):
    top_sessions = []
    for session_number, session in enumerate(sessions):
        for last_query_index in range(len(session)):
            similarity_score = similarity(matrix, s_cur, session[:last_query_index+1], len(s_cur), last_query_index + 1)[len(s_cur), last_query_index+1]
            e = Entry(session_number, last_query_index, similarity_score, iteration)
            if len(top_sessions) < size:
                top_sessions += [e]
            elif similarity_score > top_sessions[-1].score:
                top_sessions = top_sessions[:-1] + [e]
            top_sessions.sort(cmp=lambda e1, e2: -1 if e1.score > e2.score else 1 if e1.score < e2.score else 0)
    return top_sessions


def top_k_iterative_computation(s_cur, sessions):
    top_sessions = []
    last_scan_score = 0
    last_scan_iteration = -1
    for current_iteration, query in enumerate(s_cur):
        if last_scan_iteration == -1:
            top_sessions = top_k_computation([query], sessions, const.K + const.P)
            last_scan_score = top_sessions[-1].score
            last_scan_iteration = current_iteration
        else:
            update_top_sessions_score(current_iteration, top_sessions)
            k_score = top_sessions[const.K-1].score
            if last_scan_score >= k_score:
                full_scan(s_cur[:current_iteration], sessions)
                last_scan_score = top_sessions[-1].score
                last_scan_iteration = current_iteration
            else:
                last_scan_score = 1 + last_scan_score * (const.BETA ** 2)

    return top_sessions[:const.K]


if __name__ == '__main__':
    matrix = QueryDistanceMatrix(500)
    matrix.eager_evaluation()

    sessions = [[] for i in range(const.NUMBER_OF_SESSIONS)]

    for i in range(len(matrix)):
        sessions[random.randint(0, len(sessions)-1)].append(i)
    s_cur = sessions[0]
    print 'Session s_cur', len(s_cur), s_cur
    sessions = sessions[1:]
    for index, session in enumerate(sessions):
        print 'Session ', index, len(session), ':', session

    print 'Started'
    start_time = datetime.datetime.now()
    print top_k_iterative_computation(s_cur, sessions)
    print datetime.datetime.now() - start_time
