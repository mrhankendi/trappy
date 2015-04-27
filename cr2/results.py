#!/usr/bin/python
# $Copyright:
# ----------------------------------------------------------------
# This confidential and proprietary software may be used only as
# authorised by a licensing agreement from ARM Limited
#  (C) COPYRIGHT 2015 ARM Limited
#       ALL RIGHTS RESERVED
# The entire notice above must be reproduced on all authorised
# copies and copies may only be made to the extent permitted
# by a licensing agreement from ARM Limited.
# ----------------------------------------------------------------
# File:        results.py
# ----------------------------------------------------------------
# $
#
"""Compare runs 2

Second version of the compare runs script, to compare two traces of
the power allocator governor"""

import os
import collections, csv, re
import pandas as pd
from matplotlib import pyplot as plt

class CR2(pd.DataFrame):
    """A DataFrame-like class for storing benchmark results"""
    def __init__(self, *args, **kwargs):
        super(CR2, self).__init__(*args, **kwargs)
        self.ax = None

    def init_fig(self):
        _, self.ax = plt.subplots()

    def enlarge_axis(self, data):
        """Make sure that the axis don't clobber some of the data"""

        (_, _, plot_y_min, plot_y_max) = plt.axis()

        concat_data = pd.concat(data[s] for s in data)
        data_min = min(concat_data)
        data_max = max(concat_data)

        # A good margin can be 10% of the data range
        margin = (data_max - data_min) / 10
        if margin < 1:
            margin = 1

        update_axis = False

        if data_min <= plot_y_min:
            plot_y_min = data_min - margin
            update_axis = True

        if data_max >= plot_y_max:
            plot_y_max = data_max + margin
            update_axis = True

        if update_axis:
            self.ax.set_ylim(plot_y_min, plot_y_max)

    def plot_results_benchmark(self, benchmark, title=None):
        """Plot the results of the execution of a given benchmark

        A title is added to the plot if title is not supplied
        """

        if title is None:
            title = benchmark.replace('_', ' ')
            title = title.title()

        self[benchmark].plot(ax=self.ax, kind="bar", title=title)
        plt.legend(bbox_to_anchor=(1.05, .5), loc=6)

    def plot_results(self):
        for bench in self.columns.levels[0]:
            self.plot_results_benchmark(bench)

def get_run_number(metric):
    found = False
    run_number = None

    if re.match("Overall_Score|score|FPS", metric):
        found = True

        match = re.search("(.+)[ _](\d+)", metric)
        if match:
            run_number = int(match.group(2))
            if match.group(1) == "Overall_Score":
                run_number -= 1
        else:
            run_number = 0

    return (found, run_number)

def get_results(dirname=".", id=None):
    """Return a pd.DataFrame with the results

    The DataFrame's rows are the scores.  The first column is the
    benchmark name and the second the id within it.  For benchmarks
    that have a score result, that's what's used.  For benchmarks with
    FPS_* result, that's the score.  E.g. glbenchmarks "score" is it's
    fps.

    An optional id argument can be passed.  If supplied, it overrides
    the id in the results file.

    """

    bench_dict = collections.OrderedDict()

    with open(os.path.join(dirname, "results.csv")) as fin:
        results = csv.reader(fin)

        for row in results:
            (is_result, run_number) = get_run_number(row[3])

            if is_result:
                if id:
                    run_id = id
                else:
                    run_id = re.sub(r"_\d+", r"", row[0])

                bench = row[1]
                try:
                    result = int(row[4])
                except ValueError:
                    result = float(row[4])

                if bench in bench_dict:
                    if run_id in bench_dict[bench]:
                        if run_number not in bench_dict[bench][run_id]:
                            bench_dict[bench][run_id][run_number] = result
                    else:
                        bench_dict[bench][run_id] = {run_number: result}
                else:
                    bench_dict[bench] = {run_id: {run_number: result}}

    bench_dfrs = {}
    for bench, run_id_dict in bench_dict.iteritems():
        bench_dfrs[bench] = pd.DataFrame(run_id_dict)

    return CR2(pd.concat(bench_dfrs.values(), axis=1, keys=bench_dfrs.keys()))

def combine_results(data):
    """Combine two DataFrame results into one

    The data should be an array of results like the ones returned by
    get_results() or have the same structure.  The returned DataFrame
    has two column indexes.  The first one is the benchmark and the
    second one is the key for the result.

    """

    res_dict = {}
    for benchmark in data[0].columns.levels[0]:
        concat_objs = [d[benchmark] for d in data]
        res_dict[benchmark] = pd.concat(concat_objs, axis=1)

    combined = pd.concat(res_dict.values(), axis=1, keys=res_dict.keys())

    return CR2(combined)
