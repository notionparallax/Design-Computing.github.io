# -*- coding: UTF-8 -*-
"""Get the latest copy of all the repos.

This pulls the latest copy of all the repos
It can clone new repos if you delete the students pickle
"""
import os

from mark_functions import do_the_marking

MARKING_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_KEY", "")


if __name__ == "__main__" and MARKING_SPREADSHEET_ID != "":
    do_the_marking(
        this_year="2023",
        rootdir="../StudentRepos",
        chatty=False,
        force_marking=True,
        marking_spreadsheet_id=MARKING_SPREADSHEET_ID,
        marks_csv="marking_and_admin/marks.csv",
        mark_w1=True,
        mark_w2=True,
        mark_w3=True,
        mark_w4=True,
        mark_w5=False,
        mark_exam=False,
        test_number_of_students=0,  # if more than 0, will only mark the first N
    )
