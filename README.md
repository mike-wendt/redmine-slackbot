# redmine-slackbot
Slackbot for Redmine to add issues and assign them to yourself or others

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

1. Create [a bot named `@redminebot`](https://my.slack.com/services/new/bot) and save the API token
 
 `export BOT_TOKEN="<slack api token>"`
 
2. Run the following Python script to get the bot's user ID for `BOT_ID`
 
 `python print_bot_id.py`

### Redmine

1. Get Redmine version from http://redmine/admin/info
2. Get API key from user profile that has Admin access (may have to enable REST API in Admin if not seen)

### Saving config

1. Copy `run.sh.example` to `run.sh` 

 `cp run.sh.example run.sh`

2. Edit `run.sh` and fill in the following variables for your environment
```
export REDMINE_HOST="http://localhost"
export REDMINE_EXT_HOST="http://172.0.0.1"
export REDMINE_VERSION="3.3.1"
export REDMINE_TOKEN="<redmine api token>"
export BOT_ID="<from print_bot_id.py>"
export BOT_TOKEN="<slack api token>"
```

## Running

```
bash run.sh
```
Recommended to use `supervisor` if you want a long running service that is fault tolerant

## Source

Thanks to https://www.fullstackpython.com/blog/build-first-slack-bot-python.html for the great starting point/guide
