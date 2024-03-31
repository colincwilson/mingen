# profile mingen after run with
# python -m cProfile -o prof.txt 02_run_model.py

import pstats

stats = pstats.Stats('prof.txt')
stats = stats.sort_stats('tottime')
stats.print_stats(10)