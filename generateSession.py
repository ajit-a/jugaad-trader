#!/usr/bin/env python
#import pika
import time
import sys
import logging
import urllib
import math
#from kiteconnect import KiteConnect
import time
import signal
import os
import threading
import json
import queue
from autoconstraints import *
from autoutil import *
#import pyotp
import click
import time
import datetime
import os
import pickle
from jugaad_trader import Zerodha

app_dir=os.getcwd()



#logging.basicConfig(level=logging.INFO)

logging.basicConfig(
         format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
         level=logging.INFO,
         datefmt='%Y-%m-%d %H:%M:%S')

#logging.getLogger("pika").setLevel(logging.WARNING)


pin=""
passwd=""
user=""

print("Got "+str(len(sys.argv))+" args")
if(len(sys.argv) == 4):
    pin = sys.argv[1]
    passwd = sys.argv[2]
    user = sys.argv[3]

session_file=".zsession"+user

mod_time=-1
if(os.path.exists(session_file)):
    mod_time=time.ctime(os.path.getmtime(session_file))
    #file_size = os.path.getsize(session_file)
#Mon Mar 20 22:08:31 2023
    day=int(mod_time.split()[2])
    tday=int(datetime.datetime.today().day)
    print(day)
    print(datetime.datetime.today().day)
print("mod_time:"+str(mod_time))

if (mod_time!=-1 and day != tday):
    print("Deleting existing session file:"+session_file)
    os.remove(session_file)

kite = Zerodha()
success=False
def startautosession():
    global success
    try:
        kite.user_id = user
        kite.password = passwd
        j = kite.login_step1()
        if j['status'] == 'error':
            click.echo(click.style("Error: {}".format(j['message']), fg="red"))
            return
        kite.twofa = pin
        j = kite.login_step2(j)
        if j['status'] == 'error':
            click.echo(click.style("Error: {}".format(j['message']), fg="red"))
            return
        kite.enc_token = kite.r.cookies['enctoken']
        p = kite.profile()

        click.echo(click.style("Logged in successfully as {}".format(p['user_name']), fg='green'))
        success=True
        with open(os.path.join(app_dir, session_file), "wb") as fp:
            pickle.dump(kite.reqsession, fp)
        click.echo("Saved session successfully")
    except Exception as e:
        print("Exception in startautosession:"+repr(e))
        with open(session_file, 'w'): pass

def startsession():
    try:
        user_id = click.prompt("User ID >")
        password = click.prompt("Password >", hide_input=True)
        kite.user_id = user_id
        kite.password = password
        j = kite.login_step1()
        if j['status'] == 'error':
            click.echo(click.style("Error: {}".format(j['message']), fg="red"))
            return
        kite.twofa = click.prompt("Pin >", hide_input=True)
        j = kite.login_step2(j)
        if j['status'] == 'error':
            click.echo(click.style("Error: {}".format(j['message']), fg="red"))
            return
        kite.enc_token = kite.r.cookies['enctoken']
        p = kite.profile()

        click.echo(click.style("Logged in successfully as {}".format(p['user_name']), fg='green'))
        with open(os.path.join(app_dir, session_file), "wb") as fp:
            pickle.dump(kite.reqsession, fp)
        click.echo("Saved session successfully")
    except Exception as e:
        print("Exception in startsession:"+repr(e))
        with open(session_file, 'w'): pass

print("Logging in for user:"+user)

try:
    #kite.load_session("/home/swati/autotrader/jugaad-trader/.zsession")
    if(os.path.exists(session_file)):
        kite.load_session(app_dir+"/"+session_file)
        print("Existing Session loaded for user:"+user)
    else:
        startautosession()
        if success == False:
            sys.exit(os.EX_DATAERR)
        print("Session started for user:"+user)
except Exception as e:
    logging.error("Existing session not found:"+repr(e))
    logging.info("Starting new session")
    print(repr(e)+" Logging in for user:"+user)
    if(len(sys.argv) == 4):
        startautosession()
        if success == False:
            sys.exit(os.EX_DATAERR)
    else:
        startsession()
sys.exit()
