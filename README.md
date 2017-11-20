# redmine-slackbot
Slackbot for Redmine to add issues and assign them to yourself or others

## Overview

`redmine-slackbot` is a Slackbot that runs locally on a Redmine server providing
access to create, update, list, and close issues from Slack. In addition there
is now support for keywords to set estimated time, record time spent, and to
change the percent done for issues. Another new feature is a daily scrum
generator organizing open issues with time and percent done information.

The motivation to build this bot was to more easily access and track issues
with Redmine and not have to be on VPN to do so. Since the Slackbot runs
locally on the Redmine server it reaches out to Slack and listens for incoming
messages removing the need for a VPN connection.

## Install

```
pip install virtualenv
virtualenv env
source env/bin/activate
pip install slackclient
pip install python-redmine
```

## Configure

### Slack

1. Create [a bot named `@redminebot`](https://my.slack.com/services/new/bot) and
save the API token

 `export BOT_TOKEN="<slack api token>"`

2. Run the following Python script to get the bot's user ID for `BOT_ID`

 `python print_bot_id.py`

### Redmine

1. Get Redmine version from `http://redmine/admin/info`
2. Get API key from user profile that has Admin access (may have to enable REST
API in Admin if not seen)
3. Locate the IDs for all issue statuses
 * Go to `http://redmine/issue_statuses` and click on each status; the number in
the URL will be the ID
 * For example: the status ID is `5` from this URL `http://redmine/issue_statuses/5/edit`
4. Locate the time activity ID for recording time spent
 * Go to `http://redmine/enumerations` and select the activity to use for
recording time; the number in the URL will be the ID
 * For example: the activity ID is `12` from this URL `http://redmine/enumerations/12/edit`
5. Create a project called `General` or specify another project by its
identifier for all new issues to be created in
 * To find an existing project identifier, load the project page and look at the
URL; all text to the right of `project/` is the identifier
 * For example: the project identifier is `general` from the URL `http://redmine/projects/general`
6. Create a project called 'Top5' or specify another project by its identifier
for all Top 5 issues to use
7. Locate the ID for the tracker to use when creating new issues
 * Go to `http://redmine/trackers` and click on the tracker you would like to
use, the number in the URL will be the ID
 * For example: the tracker `Task` ID is `2` from this URL `http://redmine/trackers/2/edit`

### Saving config

1. Copy `run.sh.example` to `run.sh`

 `cp run.sh.example run.sh`

2. Edit `run.sh` and fill in the following variables for your environment
```
export REDMINE_HOST="http://localhost"
export REDMINE_EXT_HOST="http://172.0.0.1"
export REDMINE_VERSION="3.3.1"
export REDMINE_TOKEN="<redmine api token>"
export REDMINE_NEW_ID="1"
export REDMINE_INPROGRESS_ID="2"
export REDMINE_RESOLVED_ID="3"
export REDMINE_FEEDBACK_ID="4"
export REDMINE_CLOSED_ID="5"
export REDMINE_REJECTED_ID="6"
export REDMINE_HOLD_ID="7"
export REDMINE_ACTIVITY_ID="12"
export REDMINE_PROJECT="general"
export REDMINE_TOP5_PROJECT="top5"
export REDMINE_TRACKER_ID="2"
export BOT_ID="<from print_bot_id.py>"
export BOT_TOKEN="<slack api token>"
```

## Running

```
bash run.sh
```
Recommended to use `supervisor` if you want a long running service that is fault
tolerant

### Supervisord example conf

```
[program:redminebot]
command=/opt/redminebot/run.sh    ; the program (relative uses PATH, can take args)
numprocs=1                        ; number of processes copies to start (def 1)
directory=/opt/redminebot         ; directory to cwd to before exec (def no cwd)
autostart=true                    ; start at supervisord start (default: true)
autorestart=true                  ; restart on exit
stopasgroup=true                  ; send stop signal to the UNIX process group (default false)
user=redminebot                   ; setuid to this UNIX account to run the program
stderr_logfile=/var/log/redminebot.err.log
stdout_logfile=/var/log/redminebot.out.log
```

## Usage

Guide with examples on how to use `redminebot`, for help within Slack use `@redminebot help`

***IMPORTANT:*** For all operators below no spaces may be used as they will be treated as separate operators. The only exception are the operators `<comment>` and `<subject>` which are the last operators of commands that use them and can include spaces.

### Creating Issues - Assigned to You

#### `issue`

**Function:** For creating an issue in project `General` (or the project set by `REDMINE_PROJECT`)

**Usage:** `@redminebot issue <subject>`

* `<subject>` - Title for the created issue (can use **Estimate Time** keyword)

**Example:**
```
mikew [10:00]
@redminebot issue Push latest code

redminebot [10:00]
@mikew :white_check_mark: Created #535 Push latest code in project `General` assigned to Mike Wendt
```

#### `issuep`

**Function:** For creating an issue in a specified project

**Usage:** `@redminebot issuep <project> <subject>`

* `<project>` - Project name or ID
* `<subject>` - Title for the created issue (can use **Estimate Time** keyword)

**Example:**
```
mikew [10:00]
@redminebot issuep app Push latest code

redminebot [10:00]
@mikew :white_check_mark: Created #535 Push latest code in project `App` assigned to Mike Wendt
```

#### `issuepv`

**Function:** For creating an issue in a specified project with a specified version

**Usage:** `@redminebot issuepv <project> <version> <subject>`

* `<project>` - Project name or ID
* `<version>` - Version name or ID
* `<subject>` - Title for the created issue (can use **Estimate Time** keyword)

**Example:**
```
mikew [10:00]
@redminebot issuepv app v1 Push latest code

redminebot [10:00]
@mikew :white_check_mark: Created #535 Push latest code in project `App` with version `v1` assigned to Mike Wendt
```

### Creating Issues - Assigned to Others

#### `issueto`

**Function:** For creating an issue in project `General` (or the project set by `REDMINE_PROJECT`)

**Usage:** `@redminebot issueto <name> <subject>`

* `<name>` - User assigned to issue (can be first, last, or user name in Redmine)
* `<subject>` - Title for the created issue (can use **Estimate Time** keyword)

**Example:**
```
mikew [10:00]
@redminebot issueto josh Push latest code

redminebot [10:00]
@mikew :white_check_mark: Created #535 Push latest code in project `General` assigned to Josh Patterson
```

#### `issuepto`

**Function:** For creating an issue in a specified project

**Usage:** `@redminebot issuepto <project> <name> <subject>`

* `<project>` - Project name or ID
* `<name>` - User assigned to issue (can be first, last, or user name in Redmine)
* `<subject>` - Title for the created issue (can use **Estimate Time** keyword)

**Example:**
```
mikew [10:00]
@redminebot issuepto app josh Push latest code

redminebot [10:00]
@mikew :white_check_mark: Created #535 Push latest code in project `App` assigned to Josh Patterson
```

#### `issuepvto`

**Function:** For creating an issue in a specified project with a specified version

**Usage:** `@redminebot issuepv <project> <version> <name> <subject>`

* `<project>` - Project name or ID
* `<version>` - Version name or ID
* `<name>` - User assigned to issue (can be first, last, or user name in Redmine)
* `<subject>` - Title for the created issue (can use **Estimate Time** keyword)

**Example:**
```
mikew [10:00]
@redminebot issuepvto app v1 josh Push latest code

redminebot [10:00]
@mikew :white_check_mark: Created #535 Push latest code in project `App` with version `v1` assigned to Josh Patterson
```

### Updating Issues

#### `update`

**Function:** For updating an existing issue with a comment

**Usage:** `@redminebot update <issue #> <comment>`

* `<issue #>` - Issue ID to update
* `<comment>` - Comment to add to issue (can use **all** keywords)

**Example:**
```
mikew [10:00]
@redminebot update 535 Checked in code, still have to test

redminebot [10:00]
@mikew :memo: Updated #535 Push latest code with comment `Checked in code, still have to test`
```

### Changing Status of Issues

**Function:** For updating the status an existing issue with a comment

**Usage:** `@redminebot status <issue #> <status> <comment>`

* `<issue #>` - Issue ID to update
* `<status>` - Status to set the issue to, using one of the following keywords:

| Keyword | Issue Status | Marks Closed? | When to use? |
|---------|--------------|---------------|--------------|
|`new`|New|No|New issue that has not been started|
|`in`|In Progress|No|Issue is being actively worked on|
|`feed`|Feedback|No|Issue requires feedback to move forward|
|`resolve`|Resolved|No|Issue is thought to be fixed but requires verification from creator|
|`close`|Closed|Yes|Issue is completed|
|`reject`|Rejected|Yes|Issue is will no longer be considered|
|`hold`|Hold|No|Issue is a very low priority and will be re-evaluated in the future, no active work|

* `<comment>` - Comment to add to issue

**Example:**
```
mikew [10:00]
@redminebot status 535 in Working on this now

redminebot [10:00]
@mikew :white_check_mark: Changed status of #535 Push latest code to `In Progress` with comment `Working on this now`
```

### Closing & Rejecting Issues

#### `close`

**Function:** For closing an existing issue with a comment

**Usage:** `@redminebot close <issue #> <comment>`

* `<issue #>` - Issue ID to close
* `<comment>` - Comment to add to issue

**Example:**
```
mikew [10:00]
@redminebot close 535 Finished push

redminebot [10:00]
@mikew :white_check_mark: Closed #535 Push latest code with comment `Finished push`
```

#### `reject`

**Function:** For rejecting an existing issue with a comment

**Usage:** `@redminebot reject <issue #> <comment>`

* `<issue #>` - Issue ID to reject
* `<comment>` - Comment to add to issue (can use **all** keywords)

**Example:**
```
mikew [10:00]
@redminebot reject 535 No longer needed

redminebot [10:00]
@mikew :white_check_mark: Rejected #535 Push latest code with comment `No longer needed`
```

### Listing Issues

#### `list`

**Function:** For listing all issues assigned to you

**Usage:** `@redminebot list`

#### `listfor`

**Function:** For listing all issues assigned to specified user

**Usage:** `@redminebot listfor <name>`

* `<name>` - User assigned to issue (can be first, last, or user name in Redmine)

#### `listall`

**Function:** For listing all open issues

**Usage:** `@redminebot listall`

#### `listun`

**Function:** For listing all open issues that are unassigned

**Usage:** `@redminebot listun`

### Scrum Report

The `scrum(for)` commands create a scrum-like report listing all issues assigned to the user grouped by the following statuses in order: `In Progress, Feedback, Resolved, New, Hold`

Issues have additional detailed info, for example:
```
redminebot [10:00]
@mikew :newspaper: *Daily Scrum Report for Mike Wendt:*
*In Progress (1)*
>:zap: General #535 Push latest code (2017-11-20>?) [1.0h/0.5h] 50%
```
* `(2017-11-20>?)` - represents the start/due date
  * With the above example `?` is shown as there is no due date set
* `[1.0h/0.5h]` - represents time estimated/spent for this issue
  * `1.0h` is the estimated time for the issue which can be set by the **Estimate Time** keyword `$<t>h`
  * `0.5h` is the total spent time for the issue which can be set by the **Record Time** keyword `!<t>h`
* `50%` - represents the percent done of the issue
  * Percent done of the issue can be set by the **Percent Done** keyword `%<p>`

#### `scrum`

**Usage:** `@redminebot scrum`

#### `scrumfor`

**Usage:** `@redminebot scrumfor <name>`

* `<name>` - User assigned to issue (can be first, last, or user name in Redmine)

### End of Day Report

The `eod(for)` commands create a scrum-like report including all issues that were `Closed or Rejected` in the last day in addition to the output of the `scrum` commands. Issues share the same detailed information as `scrum` commands.

#### `eod`

**Usage:** `@redminebot eod`

#### `eodfor`

**Usage:** `@redminebot eodfor <name>`

* `<name>` - User assigned to issue (can be first, last, or user name in Redmine)

### Top 5

In order to capture longer running goals, Top 5 was created for management to track their most important items. Top 5 uses the standard issue priorities to rank these goals as well as allowing for multiple goals at the rank.

#### Listing Top 5

##### `t5`

**Usage:** `@redminebot t5`

##### `t5for`

**Usage:** `@redminebot t5for <name>`

* `<name>` - User assigned to issue (can be first, last, or user name in Redmine)

#### Adding/Ranking Top 5

##### `t5add`

**Function:** For creating a new Top 5 issue assigned to the current user

**Usage:** `@redminebot t5add <rank> <subject>`

* `<rank>` - Rank of Top 5 issue (must be 1-5)
* `<subject>` - Title for the created issue (can use **Estimate Time** keyword)

**Example:**
```
mikew [10:00]
@redminebot t5add 1 Top priority


redminebot [10:00]
@mikew :white_check_mark: Created Top 5 #536 Top priority with rank `1`
```

##### `t5rank`

**Function:** For re-ranking an existing Top 5 issue

**Usage:** `@redminebot t5rank <issue #> <rank> <comment>`

* `<issue #>` - Issue ID to re-rank
* `<rank>` - New rank of Top 5 issue (must be 1-5)
* `<comment>` - Comment to add to issue (can use **all** keywords)

**Example:**
```
mikew [10:00]
@redminebot t5rank 536 4 Reprioritizing to lower rank


redminebotAPP [10:00]
@mikew :memo: Updated Top 5 #536 Top priority to rank `4` with comment `Reprioritizing to lower rank`
```

#### Updating/Closing Top 5

In the `t5(for)` commands the issue numbers associated with the Top 5 goals are listed and can be used with `update` and `close` like any other issue. Keywords can also be used for time/progress tracking.

### Keywords

Keywords can be used to estimate/record time as well as change the percent done of an issue within comments/subjects

#### Keywords Used in `<comment>` or `<subject>`

##### Estimate Time - `$<t>h`
* Where `<t>` is an integer or decimal of the amount of time in hours to set as an estimate for this issue
* **NOTE:** When used in `<subject>` such as creating an `issue(pv)` or `t5add` this will be recorded to the issue but stripped from the title for readability
* Estimate time keywords ***overwrite*** the original value with the current value

**Example 1 - Issue Creation:**
```
mikew [10:00]
@redminebot issue Push latest code $1h

redminebot [10:00]
@mikew :white_check_mark: Created #535 Push latest code in project `General` assigned to Mike Wendt

>>> Redmine shows time estimate of 1 hour for #535
```

**Example 2 - Issue Update:**
```
mikew [10:00]
@redminebot update 535 Checked in code, still need to test $0.5h

redminebot [10:00]
@mikew :memo: Updated #535 Push latest code with comment `Checked in code, still need to test $0.5h`

>>> Redmine shows time estimate of 0.5 hour for #535
```

#### Keywords Used in `<comment>` ONLY

##### Record Time - `!<t>h`
* Where `<t>` is an integer or decimal of the amount of time in hours to record for this issue
* Record time keywords are ***cummulative*** and create a new time spent entry for the current date, with the amount `<t>` recorded to the issue specified

**Example - Issue Update:**
```
mikew [10:00]
@redminebot update 535 Checked in code, still need to test !0.5h

redminebot [10:00]
@mikew :memo: Updated #535 Push latest code with comment `Checked in code, still need to test !0.5h`

>>> Redmine has a new time spent entry of 0.5 hour for #535
```

##### Percent Done - `%<p>`
* Where `<p>` is an integer from 0-100 and represents the amount of the issue that is completed

**Example - Issue Update:**
```
mikew [10:00]
@redminebot update 535 Checked in code, still need to test %50

redminebot [10:00]
@mikew :memo: Updated #535 Push latest code with comment `Checked in code, still need to test %50`

>>> Redmine shows 50% done for #535
```

### Using Multiple Keywords

**Example - Issue Update:**
```
mikew [10:00]
@redminebot update 535 Checked in code, still need to test %50 !0.5h $1h

redminebot [10:00]
@mikew :memo: Updated #535 Push latest code with comment `Checked in code, still need to test %50 !0.5h $1h`

>>> Redmine shows for #535
  * 1 hour estimate
  * 50% done
  * new time spent entry of 0.5 hour
```

## Source

Thanks to https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
for the great starting point/guide

