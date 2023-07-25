# -*- coding: UTF-8 -*-
"""Get the latest copy of all the repos.

This pulls the latest copy of all the repos
It can clone new repos if you delete the students pickle
"""
import os
import sys

from mark_functions import do_the_marking

MARKING_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_KEY", "")


if __name__ == "__main__" and MARKING_SPREADSHEET_ID != "":
    sys.path.insert(0, "/workspaces/me/set2")

    do_the_marking(
        this_year="2023",
        rootdir="../StudentRepos",
        chatty=False,
        force_marking=True,
        marking_spreadsheet_id=MARKING_SPREADSHEET_ID,
        marks_csv="marking_and_admin/marks.csv",
        mark_w1={"timeout":15, "active":True},
        mark_w2={"timeout":15, "active":True},
        mark_w3={"timeout":30, "active":True},
        mark_w4={"timeout":50, "active":True},
        mark_w5={"timeout":50, "active":False},
        mark_exam={"timeout":45, "active":True},
        test_number_of_students=0,  # if more than 0, will only mark a sample of N repos
        force_repos=["lvl-lim", "JeWang"],
    )
elif MARKING_SPREADSHEET_ID == "":
    print(
        "The MARKING_SPREADSHEET_ID is supposed to come from the env. Either "
        "Ben hasn't granted you permissions, or the env is broken in some way."
        "It's stored in the codespace's secrets."
    )
