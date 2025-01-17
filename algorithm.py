import numpy as np
import osu_file_parser as osu_parser
from functools import reduce
import math


def parse_osu_file(file_path):
    p = osu_parser.parser(file_path)
    p.process()
    return p.get_parsed_data()

def is_empty(some_list):
    for item in some_list:
        if item != 0:
            return False
    return True

# Helper function for asperity.
def asperity_help(note_counts_wrt_columns):
    note_counts_wrt_columns.sort()
    column_gaps = []
    for i in range(len(note_counts_wrt_columns) - 1):
        column_gaps.append(note_counts_wrt_columns[i + 1] - note_counts_wrt_columns[i])
    return sum(list(map(lambda x: math.sqrt(x), column_gaps))) ** 2


class star_calculator():
    def __init__(self):
        self.column_count = 0
        self.columns = []
        self.note_starts = []
        self.note_ends = []
        self.note_types = []
        self.od = -1

    def calculate_SR(self, file_path):
        p = parse_osu_file(file_path)
        self.column_count = p[0]
        self.columns = p[1]
        self.note_starts = p[2]
        self.note_ends = p[3]
        self.note_types = p[4]
        self.od = p[5]
        # print(self.columns)
        # print(len(self.calculate_asperity()))

    def calculate_X(self):
        pass


    def smoother_forX(self):
        note_value = self.note_value_forX(self)
        asperities = self.calculate_asperity(self)
        intensities = self.intensity_forX(self)

        pass


    # Calculate Note value v for X Dimension.
    # v = 2T + 1. T = length of the note.
    # Return: array of note values for every note.
    def note_value_forX(self):
        vs = []
        for i in range(len(self.note_types)):
            if self.note_types[i] == 128:
                vs.append(2 * (self.note_ends[i] - self.note_starts[i]) + 1)
            # T = 0 for single note.
            else:
                vs.append(1)
        return vs

    # Calculate asperity. The asperity is count inside every [-0.5s, +0.5s] window.
    # Step = 10ms here.
    def calculate_asperity(self):
        time_interval_start = 0
        left_half_columns = right_half_columns = -1
        start_evaluating_note_index = 0
        if (self.column_count % 2 == 0):
            asperities = []
            left_half_columns = right_half_columns = self.column_count / 2
            while time_interval_start <= self.note_starts[-1]:
                local_asperity = self.asperity_in_window(left_half_columns, right_half_columns, time_interval_start, start_evaluating_note_index)
                asperities.append(local_asperity[0])
                start_evaluating_note_index = local_asperity[1]
                time_interval_start += 10
            return asperities
        else:
            asperities_1 = asperities_2 = []
            left_half_columns = (self.column_count - 1) / 2
            right_half_columns = left_half_columns + 1
            while time_interval_start <= self.note_starts[-1]:
                local_asperity = self.asperity_in_window(left_half_columns, right_half_columns, time_interval_start, start_evaluating_note_index)
                asperities_1.append(local_asperity[0])
                local_asperity = self.asperity_in_window(right_half_columns, left_half_columns, time_interval_start, start_evaluating_note_index)
                asperities_2.append(local_asperity[0])
                start_evaluating_note_index = local_asperity[1]
                time_interval_start += 10
            two_sets_of_asperities = np.array([asperities_1, asperities_2])
            return np.average(two_sets_of_asperities, axis = 0).tolist()



    def asperity_in_window(self, left_half_columns, right_half_columns, time_interval_start, start_evaluating_note_index):
        note_counts_wrt_columns = [0] * self.column_count
        next_start_note_index = start_evaluating_note_index

        for i in range(start_evaluating_note_index, len(self.note_starts)):
            if (time_interval_start + 500 > self.note_starts[i] >= time_interval_start - 500):
                count = 0
                note_counts_wrt_columns[self.columns[i]] += 1
                # Step is 10ms, so next time starts from the first note that is included in the next window.
                if (count == 0 and time_interval_start + 10 <= self.note_starts[i]):
                    next_start_note_index = i
                    count += 1
        left_half_columns_int = int(left_half_columns)
        note_counts_wrt_left_columns = note_counts_wrt_columns[:left_half_columns_int]
        note_counts_wrt_right_columns = note_counts_wrt_columns[left_half_columns_int:]
        if (is_empty(note_counts_wrt_left_columns) and is_empty(note_counts_wrt_right_columns)): # If no notes at all:
            return (1/3, next_start_note_index)
        else:

            note_count = sum(note_counts_wrt_left_columns) + sum(note_counts_wrt_right_columns)
            return ((asperity_help(note_counts_wrt_left_columns) + asperity_help(note_counts_wrt_right_columns)) / note_count, next_start_note_index)



    # Calculate f(t) for X.
    # Per column.
    def intensity_forX(self):
        note_starts_wrt_columns = [[] for x in range(7) ]
        intensities_wrt_columns = [[] for x in range(7) ]
        for i in range(len(self.note_starts)):
            note_starts_wrt_columns[self.columns[i]].append(self.note_starts[i])
        for j in range(self.column_count):
            intensities_wrt_columns.append(self.intensity_forX_per_column(note_starts_wrt_columns[j]), j)
        return intensities_wrt_columns

    def intensity_forX_per_column(self, note_starts_wrt_column,column)  :
        delta_t = []
        for i in range(len(note_starts_wrt_column) - 1):
            delta_t.append(note_starts_wrt_column[i + 1] - note_starts_wrt_column[i])
        x = (64.5 - math.ceil(self.od * 3))/500
        intensity_func = lambda t: 1/(t * (t + 0.3 * math.sqrt(x)))
        intensities = list(map(intensity_func, delta_t))
        return intensities

    def calculate_Y(self):
        pass

    def note_value_for_gt(self):
        vs = []
        for i in range(len(self.note_starts) - 1):
            vs.append(2*(self.note_starts[i + 1] - self.note_starts[i])+1)
        return vs

    def intensity_for_gt(self):
        pass

    def calculate_Z(self):
        pass
