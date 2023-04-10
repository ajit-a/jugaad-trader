#!python
import sys
from threading import Thread
import logging
from kiteconnect import KiteTicker
import time
import os
import signal
import queue
from jugaad_trader import Zerodha
import click
#from processor import *

import datetime
import os
import time
import asyncio

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

app_dir=os.getcwd()

kite = Zerodha()
session_file=".zsession"
def startsession():
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

try:
    #kite.load_session("/home/swati/autotrader/jugaad-trader/.zsession")
    kite.load_session(app_dir+"/"+session_file)
    kws = kite.ticker()
except Exception as e:
    logging.error("Existing session not found:"+repr(e))
    logging.info("Starting new session")
    startsession()

FIFO = '/tmp/AutoLtp'

try:
    os.mkfifo(FIFO)
except OSError as oe:
    #if oe.errno != errno.EEXIST:
    print("FIFO already exists")

tokens = []
print(len(sys.argv))
if(len(sys.argv) == 1):
    logging.info("Pass the ticker file as argument")
    exitFlag=1
    sys.exit()
    quit()

TickersFile=sys.argv[1]
with open(TickersFile) as f:
        ltokens = f.readlines()

#tokens.append(15919618);
#tokens.append(14138114);
i=0
while i<len(ltokens):
    itoken=int(ltokens[i])
    tokens.append(itoken)
    i = i + 1

print("Tokens length", len(tokens))

ltpQueue = queue.Queue(1000)

async def processLtp():
    while True:
        try:
            #print("Checking")
            ticks = ltpQueue.get()
            #pipeout = os.open(FIFO, os.O_WRONLY)
            #os.write(pipeout,json.dumps(tick).encode())
            #os.close()
            line=""
            i=0
            for tick in ticks:
                line+=str(tick['instrument_token'])+","+str(tick['last_price'])+"\n"
                i=i+1
                if(i%10==0):
                    print(line)
                    with open(FIFO, 'w') as write_stream:
                        print(line, file=write_stream)
                    i=0
                    line=""
            print(line)
            with open(FIFO, 'w') as write_stream:
                print(line, file=write_stream)
        except Exception as e:
            print(repr(e))
        #else:
        #    print("ltpQueue empty")

#ltpthread = Thread(target=processLtp)
#ltpthread.start()
loop = asyncio.get_event_loop()
asyncio.ensure_future(processLtp())

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    #print("on_ticks")
    #logging.debug("Ticks: {}".format(ticks))
    #if ticks[0]['mode'] == "ltp":
    #    print(ticks[0]['last_price'])
    ltpQueue.put_nowait(ticks)
    #for tick in ticks:
    #    rtoken = tick['instrument_token']
    #    tltp = float(tick['last_price'])
    #    sendioi("LTP",tltp,"LTP",rtoken,"LTP")

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    print("subscribing...")
    #ws.subscribe([738561, 5633])
    ws.subscribe(tokens)

    # Set RELIANCE to tick in `full` mode.
    #ws.set_mode(ws.MODE_FULL, [738561])
    #ws.set_mode(ws.MODE_LTP, [5633])
    #ws.set_mode(ws.MODE_LTP, tokens)
    ws.set_mode(ws.MODE_LTP, tokens)

def on_close(ws,code,reason):
    print("close...")
    logging.info("Code: {}".format(code))
    logging.info("Reason: {}".format(reason))
    #ws.stop()

def on_error(ws,code,reason):
    print("error...")
    logging.info("Error Code: "+str(code))
    logging.info("Error Code: {}".format(code))
    logging.info("Error Reason: {}".format(reason))

def on_order_update(ws,t):
    print("on_order_update")
    #logging.info("Ticks: {}".format(t))
    #for t in data:
    #print(t)
    #Put directly into tick queue
    #tickqueueLock.acquire()
    #tickQueue.put(t)
    #tickqueueLock.release()

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close
kws.on_error = on_error
kws.on_order_update = on_order_update    

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.

kws.connect(threaded=True)
loop.run_forever()
