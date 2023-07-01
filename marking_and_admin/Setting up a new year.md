# Setting up a new year

The file `marking_puller_2.py` is the entry point.

## Set up the spreadsheet

- in Google drive, make a copy of last year's _Details & marking 2022_ file.
- update the `MARKING_SPREADSHEET_ID` const with the ID from that new spreadsheet's URL.

In the past, the ID of the spreadsheet was hardcoded into the file. Now it's in the Codespace's env.

```
MARKING_SPREADSHEET_ID = "1wtTAM7A--ka7Lnog43L6jjo9kMCnDElCrTOBllEg4dA"  # 2019
MARKING_SPREADSHEET_ID = "1AjDu51VX26bIcLNMsr2iHq2BtrNEj91krxWKqjDW5aA"  # 2020
MARKING_SPREADSHEET_ID = "17KKMNIseRSo9IVNp-iaUCyEqbAR9tTYAcegzcvVgJFM"  # 2021
MARKING_SPREADSHEET_ID = "16tESt_4BUf-9-oD04suTprkd1O0oEl6WjzflF_avSKY"  # 2022
MARKING_SPREADSHEET_ID = "1DPBVy9DiVkdFBArOTRtj3L--f62KTnxyFFZrUXrobV0"  # 2023
```

## To mark work for the first time

- if this is a new computer, run `git config --global url."https://github.com/".insteadOf git@github.com:` or the git library will have a tantrum
- update the `THIS_YEAR` const
- delete `student.pickle` so that it forces a fresh pull
- if you have a fresh pull of the repo, you'll need a new `credentials.json` file.
  - follow this guide https://developers.google.com/workspace/guides/create-credentials
  - You need to make a web app Oauth set of creds, download it, and paste it into `marking_and_admin/credentials.json`
  - There's one ready to do in the CoDewords project in the google dashboard
  - run it, it'll fail on the `flow.run_local_server()` so it'll run the `flow.run_console()` and then it'll let you in.
  - you might need to enable the api, look at the error message, it has a link

TODO:

- congratulate everyone who has a full set of passing tests
