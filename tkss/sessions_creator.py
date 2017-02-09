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
                if first_query not in self._matrix or second_query not in self._matrix[first_query]:
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

current_iteration = 0
query_distance_matrix = QueryDistanceMatrix(5)
s_cur = []

def pretty_print_result(result):
    result_dict = {}
    for i, j in result.iterkeys():
        if i not in result_dict:
            result_dict[i] = {}
        result_dict[i][j] = result[(i, j)]
    print pandas.DataFrame(result_dict)


def _similarity(s1, s2, size_s1, size_s2, result):
    if (len(s1), len(s2)) in result:
        return

    # Update result with recursive calls
    _similarity(s1[:-1], s2[:-1], size_s1, size_s2, result)
    _similarity(s1[:-1], s2, size_s1, size_s2, result)
    _similarity(s1, s2[:-1], size_s1, size_s2, result)

    # Current step calculations
    result[(len(s1), len(s2))] = max(result[(len(s1)-1, len(s2)-1)] + (1-query_distance_matrix[s1[-1], s2[-1]]) * const.decay(size_s1-len(s1), size_s2-len(s2)),
                                     result[len(s1)-1, len(s2)] - const.DELTA,
                                     result[len(s1), len(s2)-1] - const.DELTA,
                                     0)


def similarity(s1, s2, previous_calculations=None):
    if not previous_calculations:
        result = {indexes: 0 for indexes in [(i, 0) for i in range(len(s1)+1)] + [(0, i) for i in range(len(s2)+1)]}
    else:
        iteration, result = previous_calculations
        result = map(lambda x: x * const.decay(current_iteration - iteration, 0), result)
    _similarity(s1, s2, len(s1), len(s2), result)
    return result


class Entry(object):
    def __init__(self, session, query_index, score_matrix, iteration):
        self._session = session
        self._query_index = query_index
        self._score_matrix = score_matrix
        self._iteration = iteration

    @property
    def score(self):
        self._score_matrix = similarity(s_cur, self._session[:self._query_index+1], (self._iteration, self._score_matrix))
        self._iteration = current_iteration
        return self._score_matrix[current_iteration, self._query_index]

    @property
    def upper_bound(self):
        counter = 0
        for i in range(self._iteration+1, current_iteration):
            counter += 1 * const.decay(current_iteration-i, 0)
        return self._score_matrix[self._iteration, self._query_index] * const.decay(current_iteration - self._iteration, 0) \
               + counter

    @property
    def lower_bound(self):
        return self._score_matrix[self._iteration, self._query_index] * const.decay(current_iteration - self._iteration, 0) \
               - (current_iteration - self._iteration) * const.DELTA


class SimilarityList(object):
    def __init__(self, max_length):
        self._max_length = max_length
        self._l = []

    def insert(self, e):
        if len(self._l) < self._max_length:
            self._l = self._l + [e]
        else:
            self._l.sort(cmp=lambda x, y: -1 if x.lower_bound > y.upper_bound else 1 if x.upper_bound < y.lower_bound else 0)
            last_item = self._l[-1]
            for session in filter(lambda x: x.upper_bound >= last_item.lower_bound and x.lower_bound <= last_item.upper_bound):
                session.score
            self._l.sort(cmp=lambda x, y: -1 if x.lower_bound > y.upper_bound else 1 if x.upper_bound < y.lower_bound else 0)

            if e.score > self._l[-1].upper_bound:
                self._l = self._l[:-1] + [e]
            elif e.score > self._l[-1].lower_bound:
                if e.score > self._l[-1].score:
                    self._l = self._l[:-1] + [e]


if __name__ == '__main__':
    query_distance_matrix.eager_evaluation()

    sessions = [[] for i in range(const.NUMBER_OF_SESSIONS)]

    for i in range(len(query_distance_matrix)):
        sessions[random.randint(0, len(sessions)-1)].append(i)
    s_cur = sessions[0]
    print 'Session s_cur', len(s_cur), s_cur
    sessions = sessions[1:]
    for index, session in enumerate(sessions):
        print 'Session ', index, len(session), ':', session

    query_distance_matrix.pretty_print()
    pretty_print_result(similarity(s_cur, sessions[0]))


# def compute_similarity(s_cur, sessions, iteration=None):
#     similarity_result = []
#     for session_number, session in enumerate(sessions):
#         subsession = []
#         for query in session:
#             subsession += [query]
#             similarity_score = similarity(matrix, s_cur, subsession, len(s_cur), len(subsession))[len(s_cur), len(subsession)]
#             similarity_result = similarity_result[:-1] + [SimilarityEntry(session_number, len(subsession), similarity_score, iteration)]
#             similarity_result.sort(cmp=lambda e1, e2: -1 if e1.score > e2.score else 1 if e1.score < e2.score else 0)    # TODO : use ordered list
#     return similarity_result


# def update_top_sessions_score(iteration, s_cur, top_sessions):
#     tmp_result = compute_similarity(s_cur, top_sessions[:const.K], iteration)[:const.K + const.P]
#     k_result_score = tmp_result[const.K-1].score
#     last_result_score = tmp_result[-1].score
#
#     for session in top_sessions[const.K:]:
#         upper_bound, lower_bound = get_bounds(session, iteration)
#         if upper_bound > last_result_score and lower_bound > last_result_score:
#             tmp_result = tmp_result[:-1] + session
#         elif upper_bound > last_result_score > lower_bound:
#             r = compute_similarity()
#
#         tmp_result.sort(cmp=lambda e1, e2: -1 if e1.score > e2.score else 1 if e1.score < e2.score else 0)
#
#     return tmp_result


# def top_k_iterative_computation(s_cur, sessions):
#     global current_iteration
#
#     top_sessions = []
#     last_scan_score = 0
#     last_scan_iteration = -1
#     for current_iteration, query in enumerate(s_cur):
#         if last_scan_iteration == -1:
#             top_sessions = compute_similarity([query], sessions, current_iteration+1)[:const.K + const.P]
#             last_scan_score = top_sessions[-1].score
#             last_scan_iteration = current_iteration
#         else:
#             update_top_sessions_score(current_iteration, s_cur[:current_iteration], top_sessions)
#             k_score = top_sessions[const.K-1].score
#             if last_scan_score >= k_score:
#                 compute_similarity(s_cur[:current_iteration], sessions, current_iteration+1)[:const.K + const.P] # TODO: replace with conditional computation
#                 last_scan_score = top_sessions[-1].score
#                 last_scan_iteration = current_iteration
#             else:
#                 last_scan_score = 1 + last_scan_score * (const.BETA ** 2)
#
#     return top_sessions[:const.K]


# if __name__ == '__main__':
#     matrix.eager_evaluation()
#
#     sessions = [[] for i in range(const.NUMBER_OF_SESSIONS)]
#
#     for i in range(len(matrix)):
#         sessions[random.randint(0, len(sessions)-1)].append(i)
#     s_cur = sessions[0]
#     print 'Session s_cur', len(s_cur), s_cur
#     sessions = sessions[1:]
#     for index, session in enumerate(sessions):
#         print 'Session ', index, len(session), ':', session
#
#     print 'Started'
#     start_time = datetime.datetime.now()
#     print top_k_iterative_computation(s_cur, sessions)
#     print datetime.datetime.now() - start_time
