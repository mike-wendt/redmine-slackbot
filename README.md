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
 * **NOTE:** To allow Top 5 Issues to have subtasks in any project, the settings
 need to be change in `Administration > Settings > Issue tracking` and change
 `Allow cross-project subtasks` to `With all projects`
 * The Top 5 Issues are based off of the person who creates them allowing them
 to be tracked but still assigned to other people
7. Locate the ID for the tracker to use when creating new issues
 * Go to `http://redmine/trackers` and click on the tracker you would like to
use, the number in the URL will be the ID
 * For example: the tracker `Task` ID is `2` from this URL `http://redmine/trackers/2/edit`
8. Create a new custom query to find watched issues for any user with the
following:
 * Name - `Your Watched Issues`
 * Visible - `to any users`
 * For all projects - `checked`
 * Filters
   * Status - `open`
   * Watcher - `is` and `<< me >>`
   * Assignee - `is not` and `<< me >>`
 * Save query
 * Click the link on the right-hand side `Your Watched Issues` under the section
 **Custom queries**, select this link and record the value of `query_id` for
 the value of `REDMINE_WATCHED_QUERY_ID`

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
export REDMINE_WATCHED_QUERY_ID="14"
export BOT_ID="<from print_bot_id.py>"
export BOT_TOKEN="<slack api token>"
```

## Running

```
bash run.sh
```
Recommended to use [supervisor](https://www.digitalocean.com/community/tutorials/how-to-install-and-manage-supervisor-on-ubuntu-and-debian-vps) if you want a long running service that is fault
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

For help within Slack use `@redminebot help` or see [Usage Guide](https://github.com/mike-wendt/redmine-slackbot/wiki)

## Source

Thanks to https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
for the great starting point/guide

