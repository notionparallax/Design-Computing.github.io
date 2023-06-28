# -*- coding: UTF-8 -*-
"""Run tests on a specific repo.

This file is called by marking_puller.py

Its job is to be set up and torn down for every student so that there is no
namespace pollution. Its run as a subprocess. The args are where the tests are,
and where the repo is. In almost all cases the tests are the teacher tests, and
the repo changes for each student.

"""
import importlib.util
import json
import os
import sys

# from importlib import import_module
from time import sleep


def do_the_test(repo_path):
    """Run tests on a student's repo."""
    try:
        spec = importlib.util.spec_from_file_location("tests", TEST_PATH)
        test = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test)
        print("about to test", repo_path)
        results = test.theTests(repo_path)
        results["localError"] = ":)"
        return results
    except Exception as mystery_error:
        return {
            "of_total": 0,
            "mark": 0,
            "localError": str(mystery_error).replace(",", "~"),
            # the comma messes with the csv
        }


def results_as_json(repo_path):
    """Save the results to a temporary json file."""
    results = do_the_test(repo_path)
    results["repo_owner"] = OWNER
    print("\nresults:", json.dumps(results, indent=2), "\n")
    return json.dumps(results)


# __name__ == "__main__": <= this is going to be true always because of the way,
# that this file is loaded, but if it's being loaded in debug, i.e. from this
# file, then argv will be missing the extra info
if len(sys.argv) == 1:
    # 0:'C:\\Users\\ben\\Anaconda3\\python.exe'
    OWNER = "nico-dp"
    TEST_PATH = "C:\\Users\\bdoherty\\repos\\1161_py_course\\course\\set1\\tests.py"
    REPO_PATH = f"C:\\Users\\bdoherty\\repos\\1161_py_course\\StudentRepos\\{OWNER}"
else:
    TEST_PATH = os.path.normpath(sys.argv[1])
    REPO_PATH = os.path.normpath(sys.argv[2])
    OWNER = sys.argv[3]

print("\n In the shim\n◹◸◹◸◹◸◹◸◹◸◹◸\n\nsys.argv:")
for i, a in list(enumerate(sys.argv)):
    print(f"{i}: {a}")

print(
    f"""

TEST_PATH: {TEST_PATH}
REPO_PATH: {os.path.normpath(os.path.abspath(REPO_PATH))}
OWNER:     {OWNER}
"""
)

with open("temp_results.json", "w", encoding="utf-8") as temp_results:
    test_results = results_as_json(REPO_PATH)
    temp_results.write(test_results)
    sleep(0.50)

sleep(0.50)
