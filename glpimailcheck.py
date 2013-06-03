#!/usr/bin/env python

import smtplib
import imaplib
from email.mime.text import MIMEText
from email import parser
import random
import string
import re
import time
import os

from_address = os.environ['GLPIMAILCHECK_ADDRESS']
from_password = os.environ['GLPIMAILCHECK_PASSWORD']
rand_string = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) #32 character random string
subject_re = '\[GLPI #([0-9]+)\]' #RE to match the ticket number from the subject - needs parentheses around ticket number
to_address = 'EMAILTOSUBMITTICKETSTOGLPI'
smtp_server = 'smtp.gmail.com:587'
imap_server = 'imap.gmail.com'
status_file = '/opt/glpimailcheck/glpimailstatus.txt'
sleep_time = 600 #time in seconds to sleep between sending and checking for email

glpi_login_url = 'https://GLPI_SERVER/login.php'
glpi_ticket_url = 'https://GLPI_SERVER/front/ticket.form.php'


def send_email(rand_string):
    msg = MIMEText(rand_string)
    msg['Subject'] = 'GLPI email check: %s' % rand_string
    msg['From'] = from_address
    msg['To'] = to_address

    s = smtplib.SMTP(smtp_server)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(from_address, from_password)

    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()

def retrieve_email_imap(rand_string):
    tickets = []
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(from_address, from_password)
    imap.select('inbox')
    result, data  = imap.uid('search', None, '(HEADER Subject %s)' % rand_string)
    if result == 'OK':
        if data[0]:  #data[0] is a space delimited list of matching message UIDs
            uids = data[0].split(' ')
            for uid in uids:
                result, data = imap.uid('fetch', uid, '(RFC822)')
                subj = parser.Parser().parsestr(data[0][1])['subject']
                m = re.match(subject_re, subj)
                if m:
                    tickets.append(m.group(1))
            imap.uid('store', ','.join(uids), '+FLAGS', '(\\Seen)') #Mark as read
            imap.uid('store', ','.join(uids), '+FLAGS', '(\\Deleted)') # remove from inbox
    else:
        raise Exception
    imap.close()
    imap.logout()
    return tickets

f = open(status_file,"w")
exit_val = -1

try:
    send_email(rand_string)
except:
    f.write("ERROR: problem sending email to GLPI\n")
    f.close()
    exit(-1)

time.sleep(sleep_time)
#import pdb
#pdb.set_trace()

try:
    tickets = retrieve_email_imap(rand_string)
    if tickets:
        f.write("SUCCESS: create ticket(s) %s\n" % " ".join(tickets))
        exit_val = 0
    else:
        f.write("FAILURE: ticket not received with string %s\n" % rand_string)
        exit_val = 1
except:
    f.write("ERROR: problem retrieving from IMAP server\n")
    exit_val = -1

f.close()
exit(exit_val)
'''
# Doesn't work
#requires 'requests' library
def delete_ticket(ticket_id):
    from requests import session
    username = ''
    password = ''
    with session() as c:
        c.post(login_url, data={'noAUTO':'1', 'login_name' : username, 'login_password' : password, 'sumbit': 'Post'})
        request = c.post(ticket_url, data={'delete': 'To delete', 'id': str(ticket_id),"date": "2013-06-01 15:16:00", "due_date": "NULL", "slas_id": "0", "users_id_recipient": "0", "type": "1", "itilcategories_id": "0", "status": "new", "requesttypes_id": "2", "urgency": "3", "global_validation": "none", "impact": "3", "itemtype": "", "priority": "3", "_itil_requester[_type]": "", "_itil_observer[_type]": "", "_itil_assign[_type]": "", "_link[link]": "1", "_link[tickets_id_1]": "2454", "_link[tickets_id_2]": ""})
        print request.headers
        print request.text
'''


'''
#using IMAP instead
########### Check for email from helpdesk #########
def retrieve_email_pop():
    pop_conn = poplib.POP3_SSL('pop.gmail.com')
    pop_conn.user(from_address)
    pop_conn.pass_(from_password)
    messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]
    pop_conn.quit()
    messages = ["\n".join(mssg[1]) for mssg in messages]
    messages = [parser.Parser().parsestr(mssg) for mssg in messages]
    for message in messages:
        if string.find(message['subject'], rand_string) != -1:
            print "FOUND IT"
'''
