"""Run all the weeks of one person's tests.
"""
import os

for i in range(1, 10):
    os.system("python ../course/week{weekNumber}/tests.py".format(weekNumber=i))
