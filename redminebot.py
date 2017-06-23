import os
import time
import re
import datetime
from slackclient import SlackClient
from redmine import Redmine

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
SCRUM_ORDER = [REDMINE_INPROGRESS_ID, REDMINE_FEEDBACK_ID, REDMINE_RESOLVED_ID, REDMINE_NEW_ID, REDMINE_HOLD_ID]
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
def handle_command(command, channel, username):
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
                newmsg = s.join(commands[2:])
                response = create_issue(newmsg, username, assigneduser, REDMINE_PROJECT)
            elif operator == "issue" and len(commands) > 1:
                response = create_issue(msg, username, username, REDMINE_PROJECT)
            elif operator == "issuepto" and len(commands) > 3:
                project = commands[1]
                assigneduser = commands[2]
                newmsg = s.join(commands[3:])
                response = create_issue(newmsg, username, assigneduser, project)
            elif operator == "issuep" and len(commands) > 2:
                project = commands[1]
                newmsg = s.join(commands[2:])
                response = create_issue(newmsg, username, username, project)
            elif operator == "issuepvto" and len(commands) > 4:
                project = commands[1]
                version = commands[2]
                assigneduser = commands[3]
                newmsg = s.join(commands[4:])
                response = create_issue_version(newmsg, username, assigneduser, project, version)
            elif operator == "issuepv" and len(commands) > 3:
                project = commands[1]
                version = commands[2]
                newmsg = s.join(commands[3:])
                response = create_issue_version(newmsg, username, username, project, version)
            elif operator == "update" and len(commands) > 2:
                issue = commands[1]
                newmsg = s.join(commands[2:])
                response = update_issue(newmsg, issue, username)
            elif operator == "status" and len(commands) > 3:
                issue = commands[1]
                status = commands[2]
                newmsg = s.join(commands[3:])
                response = status_issue(newmsg, issue, status, username)
            elif operator == "close" and len(commands) > 2:
                issue = commands[1]
                newmsg = s.join(commands[2:])
                response = close_issue(newmsg, issue, username)
            elif operator == "list":
                response = list_issues(username)
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
            elif operator == "help":
                response = show_commands()
    except RuntimeError as e:
        response = e[0]
    message = "<@" + username + "> " + response
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
                profile = sc.api_call("users.info", user=output['user'])
                username = profile['user']['name']
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip(), \
                       output['channel'], username
    return None, None, None

"""
    Slack command handler functions
"""
def show_commands():
    """
        Return ist of commands that bot can handle
    """
    return ":hammer_and_wrench: *List of supported commands:*\n" \
            "`issue <subject>` - creates new issue and assigns it to you\n" \
            "`issueto <name> <subject>` - creates new issue and assigns it to `<name>`\n" \
            "`issuep <project> <subject>` - creates new issue in `<project>` and assigns it to you\n" \
            "`issuepto <project> <name> <subject>` - creates new issue and assigns it to `<name>` in `<project>`\n" \
            "`issuepv <project> <version> <subject>` - creates new issue in `<project>` with version `<version>` and assigns it to you\n" \
            "`issuepvto <project> <version> <name> <subject>` - creates new issue and assigns it to `<name>` in `<project>` with version `<version>`\n" \
            "`update <issue #> <comment>` - updates an issue with the following `<comment>`\n" \
            "`status <issue #> <status> <comment>` - changes the status of an issue\n" \
            "\t`<status>` must be one of the following: "+list_status_keys()+"\n" \
            "`close <issue #> <comment>` - closes an issue with the following comment\n" \
            "`list` - list all open issues assigned to you\n" \
            "`listfor <name>` - list all open issues assigned to `<name>`\n" \
            "`scrum` - generate daily scrum for issues assigned to you\n" \
            "`scrumfor <name>` - generate daily scrum for issues assigned to `<name>`\n" \
            "`eod` - generate end of day report for issues assigned to you\n" \
            "`eodfor <name>` - generate end of day report for issues assigned to `<name>`\n\n" \
            ":key: *List of keywords:*\n" \
            "Estimate time - `$<t>h` - where `<t>` is an integer/decimal for # of hours\n" \
            "_*NOTE:* These keywords can be used in_ `<comment>` _text only_\n" \
            "Record time - `!<t>h` - where `<t>` is an integer/decimal for # of hours\n" \
            "Percent done - `%<p>` - where `<p>` is an integer from 0-100\n"

def update_issue(text, issue, username):
    user = rm_get_user(username)
    issueid = rm_get_issue(issue)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        rm_update_issue(issue=issueid, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent, due=None, status=None)
        return ":memo: Updated Issue "+issue_url(issueid)+" with comment `"+text+"`"
    except:
        raise RuntimeError(":x: Issue update failed")

def status_issue(text, issue, status, username):
    user = rm_get_user(username)
    issueid = rm_get_issue(issue)
    statusid, statusname = get_status(status)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        rm_update_issue(issue=issueid, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent, status=statusid, due=None)
        return ":white_check_mark: Changed status of Issue "+issue_url(issueid)+" to `"+statusname+"` with comment `"+text+"`"
    except:
        raise RuntimeError(":x: Issue status update failed")
        
def close_issue(text, issue, username):
    user = rm_get_user(username)
    issueid = rm_get_issue(issue)
    today = time.strftime('%Y-%m-%d')
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, record, percent) = parse_keywords(text)
        if not percent:
            percent = 100
        rm_update_issue(issue=issueid, notes=text, rcn=rcn, estimate=estimate, record=record, percent=percent, status=REDMINE_CLOSED_ID, due=today)
        return ":white_check_mark: Closed Issue "+issue_url(issueid)+" with comment `"+text+"`"
    except:
        raise RuntimeError(":x: Issue closing failed")

def create_issue(text, username, assigneduser, project_name):
    user = rm_get_user(username)
    assigned = rm_get_user(assigneduser)
    project = rm_get_project(project_name)
    # impersonate user so it looks like the update is from them
    rcn = rm_impersonate(user.login)
    try:
        (estimate, clean_text) = parse_remove_estimate(text)
        issue = rm_create_issue(estimate=estimate, subject=clean_text, rcn=rcn, assigned=assigned.id, project=project, version=None)
        return ":white_check_mark: Created Issue "+issue_subject_url(issue.id,issue.subject)+" in project `"+project_name+"` assigned to "+assigned.firstname+" "+assigned.lastname
    except:
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
        issue = rm_create_issue(estimate=estimate, subject=clean_text, rcn=rcn, assigned=assigned.id, project=project, version=version)
        return ":white_check_mark: Created Issue "+issue_subject_url(issue.id,issue.subject)+" in project `"+project_name+"` with version `"+version_name+"` assigned to "+assigned.firstname+" "+assigned.lastname
        return ""+str(version)
    except:
        raise RuntimeError(":x: Issue creation failed")
        
def list_issues(username):
    user = rm_get_user(username)
    try:
        result = rm_get_user_issues(user.id, 'open')
        response = ""
        if len(result) > 0:
            response = ":book: *Open Issues Assigned to "+user.firstname+" "+user.lastname+":*\n"
            for issue in result:
                response += ""+issue.project.name+" "+issue_subject_url(issue.id, issue.subject)+"\n"
        else:
            response = ":thumbsup_all: No open issues assigned to "+user.firstname+" "+user.lastname
        return response
    except:
        raise RuntimeError(":x: List operation failed")

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
                    response += ""+issue.project.name+" "+issue_subject_url(issue.id, issue.subject)+issue_time_percent_details(issue)+"\n"
        if not issues_found:
            response += ":thumbsup_all: No issues found!\n"
        response += "\n_*Additional comments:*_"
        return response
    except:
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
                    response += ""+issue.project.name+" "+issue_subject_url(issue.id, issue.subject)+issue_time_percent_details(issue)+"\n"
        for s in SCRUM_ORDER:
            result = rm_get_user_issues(user.id, s)
            if len(result) > 0:
                issues_found = True
                response += "*_"+STATUS_NAME_LOOKUP[s]+" ("+str(len(result))+")_*\n"
                for issue in result:
                    response += ""+issue.project.name+" "+issue_subject_url(issue.id, issue.subject)+issue_time_percent_details(issue)+"\n"
        if not issues_found:
            response += ":thumbsup_all: No issues found!\n"
        response += "\n_*Additional comments:*_"
        return response
    except:
        raise RuntimeError(":x: EOD operation failed")

"""
    Redmine functions
"""
def rm_get_user(username):
    try:
        return rc.user.filter(name=username)[0]
    except:
        raise RuntimeError(":x: Failed to find user `"+username+"` in Redmine")
    
def rm_get_project(project):
    try:
        return rc.project.get(project)
    except:
        raise RuntimeError(":x: Failed to find project `"+project+"` in Redmine")
    
def rm_get_version(project, version):
    try:
        proj = rm_get_project(project)
        for v in proj.versions:
            if v.name == version:
                return v.id
        raise RuntimeError(":x: Failed to find version `"+version+"` within project `"+project+"` in Redmine")
    except:
        raise RuntimeError(":x: Failed to find version `"+version+"` within project `"+project+"` in Redmine")

def rm_get_issue(issueid):
    try:
        return rc.issue.get(int(issueid)).id
    except:
        raise RuntimeError(":x: Failed to find issue ID `"+issueid+"` in Redmine")
        
def rm_get_user_issues(userid, status):
    if not status:
        status = 'open'
    try: 
        return rc.issue.filter(sort='project', assigned_to_id=userid, status_id=status)
    except:
        raise RuntimeError(":x: Failed to find issues for user `"+username+"` in Redmine")

def rm_get_user_issues_today(userid, status):
    if not status:
        status = 'open'
    try: 
        return rc.issue.filter(sort='project', assigned_to_id=userid, status_id=status, updated_on=datetime.date.today())
    except:
        raise RuntimeError(":x: Failed to find issues for user `"+username+"` in Redmine")

def rm_impersonate(userlogin):
    try:
        return Redmine(REDMINE_HOST, version=REDMINE_VERSION, key=REDMINE_TOKEN, impersonate=userlogin)
    except:
        raise RuntimeError(":x: Failed impersonate user `"+userlogin+"` in Redmine")
        
def rm_create_issue(estimate, assigned, subject, project, version, rcn):
    params = dict()
    if estimate:
        params['estimated_hours'] = estimate
    if subject:
        params['subject'] = parse_remove_http(subject)
    if assigned:
        params['assigned_to_id'] = assigned
    if version:
        params['fixed_version_id'] = version
    if not project:
        project = REDMINE_PROJECT
    
    try:
        return rcn.issue.create(project_id=project, tracker_id=REDMINE_TRACKER_ID, **params)
    except:
        raise RuntimeError(":x: Issue creation failed")

def rm_update_issue(issue, estimate, percent, status, due, notes, record, rcn):
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
        params['notes'] = notes
    if record:
        rm_record_time(issue, record, rcn)
    
    try:
        result = rcn.issue.update(issue, **params)
    except:
        raise RuntimeError(":x: Issue update failed")
    
def rm_record_time(issueid, record, rcn):
    try:
        result = rcn.time_entry.create(issue_id=issueid, spent_on=datetime.date.today(), hours=record, activity_id=REDMINE_ACTIVITY_ID)
    except:
        raise RuntimeError(":x: Issue record time spent failed")
        
def rm_sum_time_entries(issueid):
    try:
        issue = rc.issue.get(issueid)
        total = 0.0
        for te in issue.time_entries:
            total += te.hours
        return total
    except:
        raise RuntimeError(":x: Failed in summing time entries")
        
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
    estimated = [tup for tup in issue if tup[0] == 'estimated_hours']
    response = ""
    if estimated:
        spent = rm_sum_time_entries(issue.id)
        response += " ["+str(issue.estimated_hours)+"h/"+str(spent)+"h]"
    response += " "+str(issue.done_ratio)+"%"
    return response
        
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

"""
    Main
"""
if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if sc.rtm_connect():
        print("RedmineBot connected and running!")
        while True:
            command, channel, username = parse_slack_output(sc.rtm_read())
            if command and channel and username:
                handle_command(command, channel, username)
            elif channel and username:
                handle_command("help", channel, username)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
