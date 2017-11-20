import os
import time
import re
import sys
import traceback
from datetime import datetime
from slackclient import SlackClient
from redminelib import Redmine

"""
    Load environment variables
"""
REDMINE_HOST = os.environ.get('REDMINE_HOST')
REDMINE_EXT_HOST = os.environ.get('REDMINE_EXT_HOST')
REDMINE_VERSION = os.environ.get('REDMINE_VERSION')
REDMINE_TOKEN = os.environ.get('REDMINE_TOKEN')
REDMINE_NEW_ID = os.environ.get('REDMINE_NEW_ID')
REDMINE_INPROGRESS_ID = os.environ.get('REDMINE_INPROGRESS_ID')
REDMINE_FEEDBACK_ID = os.environ.get('REDMINE_FEEDBACK_ID')
REDMINE_RESOLVED_ID = os.environ.get('REDMINE_RESOLVED_ID')
REDMINE_CLOSED_ID = os.environ.get('REDMINE_CLOSED_ID')
REDMINE_REJECTED_ID = os.environ.get('REDMINE_REJECTED_ID')
REDMINE_HOLD_ID = os.environ.get('REDMINE_HOLD_ID')
REDMINE_ACTIVITY_ID = os.environ.get('REDMINE_ACTIVITY_ID')
REDMINE_PROJECT = os.environ.get('REDMINE_PROJECT')
REDMINE_TOP5_PROJECT = os.environ.get('REDMINE_TOP5_PROJECT')
REDMINE_TRACKER_ID = os.environ.get('REDMINE_TRACKER_ID')
BOT_ID = os.environ.get('BOT_ID')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

"""
    CONSTANTS
"""
AT_BOT = "<@" + BOT_ID + ">"
STATUSES = {
    'new': (REDMINE_NEW_ID, "New"),
    'in': (REDMINE_INPROGRESS_ID, "In Progress"),
    'feed': (REDMINE_FEEDBACK_ID, "Feedback"),
    'resolve': (REDMINE_RESOLVED_ID, "Resolved"),
    'close': (REDMINE_CLOSED_ID, "Closed"),
    'reject': (REDMINE_REJECTED_ID, "Rejected"),
    'hold': (REDMINE_HOLD_ID, "Hold")
}
STATUS_NAME_LOOKUP = {
    REDMINE_NEW_ID: "New",
    REDMINE_INPROGRESS_ID: "In Progress",
    REDMINE_FEEDBACK_ID: "Feedback",
    REDMINE_RESOLVED_ID: "Resolved",
    REDMINE_CLOSED_ID: "Closed",
    REDMINE_REJECTED_ID: "Rejected",
    REDMINE_HOLD_ID: "Hold"
}
# Order of issues in scrum and eod report
SCRUM_ORDER = [REDMINE_INPROGRESS_ID, REDMINE_FEEDBACK_ID, \
              REDMINE_RESOLVED_ID, REDMINE_NEW_ID, REDMINE_HOLD_ID]
EOD_ORDER = [REDMINE_CLOSED_ID, REDMINE_REJECTED_ID]

"""
    CONSTANT regexps
"""
ESTIMATE_RE = re.compile(r"[$]([0-9.]+)[h]")
RECORD_RE = re.compile(r"[!]([0-9.]+)[h]")
PERCENT_RE = re.compile(r"[%]([0-9]{1,3})")
HTTP_RE = re.compile(r"(\<(https?:\/\/[^\|]*)\|([^\>]*)\>)")

"""
    Instantiate Slack & Redmine clients
"""
sc = SlackClient(BOT_TOKEN)
rc = Redmine(REDMINE_HOST, version=REDMINE_VERSION, key=REDMINE_TOKEN)

"""
    Slack command parser
"""
def handle_command(command, channel, user, username):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = ":question: Unknown/invalid command - Try `help` for a list of supported commands"
    commands = command.split()
    try:
        if commands:
            operator = commands[0].lower()
            s = " "
            msg = s.join(commands[1:])
            if operator == "issueto" and len(commands) > 2:
                assigneduser = commands[1]
                msg = s.join(commands[2:])
                response = create_issue(msg, username, assigneduser, REDMINE_PROJECT)
            elif operator == "issue" and len(commands) > 1:
                response = create_issue(msg, username, username, REDMINE_PROJECT)
            elif operator == "issuepto" and len(commands) > 3:
                project = commands[1]
                assigneduser = commands[2]
                msg = s.join(commands[3:])
                response = create_issue(msg, username, assigneduser, project)
            elif operator == "issuep" and len(commands) > 2:
                project = commands[1]
                msg = s.join(commands[2:])
                response = create_issue(msg, username, username, project)
            elif operator == "issuepvto" and len(commands) > 4:
                project = commands[1]
                version = commands[2]
                assigneduser = commands[3]
                msg = s.join(commands[4:])
                response = create_issue_version(msg, username, assigneduser, project, version)
            elif operator == "issuepv" and len(commands) > 3:
                project = commands[1]
                version = commands[2]
                msg = s.join(commands[3:])
                response = create_issue_version(msg, username, username, project, version)
            elif operator == "assign" and len(commands) > 3:
                issue = commands[1]
                assigneduser = commands[2]
                msg = s.join(commands[3:])
                response = assign_issue(msg, issue, username, assigneduser)
            elif operator == "update" and len(commands) > 2:
                issue = commands[1]
                msg = s.join(commands[2:])
                response = update_issue(msg, issue, username)
            elif operator == "status" and len(commands) > 3:
                issue = commands[1]
                status = commands[2]
                msg = s.join(commands[3:])
                response = status_issue(msg, issue, status, username)
            elif operator == "close" and len(commands) > 2:
                issue = commands[1]
                msg = s.join(commands[2:])
                response = close_issue(msg, issue, username)
            elif operator == "reject" and len(commands) > 2:
                issue = commands[1]
                msg = s.join(commands[2:])
                response = reject_issue(msg, issue, username)
            elif operator == "list":
                response = list_issues(username)
            elif operator == "listall":
                response = list_all_issues()
            elif operator == "listun":
                response = list_unassigned_issues()
            elif operator == "listfor" and len(commands) > 1:
                listuser = commands[1]
                response = list_issues(listuser)
            elif operator == "scrum":
                response = daily_scrum(username)
            elif operator == "scrumfor" and len(commands) > 1:
                listuser = commands[1]
                response = daily_scrum(listuser)
            elif operator == "eod":
                response = daily_eod(username)
            elif operator == "eodfor" and len(commands) > 1:
                listuser = commands[1]
                response = daily_eod(listuser)
            elif operator == "t5":
                response = list_top5(username)
            elif operator == "t5for" and len(commands) > 1:
                t5user = commands[1]
                response = list_top5(t5user)
            elif operator == "t5add" and len(commands) > 2:
                rank = commands[1]
                msg = s.join(commands[2:])
                response = create_top5(msg, username, rank)
            elif operator == "t5rank" and len(commands) > 3:
                issue = commands[1]
                rank = commands[2]
                msg = s.join(commands[3:])
                response = rank_top5(msg, issue, username, rank)
            elif operator == "help":
                response = show_commands()
            elif int(commands[0]) > 0:
                issue = int(commands[0])
                response = "Issue: "+issue_url(issue)
    except ValueError:
        respone = show_commands()
    except RuntimeError as e:
        response = e[0]
    message = "<@" + user + "> " + response
    sc.api_call("chat.postMessage", channel=channel, \
                          text=message, as_user=True)

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                try:
                    user = output['user']
                    profile = sc.api_call("users.info", user=output['user'])
                    # username used for searching in redmine; try last,
                    # then first, then display
                    if 'last_name' in profile['user']['profile'] \
                      and profile['user']['profile']['last_name'] != '':
                        username = profile['user']['profile']['last_name']
                    elif 'first_name' in profile['user']['profile'] \
                      and profile['user']['profile']['first_name'] != '':
                        username = profile['user']['profile']['first_name']
                    elif 'display_name' in profile['user']['profile'] \
                      and profile['user']['profile']['display_name'] != '':
                        username = profile['user']['profile']['display_name']
                    else:
                        username = profile['user']['name']
                    # return text after the @ mention, whitespace removed
                    return output['text'].split(AT_BOT)[1].strip(), \
                           output['channel'], user, username
                except:
                    traceback.print_exc(file=sys.stderr)
                    raise RuntimeError(":x: Unable to find `"+user \
                                       +"` in Redmine")
    return None, None, None, None

"""
    Slack command handler functions
"""
def show_commands():
    """
        Return ist of commands that bot can handle
    """
    return ":hammer_and_wrench: *List of supported commands:*\n" \
            "*Issue Link Command:*\n" \
            "> `<issue #>` - returns a link to the referenced issue number\n" \
            "*Issue Commands:*\n" \
            "> `issue <subject>` - creates new issue assigned to you\n" \
            "> `issueto <name> <subject>` - creates new issue assigned to `<name>`\n" \
            "> `issuep <project> <subject>` - creates new issue assigned to you in `<project>` \n" \
            "> `issuepto <project> <name> <subject>` - creates new issue assigned to `<name>` in `<project>`\n" \
            "> `issuepv <project> <version> <subject>` - creates new issue assigned to you in `<project>` with version `<version>`\n" \
            "> `issuepvto <project> <version> <name> <subject>` - creates new issue assigned to `<name>` in `<project>` with version `<version>`\n" \
            "> `assign <issue #> <name> <comment>` - assigns issue to `<name>`\n" \
            "> `update <issue #> <comment>` - updates issue with comment\n" \
            "> `status <issue #> <status> <comment>` - changes status of an issue\n" \
            ">\t`<status>` must be one of the following: "+list_status_keys()+"\n" \
            "> `close <issue #> <comment>` - closes issue with comment\n" \
            "> `reject <issue #> <comment>` - rejects issue with comment\n" \
            "*List Commands:*\n" \
            "> `list` - lists all open issues assigned to you\n" \
            "> `listfor <name>` - lists all open issues assigned to `<name>`\n" \
            "> `listall` - lists all open issues\n" \
            "> `listun` - lists all open and unassigned issues\n" \
            "*Scrum & End of Day Commands:*\n" \
            "> `scrum` - generates daily scrum for you\n" \
            "> `scrumfor <name>` - generates daily scrum for `<name>`\n" \
            "> `eod` - generates end of day report for you\n" \
            "> `eodfor <name>` - generates end of day report for `<name>`\n" \
            "*Top 5 Commands:*\n" \
            "> `t5` - lists your Top 5\n" \
            "> `t5for <user>` - lists Top 5 for user\n" \
            "> `t5add <rank> <subject>` - creates Top 5 with `<rank>` (1-5)\n" \
            "> `t5rank <issue #> <rank> <comment>` - changes the Top 5 issue to `<rank>` (1-5) with comment\n" \
            "_*NOTE:*_ Top 5 issues can be updated & closed with general issue commands\n" \
            ":key: *List of keywords:*\n" \
            "_This keyword can be used in `<subject>` or `<comment>` _\n" \
            "> Estimate time - `$<t>h` - where `<t>` is an integer/decimal for # of hours\n" \
            "_These keywords can be used in `<comment>` text only_\n" \
            "> Record time - `!<t>h` - where `<t>` is an integer/decimal for # of hours\n" \
            "> Percent done - `%<p>` - where `<p>` is an integer from 0-100\n\n" \
            ":information_source: *Further Help:*\n" \
            "> Meaning of emojis used to tag issues, see <https://github.com/mike-wendt/redmine-slackbot/wiki/Issue-Emoji-Meanings|Emoji Meanings>\n" \
            "> Full help with examples, see <https://github.com/mike-wendt/redmine-slackbot/wiki|Usage Guide>\n"


def assign_issue(text, issue, username, assigneduser):
    user = rm_get_user(username)
    assigned = rm_get_user(assigneduser)
    issue = rm_get_issue(issue)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        rm_update_issue(issue=issue.id, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent, assigned=assigned.id)
        return ":bookmark: Assigned "+issue_subject_url(issue.id,issue.subject)+" to "+assigned.firstname+" "+assigned.lastname+" with comment `"+text+"`"
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue assign failed")

def update_issue(text, issue, username):
    user = rm_get_user(username)
    issue = rm_get_issue(issue)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        rm_update_issue(issue=issue.id, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent)
        return ":memo: Updated "+issue_subject_url(issue.id,issue.subject)+" with comment `"+text+"`"
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue update failed")

def status_issue(text, issue, status, username):
    user = rm_get_user(username)
    issue = rm_get_issue(issue)
    statusid, statusname = get_status(status)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        rm_update_issue(issue=issue.id, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent, status=statusid)
        return ":white_check_mark: Changed status of "+issue_subject_url(issue.id,issue.subject)+" to `"+statusname+"` with comment `"+text+"`"
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue status update failed")

def close_issue(text, issue, username):
    user = rm_get_user(username)
    issue = rm_get_issue(issue)
    today = local2utc(datetime.today()).date()
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        if not percent:
            percent = 100
        rm_update_issue(issue=issue.id, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent, status=REDMINE_CLOSED_ID, due=today)
        return ":white_check_mark: Closed "+issue_subject_url(issue.id,issue.subject)+" with comment `"+text+"`"
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue closing failed")

def reject_issue(text, issue, username):
    user = rm_get_user(username)
    issue = rm_get_issue(issue)
    today = local2utc(datetime.today()).date()
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        if not percent:
            percent = 100
        rm_update_issue(issue=issue.id, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent, status=REDMINE_REJECTED_ID, due=today)
        return ":white_check_mark: Rejected "+issue_subject_url(issue.id,issue.subject)+" with comment `"+text+"`"
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue rejecting failed")

def create_issue(text, username, assigneduser, project_name):
    user = rm_get_user(username)
    assigned = rm_get_user(assigneduser)
    project = rm_get_project(project_name)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, clean_text) = parse_remove_estimate(text)
        issue = rm_create_issue(estimate=estimate, subject=clean_text, rcn=rcn, assigned=assigned.id, project=project.identifier)
        return ":white_check_mark: Created "+issue_subject_url(issue.id,issue.subject)+" in project `"+project.name+"` assigned to "+assigned.firstname+" "+assigned.lastname
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue creation failed")

def create_issue_version(text, username, assigneduser, project_name, version_name):
    user = rm_get_user(username)
    assigned = rm_get_user(assigneduser)
    project = rm_get_project(project_name)
    version = rm_get_version(project_name, version_name)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, clean_text) = parse_remove_estimate(text)
        issue = rm_create_issue(estimate=estimate, subject=clean_text, rcn=rcn, assigned=assigned.id, project=project.identifier, version=version.id)
        return ":white_check_mark: Created "+issue_subject_url(issue.id,issue.subject)+" in project `"+project.name+"` with version `"+version.name+"` assigned to "+assigned.firstname+" "+assigned.lastname
        return ""+str(version)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue creation failed")

def list_issues(username):
    user = rm_get_user(username)
    try:
        result = rm_get_user_issues(user.id, 'open')
        response = ""
        if len(result) > 0:
            response = ":book: *Open Issues Assigned to "+user.firstname+" "+user.lastname+":*\n"
            for issue in result:
                response += issue_detail(issue, extended=False, user=False)
        else:
            response = ":thumbsup_all: No open issues assigned to "+user.firstname+" "+user.lastname
        return response
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: List operation failed")

def list_all_issues():
    try:
        result = rm_get_all_issues('open',False)
        response = ""
        if len(result) > 0:
            response = ":book: *All Open Issues:*\n"
            for issue in result:
                response += issue_detail(issue, extended=False, user=True)
        else:
            response = ":thumbsup_all: No open issues found"
        return response
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: List all operation failed")

def list_unassigned_issues():
    try:
        result = rm_get_all_issues('open',True)
        response = ""
        if len(result) > 0:
            response = ":book: *All Open and Unassigned Issues:*\n"
            for issue in result:
                response += issue_detail(issue, extended=False, user=False)
        else:
            response = ":thumbsup_all: No open and unassigned issues found"
        return response
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: List unassigned operation failed")

def daily_scrum(username):
    user = rm_get_user(username)
    try:
        response = ":newspaper: *Daily Scrum Report for "+user.firstname+" "+user.lastname+":*\n"
        issues_found = False
        for s in SCRUM_ORDER:
            result = rm_get_user_issues(user.id, s)
            if len(result) > 0:
                issues_found = True
                response += "*_"+STATUS_NAME_LOOKUP[s]+" ("+str(len(result))+")_*\n"
                for issue in result:
                    response += issue_detail(issue, extended=True, user=False)
        if not issues_found:
            response += ":thumbsup_all: No issues found!\n"
        return response
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Scrum operation failed")

def daily_eod(username):
    user = rm_get_user(username)
    try:
        response = ":newspaper: *End of Day Report for "+user.firstname+" "+user.lastname+":*\n"
        issues_found = False
        for s in EOD_ORDER:
            result = rm_get_user_issues_today(user.id, s)
            if len(result) > 0:
                issues_found = True
                response += "*_"+STATUS_NAME_LOOKUP[s]+" ("+str(len(result))+")_*\n"
                for issue in result:
                    response += issue_detail(issue, extended=True, user=False)
        for s in SCRUM_ORDER:
            result = rm_get_user_issues(user.id, s)
            if len(result) > 0:
                issues_found = True
                response += "*_"+STATUS_NAME_LOOKUP[s]+" ("+str(len(result))+")_*\n"
                for issue in result:
                    response += issue_detail(issue, extended=True, user=False)
        if not issues_found:
            response += ":thumbsup_all: No issues found!\n"
        return response
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: EOD operation failed")

def list_top5(username):
    user = rm_get_user(username)
    try:
        top5_found = False
        response = ":pushpin: *Top 5 for "+user.firstname+" "+user.lastname+":*\n"
        for p in range(5, 0, -1):
            result = rm_get_top5(user.id, p)
            rank = 6 - p
            cnt = 1
            for issue in result:
                if len(result) > 1:
                    response += top5_detail(issue, rank, cnt)
                    cnt += 1
                else:
                    response += top5_detail(issue, rank)
                top5_found = True
        if not top5_found:
            response = ":thumbsup_all: No Top 5 for "+user.firstname+" "+user.lastname
        return response
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Top 5 list operation failed")

def create_top5(text, username, rank):
    user = rm_get_user(username)
    priority = parse_rank(rank)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, clean_text) = parse_remove_estimate(text)
        issue = rm_create_issue(estimate=estimate, subject=clean_text, rcn=rcn, assigned=user.id, project=REDMINE_TOP5_PROJECT, priority=priority)
        return ":white_check_mark: Created Top 5 "+issue_subject_url(issue.id,issue.subject)+" with rank `"+str(rank)+"`"
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Top 5 creation failed")

def rank_top5(text, issue, username, rank):
    user = rm_get_user(username)
    issue = rm_get_issue(issue)
    priority = parse_rank(rank)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        rm_update_issue(issue=issue.id, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent, priority=priority)
        return ":memo: Updated Top 5 "+issue_subject_url(issue.id,issue.subject)+" to rank `"+str(rank)+"` with comment `"+text+"`"
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Top 5 rank update failed")

"""
    Redmine functions
"""
def rm_get_user(username):
    try:
        return rc.user.filter(name=username)[0]
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed to find user `"+username+"` in Redmine")

def rm_get_project(project):
    try:
        return rc.project.get(project)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed to find project `"+project+"` in Redmine")

def rm_get_version(project, version):
    try:
        proj = rm_get_project(project)
        for v in proj.versions:
            if v.name.lower() == version.lower():
                return v
        raise RuntimeError(":x: Failed to find version `"+version+"` within project `"+project+"` in Redmine")
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed to find version `"+version+"` within project `"+project+"` in Redmine")

def rm_get_issue(issueid):
    try:
        return rc.issue.get(int(issueid))
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed to find issue ID `"+issueid+"` in Redmine")

def rm_get_user_issues(userid, status):
    if not status:
        status = 'open'
    try:
        return rc.issue.filter(sort='project', assigned_to_id=userid, status_id=status)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed to find issues for user `"+username+"` in Redmine")

def rm_get_user_issues_today(userid, status):
    if not status:
        status = 'open'
    try:
        today = datetime.today().date()
        return rc.issue.filter(sort='project', assigned_to_id=userid, status_id=status, updated_on=today)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed to find issues for user `"+username+"` in Redmine")

def rm_get_all_issues(status, unassigned):
    if not status:
        status = 'open'
    if not unassigned:
        unassigned = False
    try:
        if unassigned:
            return rc.issue.filter(sort='project', assigned_to_id='!*', status_id=status)
        else:
            return rc.issue.filter(sort='project', status_id=status)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed to find issues for user `"+username+"` in Redmine")

def rm_impersonate(userlogin):
    try:
        return Redmine(REDMINE_HOST, version=REDMINE_VERSION, key=REDMINE_TOKEN, impersonate=userlogin)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed impersonate user `"+userlogin+"` in Redmine")

def rm_create_issue(estimate, assigned, subject, project, rcn, version=None, priority=None):
    params = dict()
    if estimate:
        params['estimated_hours'] = estimate
    if subject:
        params['subject'] = parse_remove_http(subject)
    if assigned:
        params['assigned_to_id'] = assigned
    if version:
        params['fixed_version_id'] = version
    if priority:
        params['priority_id'] = priority
    if not project:
        project = REDMINE_PROJECT

    try:
        return rcn.issue.create(project_id=project, tracker_id=REDMINE_TRACKER_ID, **params)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue creation failed")

def rm_update_issue(issue, estimate, percent, notes, record, rcn, status=None, due=None, priority=None, assigned=None):
    params = dict()
    if estimate:
        params['estimated_hours'] = estimate
    if percent:
        params['done_ratio'] = percent
    if status:
        params['status_id'] = status
    if due:
        params['due_date'] = due
    if notes:
        params['notes'] = parse_replace_http(notes)
    if record:
        rm_record_time(issue, record, rcn)
    if priority:
        params['priority_id'] = priority
    if assigned:
        params['assigned_to_id'] = assigned

    try:
        result = rcn.issue.update(issue, **params)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue update failed")

def rm_record_time(issueid, record, rcn):
    try:
        today = local2utc(datetime.today()).date()
        result = rcn.time_entry.create(issue_id=issueid, spent_on=today, hours=record, activity_id=REDMINE_ACTIVITY_ID)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Issue record time spent failed")

def rm_sum_time_entries(issueid):
    try:
        issue = rc.issue.get(issueid)
        total = 0.0
        for te in issue.time_entries:
            total += te.hours
        return total
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed in summing time entries")

def rm_get_top5(userid, priority):
    try:
        return rc.issue.filter(sort='created_on', project_id=REDMINE_TOP5_PROJECT, assigned_to_id=userid, status_id='open', priority_id=priority)
    except:
        traceback.print_exc(file=sys.stderr)
        raise RuntimeError(":x: Failed to find Top 5 for user `"+username+"` in Redmine")

"""
    Status functions
"""
def get_status(status):
    try:
        return STATUSES.get(status)[0], STATUSES.get(status)[1]
    except:
        raise RuntimeError(":x: Unknown status code, use one of the following:\n"+list_statuses())

def list_status_keys():
    response = ""
    for i in STATUSES:
        response += "`"+i+"` "
    return response

def list_statuses():
    response = ""
    for i in STATUSES:
        response += "`"+i+"` - "+STATUSES[i][1]+"\n"
    return response

"""
    Response formatting functions
"""
def issue_url(issueid):
    return "<"+REDMINE_EXT_HOST+"/issues/"+str(issueid)+"|#"+str(issueid)+">"

def issue_subject_url(issueid, subject):
    return "<"+REDMINE_EXT_HOST+"/issues/"+str(issueid)+"|#"+str(issueid)+" "+subject+">"

def issue_time_percent_details(issue):
    estimated = check_key_exists(issue, 'estimated_hours')
    start = check_key_exists(issue, 'start_date')
    due = check_key_exists(issue, 'due_date')
    response = ""
    spent = rm_sum_time_entries(issue.id)
    if start:
        response += " ("+str(issue.start_date)+">"
    else:
        response += " (?>"
    if due:
        response += str(issue.due_date)+")"
    else:
        response += "?)"
    if estimated:
        response += " ["+str(issue.estimated_hours)+"h/"+str(spent)+"h]"
    else:
        response += " [?/"+str(spent)+"h]"
    response += " "+str(issue.done_ratio)+"%"
    return response

def issue_tag(created, updated):
    cdate = utc2local(created).date()
    udate = utc2local(updated).date()
    today = datetime.today().date()

    if cdate == today:
        return ":zap:"
    else:
        if (today - udate).days == 0:
            return ":sunny:"
        elif (today - udate).days == 1:
            return ":mostly_sunny:"
        elif (today - udate).days == 2:
            return ":barely_sunny:"
        elif (today - udate).days == 3:
            return ":cloud:"
        elif (today - udate).days > 3 and (today - udate).days < 8:
            return ":rain_cloud:"
        elif (today - udate).days >= 8:
            return ":snowflake:"
    return ":grey_question:"

def issue_version(issue):
    if check_key_exists(issue, 'fixed_version'):
        return " - "+issue.fixed_version.name
    else:
        return ""

def issue_user(issue):
    if check_key_exists(issue, 'assigned_to'):
        return " :bookmark: "+issue.assigned_to.name
    else:
        return ""

def issue_detail(issue, extended=False, user=False):
    version = issue_version(issue)
    tag = issue_tag(issue.created_on, issue.updated_on)
    username = issue_user(issue)
    response = "> "+tag+" "+issue.project.name+version+" "+ \
               issue_subject_url(issue.id, issue.subject)
    if extended:
        response += issue_time_percent_details(issue)
    if user:
        response += username

    response += "\n"
    return response

def top5_detail(issue, rank, cnt=None):
    tag = issue_tag(issue.created_on, issue.updated_on)
    username = issue_user(issue)

    rank_out = str(rank)
    if cnt:
        rank_out += "."+str(cnt)
    rank_out += ") "

    response = "> "+tag+" "+rank_out+" "+issue_subject_url(issue.id, issue.subject)+" "+ \
               issue_time_percent_details(issue)

    response += "\n"
    return response

"""
    Time conversion helper functions
"""
def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return utc + offset

def local2utc(local):
    epoch = time.mktime(local.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return local - offset

"""
    Keyword/text parsing functions
"""
def parse_keywords(msg):
    """
        Parse message finding keywords starting with '!', '$' followed by a number
        (can be decimal) followed by 'h' for hours

        '!' - record time; '$' - estimated time

        exp:
        '$5h' - change time estimate of current issue to 5 hours
        '!1h' - record 1 hour of time to the current issue

        Parse message finding keywords starting with '%' followed by a number
        0-100

        '%' - percent done

        exp:
        '%100' - change percent done to %100
        '%10' - change percent done to %10
    """
    estimate = ESTIMATE_RE.search(msg)
    record = RECORD_RE.search(msg)
    percent = PERCENT_RE.search(msg)

    if estimate:
        estimate = estimate.group(1)
    if record:
        record = record.group(1)
    if percent:
        percent = int(percent.group(1))

        if percent > 100:
            percent = 100
        elif percent < 0:
            percent = 0
        else:
            percent = int(round(percent/10.0)*10)

    return estimate, record, percent

def parse_remove_estimate(msg):
    """
        Parse message finding keywords starting with '$' followed by a number
        (can be decimal) followed by 'h' for hours for the estimated time and
        return the time in hours as well as the text with the keyword removed
    """
    estimate = ESTIMATE_RE.search(msg)

    if estimate:
        estimate = estimate.group(1)
        msg = ESTIMATE_RE.sub('', msg)

    return estimate, msg

def parse_remove_http(msg):
    """
        Strip extra HTTP formatting inserted by slack for HTTP addresses

        For subjects that we don't want a URL in title of issue

        Example:
        "<http://google.com|google.com>" --> "google.com"
    """
    matches = HTTP_RE.finditer(msg)

    if matches:
        for m in matches:
            msg = msg.replace(m.group(1),m.group(3))

    return msg

def parse_replace_http(msg):
    """
        Strip extra HTTP formatting inserted by slack for HTTP addresses

        For comments where we want links preserved

        Example:
        "<http://google.com|google.com>" --> "http://google.com"
    """
    matches = HTTP_RE.finditer(msg)

    if matches:
        for m in matches:
            msg = msg.replace(m.group(1),m.group(2))

    return msg

def parse_rank(rank):
    """
        Ensure rank is 1-5 and invert to match priorities
    """
    rank = int(rank)
    if rank >= 1 and rank <= 5:
        return int(6 - rank)
    else:
        raise RuntimeError(":x: Invalid rank `"+str(rank)+"`; rank should be 1-5")

"""
    Helper functions
"""
def check_key_exists(target, key):
    return [tup for tup in target if tup[0] == key]

"""
    Main
"""
if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if sc.rtm_connect():
        print("RedmineBot connected and running!")
        while True:
            command, channel, user, username = parse_slack_output(sc.rtm_read())
            if command and channel and user != BOT_ID and username:
                handle_command(command, channel, user, username)
            elif channel and user != BOT_ID:
                handle_command("help", channel, user,  username)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
