"""All the work to actually mark the students' work."""

import json
import math
import os
import os.path
import pickle
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from io import StringIO
from itertools import repeat
<<<<<<< HEAD
from typing import Any, Union
=======
from typing import Any, Union  # , Optional, Set, Tuple, TypeVar
>>>>>>> aa05ff90144b910a132564720daa853f06f95ff5

import git
import pandas as pd
import requests
import ruamel.yaml as yaml
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pandas import DataFrame, Series


class RunCmd(threading.Thread):
    """Run a subprocess command, if it exceeds the timeout kill it.

    (without mercy)
    """

    def __init__(self, cmd, timeout):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.timeout = timeout

    def run(self):
        self.this_process = subprocess.Popen(self.cmd)
        self.this_process.wait()

    def Run(self):
        self.start()
        self.join(self.timeout)

        if self.is_alive():
            self.this_process.terminate()  # use self.p.kill() if process needs a kill -9
            self.join()


def build_spreadsheet_service():
    # If modifying these scopes, delete the file token.pickle.
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = None
    # Shows basic usage of the Sheets API. Prints values from a sample spreadsheet.
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            with open("temp_spreadsheet_creds.json", "w", encoding="utf-8") as tsc:
                tsc.write(os.getenv("SPREADSHEET_CREDS", ""))
            flow = InstalledAppFlow.from_client_secrets_file(
                "temp_spreadsheet_creds.json",
                scopes,
                redirect_uri="https://design-computing.github.io/",
            )
            # with open("temp_spreadsheet_creds.json", "w", encoding="utf-8") as tsc:
            #     tsc.write("")
            try:
                pass
                creds = flow.run_local_server()
            except OSError as os_e:
                print(os_e)
                creds = flow.run_console()
            except Exception as mystery_error:
                print(mystery_error)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("sheets", "v4", credentials=creds)
    return service


def write(service, data=[["These"], ["are"], ["some"], ["d", "entries"]]):
    comment_list = process_for_notes(data)
    # Writing values
    body = {"values": process_for_writing(data)}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=MARKING_SPREADSHEET_ID,
            range="testing!A2:Z100",
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )
    print(f"{result.get('updatedCells')} cells updated.")

    # Write comments
    body = {"requests": comment_list}
    result = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=MARKING_SPREADSHEET_ID, body=body)
        .execute()
    )
    print(f"{result.get('totalUpdatedCells')} cells updated.")


def process_for_writing(data):
    for i, row in enumerate(data):
        for j, item in enumerate(row):
            if isinstance(item, dict) or isinstance(item, yaml.comments.CommentedMap):
                data[i][j] = item.get("mark", str(dict(item)))
            elif (not isinstance(item, str)) and math.isnan(item):
                data[i][j] = ""
    return data


def process_for_notes(data):
    comments = []
    for i, row in enumerate(data):
        for j, item in enumerate(row):
            if isinstance(item, dict):
                readable_comment: str = prepare_comment(item)
                ss_comment_package: dict = set_comment(j, i, readable_comment)
                comments.append(ss_comment_package)
    return comments


def prepare_comment(item: dict) -> str:
    if "results" not in item.keys():
        fk_up = "some kind of major fuck up"
        return f"⚠ {item.get('bigerror', fk_up)} ⏱ {round(item.get('time', 0))}"
    test_results = []
    for res in item["results"]:
        icon = "👏" if res["value"] == 1 else "💩"
        test_results.append(f"{icon}: {res['name']}")
        # TODO: trace this back, and get rid of the "name" key, make it exercise_name, or test_name
    test_res = "\n".join(test_results)
    message = f"""{item['repo_owner']}
⏱ {round(item['time'])}
{test_res}
{item['mark']}/{item['of_total']}"""
    return message


def set_comment(x_coord, y_coord, comment, y_offset=1):
    request: dict[str, Any] = {
        "repeatCell": {
            "range": {
                "sheetId": 1704890600,
                "startRowIndex": y_coord + y_offset,
                "endRowIndex": y_coord + 1 + y_offset,
                "startColumnIndex": x_coord,
                "endColumnIndex": x_coord + 1,
            },
            "cell": {"note": comment},
            "fields": "note",
        }
    }
    return request


def get_df_from_csv_url(url: str, column_names: Union[list[str], bool] = False):
    """Get a csv of values from google docs."""
    res = requests.get(url)
    data = res.text
    if column_names:
        return pd.read_csv(StringIO(data), header=0, names=column_names)
    else:
        return pd.read_csv(StringIO(data))


def get_forks(
    org: str = "design-computing",
    repo: str = "me",
    force_inclusion_of_these_repos: list[str] = [],
) -> list[dict]:
    """Get a list of dicts of the user names and the git url for all the forks.

    Limits to repos created this year (THIS_YEAR as a const)

    Args:
        org (str, optional): The name of the Github user/organisation to pull
                              the forks from. Defaults to "design-computing".
        repo (str, optional): The name of the repo to get the forks of.
                              Defaults to "me".
        force_inclusion_of_these_repos (list[str], optional): _description_.
                              Defaults to [].

    Raises:
        Exception: _description_

    Returns:
        list[dict]: _description_
    """

    api = "https://api.github.com"
    limit = 100
    # TODO: #29 take these secrets out, put them in an env, and reset them
    client_id = os.getenv("CLIENT_ID_GITHUB", "")  # "040e86e3feed633710a0"
    secret = os.getenv(
        "SECRET_GITHUB", ""
    )  # "69588d73388091b5ff8635fd1a788ea79177bf69"
    url = (
        f"{api}/repos/{org}/{repo}/forks?"
        f"per_page={limit}&"
        f"client_id={client_id}&"
        f"client_secret={secret}'"
    )
    print("get forks from:\n", url)
    response = requests.get(url)
    if response.status_code == 200:
        forks = response.json()
        repos = [
            {"owner": fork["owner"]["login"], "git_url": fork["git_url"]}
            for fork in forks
            # filter for this year's repos
            if (fork["created_at"][:4] == THIS_YEAR)
            # a list of repos to get that aren't this year's,
            # to account for students retaking the course
            or (fork["owner"]["login"] in force_inclusion_of_these_repos)
        ]
        return repos
    else:
        rate_limit_message(response)
        raise Exception("GitHubFuckYouError")


def rate_limit_message(response):
    rate_limit = requests.get("https://api.github.com/rate_limit").json().get("rate")
    reset_time = str(
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rate_limit["reset"]))
    )
    print(
        response.status_code,
        response.reason,
        json.dumps(response.json(), indent=2),
        json.dumps(rate_limit, indent=2),
        "try again at" + reset_time,
        sep="\n",
    )


def update_repos(row: Series) -> str:
    """Git clone a repo, or if already cloned, git pull."""
    url = row["git_url"]
    https_url = url.replace("git://", "https://")
    owner = row["owner"]
    path = os.path.normpath(os.path.join(ROOTDIR, owner))
    time_now_str = datetime.now().strftime("%H:%M:%S")
    try:
        git.Repo.clone_from(https_url, path)
        print(f"{time_now_str}: new repo for {owner}")
        return ":) new"
    except git.GitCommandError as git_command_error:
        if "already exists and is not an empty directory" in git_command_error.stderr:
            if CHATTY:
                print(f"We already have {owner}, trying a pull. ({git_command_error})")
            try:
                repo = git.cmd.Git(path)
                try:
                    response = repo.pull()
                    print(f"{time_now_str}: pulled {owner}'s repo: {response}")
                    return str(response)
                except Exception as general_exception:
                    repo.execute(["git", "fetch", "--all"])
                    repo.execute(["git", "reset", "--hard", "origin/main"])
                    print(general_exception)
                    return "hard reset"
            except Exception as general_exception:
                if CHATTY:
                    print(
                        f"pull error: {row.name} {row.contactEmail}", general_exception
                    )
                return str(general_exception)
        elif "Connection timed out" in git_command_error.stderr:
            print(row)
            message = f"{row['owner']}: timeout error: {git_command_error}"
            print(message)
            return message
        else:
            message = f"{row['owner']}: unexpected error: {git_command_error}"
            print(message)
            return message
    except Exception as spare_error:
        message = f"clone error other than existing repo: {spare_error}"
        if CHATTY:
            print(message, f"{row.name} {row.contactEmail}", spare_error)
        return message


def try_to_kill(file_path: str):
    """Attempt to delete the file specified by file_path."""
    try:
        os.remove(file_path)
        print(f"deleted {file_path}")
    except Exception as mystery_error:
        if CHATTY:
            print(file_path, mystery_error)


<<<<<<< HEAD
def pull_all_repos(dir_list, hardcore_pull: bool = False):
    """Pull latest version of all repos."""

=======
def pull_all_repos(dir_list, CHATTY: bool = False, hardcore_pull: bool = False):
    """Pull latest version of all repos."""
    # TODO: make sure chatty is actually a global
>>>>>>> aa05ff90144b910a132564720daa853f06f95ff5
    of_total = len(dir_list)
    for i, student_repo in enumerate(dir_list):
        repo_is_here = os.path.join(ROOTDIR, student_repo)
        try:
            repo = git.cmd.Git(repo_is_here)
            if hardcore_pull:
                repo.execute(["git", "fetch", "--all"])
                repo.execute(["git", "reset", "--hard", "origin/main"])
            repo.pull()  # probably not needed, but belt and braces
            time_now_str = datetime.now().strftime("%H:%M:%S")
            print(f"{time_now_str}: {i}/{of_total} pulled {student_repo}'s repo")
        except Exception as mystery_exception:
            print(student_repo, mystery_exception)


def csv_of_details(dir_list):
    """Make a CSV of all the students."""
    results = []
    for student_repo in dir_list:
        path = os.path.join(ROOTDIR, student_repo, "aboutMe.yml")
        details = open(path).read()
        # replaces the @ symbol
        details = details.replace("@", "^AT^")
        # bumps unspaced values off the colon so that it parses
        details = re.sub(":(\w)", ": \g<1>", details)
        details = re.sub(" -", " None", details)
        details = details.replace("é", "e")
        details = details.replace("w:", "w: ")
        try:
            details = yaml.load(details, yaml.RoundTripLoader)
            details["repoName"] = student_repo
            details["error"] = False
            results.append(details)

            if details["studentNumber"] == "z1234567":
                print(student_repo, "hasn't updated")
        except Exception as mystery_error:
            print(details)
            results.append({"error": mystery_error, "repoName": student_repo})

    print("\n\nResults:")
    results_df = pd.DataFrame(results)
    # print(resultsDF)
    results_df.to_csv(os.path.join(CWD, "csv/studentDetails.csv"))
    fix_up_csv()


def fix_up_csv(path="csv/studentDetails.csv"):
    """Do replacements on csv.

    Mostly to undo tricks that were needed to deal with invalid yml
    """
    lines = []
    with open(path) as infile:
        for line in infile:
            line = line.replace("^AT^", "@")
            line = line.replace(",,", ",-,")
            lines.append(line)
    with open(path, "w", encoding="utf-8") as outfile:
        for line in lines:
            print(line)
            outfile.write(line)


def log_progress(message, logfile_name):
    """Write a message to a logfile."""
    completed_students_list = open(logfile_name, "a", encoding="utf-8")
    completed_students_list.write(message)
    completed_students_list.close()


def get_readmes(
    row, output="mark", print_labbooks=False
) -> Union[int, str, list[Union[int, str]]]:
    """Get the text, or the mark, or both related to log books."""
    # intro_set  = "TODO: Reflect on what you learned this set and what is still unclear."
    # intro_week = "TODO: Reflect on what you learned this week and what is still unclear."
    regex = r"TODO: Reflect.+unclear\."
    subst = ""
    path = os.path.join(ROOTDIR, row.owner)
    mark = 0
    all_readme = ""
    for i in range(1, 11):
        file_path = os.path.join(path, f"set{i}", "readme.md")
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    contents = file.read()
                    new = re.sub(regex, subst, contents, 0, re.MULTILINE).strip()
                    # print(i,"|", new, "|", len(new))
                    if len(new) > 0:
                        mark += 1
                        all_readme += f"w{i}: {new}\n\n"
                        if print_labbooks:
                            print(f"{row.owner}, w{i}: {new}")
            except UnicodeDecodeError:
                # if there's strange unicode in here, something must be going on!
                mark += 1

    if output == "mark":
        return mark
    elif output == "textList":
        return str(all_readme)
    else:
        return [mark, all_readme]


def get_readme_text(row) -> str:
    """Get the collected text of all the readme files."""
    text = get_readmes(row, output="textList", print_labbooks=False)
    assert isinstance(text, str)
    return text


def get_readme_mark(row) -> int:
    """Get the number of readmen files that are filled in."""
    mark = get_readmes(row, output="mark", print_labbooks=False)
    assert isinstance(mark, int)
    return mark


def test_in_clean_environment(
    row: Series,
    set_number: int,
    timeout: int = 5,
    logfile_name: str = "log.txt",
    temp_file_path: str = "temp_results.json",
    test_file_path: str = "test_shim.py",
) -> dict:
    pre = f"W{set_number}, {row.owner}:"
    marks_csv_exists = os.path.isfile(MARKS_CSV)
    if (
        "updated" in row.index
        and "Already up to date" in row.updated
        and not FORCE_MARKING
        and marks_csv_exists
    ):
        print(f"{pre} We don't need to mark this one")
        results_dict = get_existing_marks_from_csv(row, set_number)
    else:
        print(
            f"{pre} We need to mark this one ",
            "FORCE" if FORCE_MARKING else "🔰",
        )
        results_dict = mark_a_specific_person_week(
            row, set_number, timeout, logfile_name, temp_file_path, test_file_path
        )
    return results_dict


def get_existing_marks_from_csv(row: Series, set_number: int) -> dict:
    whole_csv_df = pd.read_csv(MARKS_CSV)
    this_person_df = whole_csv_df[whole_csv_df.owner == row.owner]
    try:
        # TODO: should this eval or json.loads?
        # json.loads has a problem because the strings in the keys are wrapped
        # in single quotes. I'm not sure how to save the csv with double quotes
        # as it's the default behaviour of to_csv.
        # results_dict = json.loads(str(this_person_df.iloc[0][f"set{set_number}"]))
        cell = this_person_df.iloc[0][f"set{set_number}"]
        results_dict = eval(str(cell))
        return results_dict
    except KeyError as k:
        print(f"no marks for set{set_number}", k)
        return {}
    except Exception as mystery_error:
        print(mystery_error)
        return {}


def mark_a_specific_person_week(
    row,
    set_number,
    timeout,
    logfile_name,
    temp_file_path,
    test_file_path,
):
    """Test a single student's work in a clean environment.

    This calls a subprocess that opens a fresh python environment, runs the
    tests and then saves the results to a temp file.

    Back in this process, we read that temp file, and then use its values to
    constuct a dictionary of results (or errors).

    The logging is just to see real time progress as this can run for a long
    time and hang the machine.
    """
    results_dict = {}
    log_progress(row.owner, logfile_name)
    start_time = time.time()

    python = sys.executable
    path_to_test_shim = get_safe_path("marking_and_admin", test_file_path)
    path_to_tests = get_safe_path("..", "course", f"set{set_number}", "tests.py")
    path_to_repo = get_safe_path(ROOTDIR, row.owner)

    test_args = [python, path_to_test_shim, path_to_tests, path_to_repo, row.owner]

    try:
        time_in = datetime.now()
        RunCmd(test_args, timeout).Run()  # this is unessarily complicated
        time_out = datetime.now()
        total_time_seconds = (time_out - time_in).total_seconds()
        # full_path = os.path.join(LOCAL, temp_file_path)
        with open(
            temp_file_path, "r", encoding="utf-8", errors="ignore"
        ) as temp_results:
            contents = temp_results.read()
            practical_timeout = math.floor(timeout * 0.98)
            if total_time_seconds > practical_timeout:
                print("\n\nAnnoying timeout ⌛⏳⌛⏳", "\n" * 5)
                message = (
                    "Execution timed out. "
                    + f"It was given {practical_timeout} seconds to complete."
                )
                results_dict = {"bigerror": message, "gh_username": row.owner}
            else:
                # TODO: catch empty string contents, and make the error message better
                results_dict = json.loads(contents)
                results_dict["bigerror"] = ":)"
        log_progress(f" good for w{set_number}\n", logfile_name)
    except json.JSONDecodeError as json_exception:
        results_dict = {
            "bigerror": str(json_exception).replace(",", "~"),
            "gh_username": row.owner,
        }  # the comma messes with the csv

        log_progress(f" bad {json_exception} w{set_number}\n", logfile_name)

    elapsed_time = time.time() - start_time
    results_dict["time"] = elapsed_time
    return results_dict


def get_safe_path(*parts):
    joined = os.path.join(*parts)
    abs_path = os.path.abspath(joined)
    return abs_path


def prepare_log(logfile_name, first_line="here we go:\n"):
    """Create or empty the log file."""
    completed_students_list = open(logfile_name, "w", encoding="utf-8")
    completed_students_list.write(first_line)
    completed_students_list.close()


def mark_work(dir_list, set_number, root_dir, df_please=True, timeout=5):
    """Mark the set's exercises."""
    logfile_name = "temp_completion_log"
    prepare_log(logfile_name)
    repeat_count = len(dir_list)  # for repeat count

    results = list(
        map(
            test_in_clean_environment,  # Function name
            dir_list,  # student_repo
            repeat(root_dir, repeat_count),  # root_dir
            repeat(set_number, repeat_count),  # set_number
            repeat(logfile_name, repeat_count),  # logfile_name
            repeat(timeout, repeat_count),  # timeout
        )
    )

    results_df = pd.DataFrame(results)
    csv_path = f"csv/set{set_number}marks.csv"
    results_df.to_csv(os.path.join(CWD, csv_path), index=False)
    for _ in [1, 2, 3]:
        # this is pretty dirty, but it gets tricky when you have
        # ,,, -> ,-,, because each intance needs to be replaced multiple times
        # TODO: #makeitnice
        fix_up_csv(path=csv_path)
    print("\n+-+-+-+-+-+-+-+\n\n")
    if df_please:
        return results_df


def get_details(row: Series) -> dict:
    try:
        path_to_about_me = os.path.abspath(
            os.path.join(ROOTDIR, row.owner, "aboutMe.yml")
        )
        with open(path_to_about_me, "r", encoding="utf-8") as y_file:
            details_raw_yaml = y_file.read()
        details: dict = dict(yaml.load(details_raw_yaml, yaml.RoundTripLoader))
        details["error"] = "👍"
        details["owner"] = row.owner
        return details
    except FileNotFoundError as fnf:
        print(row)
        print(fnf)
        error_message = {"error": "|".join(str(fnf).splitlines()), "owner": row.owner}
        return error_message


def construct_contact_email(details: dict) -> str:
    return f"""{details["contactEmail"]["firstBit"]}@{details["contactEmail"]["otherBit"]}"""


def get_last_commit(row: Series) -> str:
    path = os.path.join(ROOTDIR, row.owner)
    repo = git.cmd.Git(path)
    try:
        last_commit_date = str(repo.execute(["git", "log", "-1", "--format=%cd"]))
        return last_commit_date
    except git.GitCommandError as gce:
        print(gce)
        return "Fri Jun 23 11:11:11 2023 +1000"
        # TODO: find out why I was returning a no commits error


def mark_week(
    mark_sheet: DataFrame,
    set_number: int = 1,
    timeout: int = 10,
    active: bool = True,
):
    """Mark a single week for all students.

    Args:
        mark_sheet (Dataframe): A dataframe that describes who's
                                going to get marked.
        set_number (int, optional): The number of the set that we're marking.
                                    Defaults to 1.
        timeout (int, optional): number of seconds to try for before we cut
                                 this student off. Defaults to 10.
        active (bool, optional): Is this week being marked yet?.
                                 Defaults to True.

    Returns:
        Series: A series of the marks, or if not active yet, 0
    """
    if active:
        mark = mark_sheet.apply(
            test_in_clean_environment,
            args=(set_number, timeout),
            axis=1,
        )
        return mark
    else:
        return 0


def do_the_marking(
    this_year: str = "2023",
    rootdir: str = "../StudentRepos",
    chatty: bool = False,
    force_marking=False,
    marking_spreadsheet_id: str = "16tESt_4BUf-9-oD04suTprkd1O0oEl6WjzflF_avSKY",  # 2022
    marks_csv: str = "marks.csv",
    w1: dict[str, int | bool] = {"timeout": 5, "active": False},
    w2: dict[str, int | bool] = {"timeout": 5, "active": False},
    w3: dict[str, int | bool] = {"timeout": 5, "active": False},
    w4: dict[str, int | bool] = {"timeout": 5, "active": False},
    w5: dict[str, int | bool] = {"timeout": 5, "active": False},
    exam: dict[str, int | bool] = {"timeout": 5, "active": False},
    test_number_of_students: int = 0,
    force_repos: list[str] = [],
) -> None:
    """do_the_marking Runs tests against all student work.

    Args:
        this_year (str, optional): The year that you want to test. Defaults to "2023".
        rootdir (str, optional): Where you want to keep all the repos you're
                                  working with. Defaults to "../StudentRepos".
        chatty (bool, optional): Do you want it to be verbose? Defaults to False.
        force_marking (bool, optional): _description_. Defaults to False.
        marking_spreadsheet_id (str, optional): _description_. Defaults to
                                "16tESt_4BUf-9-oD04suTprkd1O0oEl6WjzflF_avSKY".
        mark_w1 (bool, optional): _description_. Defaults to True.
        mark_w2 (bool, optional): _description_. Defaults to False.
        mark_w3 (bool, optional): _description_. Defaults to False.
        mark_w4 (bool, optional): _description_. Defaults to False.
        mark_w5 (bool, optional): _description_. Defaults to False.
        mark_exam (bool, optional): _description_. Defaults to False.
        test_number_of_students (int, optional): _description_. Defaults to 0.
    """
    global THIS_YEAR
    THIS_YEAR = this_year
    global ROOTDIR
    ROOTDIR = rootdir
    global CHATTY
    CHATTY = chatty
    global FORCE_MARKING
    FORCE_MARKING = force_marking
    global MARKING_SPREADSHEET_ID
    MARKING_SPREADSHEET_ID = marking_spreadsheet_id
    global MARKS_CSV
    MARKS_CSV = marks_csv
    global FORCE_REPOS
    FORCE_REPOS = force_repos

    start_time = time.time()

    if not os.path.exists(ROOTDIR):
        os.makedirs(ROOTDIR)
    print("listdir(ROOTDIR):\n", os.listdir(ROOTDIR))

    students = get_student_data()

    mark_sheet = pd.DataFrame(students)
    if test_number_of_students > 0:
        mark_sheet = mark_sheet.sample(test_number_of_students)

    deets = pd.DataFrame(list(mark_sheet.apply(get_details, axis=1)))
    # temp:
    deets.drop(["officialEmail", "contactEmail"], axis=1, errors="ignore", inplace=True)
    mark_sheet = mark_sheet.merge(deets, on="owner")

    mark_sheet["updated"] = mark_sheet.apply(update_repos, axis=1)
    mark_sheet["last_commit"] = mark_sheet.apply(get_last_commit, axis=1)

    mark_sheet["set1"] = mark_week(
        mark_sheet, set_number=1, timeout=w1["timeout"], active=w1["active"]
    )
    mark_sheet["set2"] = mark_week(
        mark_sheet, set_number=2, timeout=w2["timeout"], active=w2["active"]
    )
    mark_sheet["set3"] = mark_week(
        mark_sheet, set_number=3, timeout=w3["timeout"], active=w3["active"]
    )
    mark_sheet["set4"] = mark_week(
        mark_sheet, set_number=4, timeout=w4["timeout"], active=w4["active"]
    )
    mark_sheet["set5"] = mark_week(
        mark_sheet, set_number=5, timeout=w5["timeout"], active=w5["active"]
    )
    mark_sheet["exam"] = mark_week(
        mark_sheet, set_number=8, timeout=exam["timeout"], active=exam["active"]
    )
    mark_sheet.drop(["name"], axis=1, errors="ignore", inplace=True)

    mark_sheet["readme_mark"] = mark_sheet.apply(get_readme_mark, axis=1)
    mark_sheet["readme_text"] = mark_sheet.apply(get_readme_text, axis=1)

    use_nice_spreadsheet_connection = False
    if not use_nice_spreadsheet_connection:
        convert_result_dicts_to_ints(mark_sheet)
    mark_sheet.to_csv(MARKS_CSV)

    if use_nice_spreadsheet_connection:
        data = [list(x) for x in mark_sheet.to_numpy()]
        service = build_spreadsheet_service()
        write(service, data=data)

    print("that took", (time.time() - start_time) / 60, "minutes")


def convert_result_dicts_to_ints(mark_sheet):
    """Convert the dict of results into a single mark.

    dict looks like this:
    {
      'of_total': 2,
      'mark': 0,
      'results': [
        {'value': 0, 'name': 'Exercise 2: debug the file'},
        {'value': 0, 'name': 'Lab book entry completed'}
      ],
      'week_number': 2,
      'localError': ':)',
      'repo_owner': 'rhiannon84',
      'bigerror': ':)',
      'time': 4.783979892730713
    }
    so we're just pulling the mark out, but it's fraught, so there's some checking.
    """

    def convert_one_results_dict_to_an_int(results_dict) -> int:
        try:
            return results_dict.get("mark", 0)
        except AttributeError as attr_err:
            print(attr_err)
            return 0

    for i in range(1, 6):
        mark_sheet[f"set{i}_data"] = mark_sheet[f"set{i}"]
        mark_sheet[f"set{i}"] = mark_sheet[f"set{i}"].apply(
            convert_one_results_dict_to_an_int
        )


def get_student_data():
    students = None
    file_name = "student.json"
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as data_file:
            students = json.load(data_file)
    else:
        force_repos = FORCE_REPOS
        students = get_forks(force_inclusion_of_these_repos=force_repos)
        with open("student.json", "w", encoding="utf-8") as data_file:
            json.dump(students, data_file, indent=2)
    return students


if __name__ == "__main__":
    print("👀  " * 30)
    print("don't be a silly billy, run from marking_puller.py")
