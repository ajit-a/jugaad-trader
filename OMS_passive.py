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

FIFO = '/tmp/AutoLtp'
DATA_HOST='127.0.0.1'
try:
    os.mkfifo(FIFO)
except OSError as oe:
    #if oe.errno != errno.EEXIST:
    print("FIFO already exists")

squareoff_orders = {}
co_sl_orders = {}
MAXORDERS=1
MAXPROFIT=10000
MAXLOSS=-5000
straddleadjusted=True

bnfvalue=0
bnfdirection="UP"
nfvalue=0
nfdirection="DOWN"

token_price_ltp[BNF_TICKER]=bnfvalue
token_price_ltp[NIFTY_TICKER]=nfvalue

blockList = []
try:
    with open('blocklist.csv') as f:
        lines = f.readlines()
        for record in lines:
            blockList.append(record.strip('\n'))
except OSError as oe:
    #if oe.errno != errno.EEXIST:
    print("blocklist.csv doesnt exists")

session_file=".zsession"

mod_time=time.ctime(os.path.getmtime(session_file))
file_size = os.path.getsize(session_file)
print("mod_time:"+str(mod_time)+" size:"+str(file_size))
#Mon Mar 20 22:08:31 2023
day=int(mod_time.split()[2])
tday=int(datetime.datetime.today().day)
print(day)
print(datetime.datetime.today().day)
#year,month,day,hour,minute,second=time.localtime(mod_time)[:-3]
#print("Date modified: %02d/%02d/%d %02d:%02d:%02d"%(day,month,year,hour,minute,second))

needlogin = True
if (day == tday and file_size > 0):
    print("Will read from session file")
    needlogin = False
else:
    print("Clearing stale session file")
    with open(session_file, 'w'): pass

pin=""
passwd=""
user=""

print("Got "+str(len(sys.argv))+" args")
if(len(sys.argv) == 4):
    pin = sys.argv[1]
    passwd = sys.argv[2]
    user = sys.argv[3]

kite = Zerodha()
def startautosession():
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
    kite.load_session(app_dir+"/"+session_file)
except Exception as e:
    logging.error("Existing session not found:"+repr(e))
    logging.info("Starting new session")
    if needlogin == True:
        if(len(sys.argv) == 4):
            startautosession()
        else:
            startsession()

orderIds = {}
blockedSymbols = []

def sendOrder(
        variety_,
        exchange_,
        tradingsymbol_,
        transaction_type_,
        quantity_,
        product_,
        order_type_,
        price_,
        validity_=None,
        disclosed_quantity_=None,
        trigger_price_=None,
        squareoff_=None,
        stoploss_=None,
        trailing_stoploss_=None,
        tag_=None
        ):
    logging.info("sendOrder:"+str(variety_)+":"+str(tradingsymbol_))
    try:
        #if ( ( (datetime.datetime.now().hour ==9 and datetime.datetime.now().minute >= 31) 
        #    or (datetime.datetime.now().hour >9) )
        #    and (datetime.datetime.now().hour <= 15)
        #    or datetime.datetime.today().weekday() >=5
        #    and (datetime.datetime.now() >= lastrejectedtime + datetime.timedelta(seconds = 30))
        #    ):
        if True:
            print("now:"+str(datetime.datetime.now())+" lastrejectedtime:"+str(lastrejectedtime)+" diff:"+str(lastrejectedtime + datetime.timedelta(seconds = 30)))
            #and (datetime.datetime.now() >= lastrejectedtime + datetime.timedelta(seconds = 30)) ):
            #and (datetime.datetime.now() >= lastrejectedtime + datetime.timedelta(minutes = 1)) ):
            if(datetime.datetime.now().hour >16):
                variety_ = "amo"
            if(trigger_price_ != None and trigger_price_ !=0):
                trigger_price_=round(trigger_price_,1)
            if(squareoff_ != None and squareoff_ !=0):
                squareoff_=round(squareoff_,1)
            if(stoploss_ != None and stoploss_ !=0):
                stoploss_=round(stoploss_,1)
            if(trailing_stoploss_ != None and trailing_stoploss_ !=0):
                trailing_stoploss_=round(trailing_stoploss_,1)
            order_id = kite.place_order(
                                variety=variety_,
                                tradingsymbol=tradingsymbol_,
                                exchange=exchange_,
                                transaction_type=transaction_type_,
                                quantity=quantity_,
                                order_type=order_type_,
                                product=product_,
                                price=price_,
                                disclosed_quantity=disclosed_quantity_,
                                trigger_price=trigger_price_,
                                tag=tag_
                                )
            return order_id
        else:
            logging.info("sendOrder:Time criteria not satisfied. Order not sent")
            return 0
    except Exception as e:
        logging.info("place_order Order placement failed: {}".format(e)+" ts:"+tradingsymbol_+" price:"+str(price_)+" qty:"+str(quantity_))
        print(repr(e))
        if 'blocked' in repr(e):
            bsLock.acquire()
            blockedSymbols.append(tradingsymbol_)
            bsLock.release()
            return -1

def placed_order_status(order_id):
        # check status of orders placed if successful or not
        order_successful = False
        if len(kite.trades(order_id)) == 0:
            print("Order placement failed for order_id ",order_id)
        else:
            order_successful = True
            print("Order Successful")

def createSingleOrderForGTT(
        symbol,
        target,
        stoploss,
        direction,
        exchange,
        qty
        ):
        ORDERS = [
        {
                "exchange" : exchange,
                "tradingsymbol" : symbol,
                "transaction_type" : direction,
                "quantity" :  qty,
                "order_type" : "LIMIT",
                "product" : "MIS",
                "price" : target
        }
        ]
        #print(ORDERS)
        return ORDERS            
def createOCOOrderForGTT(
        symbol,
        target,
        stoploss,
        direction,
        exchange,
        qty
        ):
        ORDERS = [
        {
                "exchange" : exchange,
                "tradingsymbol" : symbol,
                "transaction_type" : direction,
                "quantity" :  qty,
                "order_type" : "LIMIT",
                "product" : "MIS",
                "price" : target
        },
        {
                "exchange" : exchange,
                "tradingsymbol" : symbol,
                "transaction_type" : direction,
                "quantity" :  qty,
                "order_type" : "LIMIT",
                "product" : "MIS",
                "price" : stoploss
        }
        ]
        #print(ORDERS)
        return ORDERS            

def TradeGTT(
        symbol,
        price,
        squareoff,
        stoploss,
        trailing_stoploss,
        direction,
        qty
        ):
    logging.debug("TradeGTT called")
    # Place an order
    try:
        if(symbol_to_type[symbol]=="EQ"):
            exchange="NSE"
        else:
            exchange="NFO"

        if(stoploss<0.1):
            stoploss=0.1
        if(squareoff<0.1):
            squareoff=0.1

        ORDERS = createOCOOrderForGTT(symbol,squareoff,stoploss,direction,exchange,qty);

        if(direction == "BUY"):
            lst_triggers = [stoploss,squareoff]
        elif(direction == "SELL"):
            lst_triggers = [squareoff,stoploss]

        order_id = kite.place_gtt(
                         kite.GTT_TYPE_OCO,
                         symbol,
                         exchange,
                         lst_triggers,
                         price,
                         ORDERS)

        logging.info("Order placed. ID is: {}".format(order_id))
    except Exception as e:
        logging.info("TradeGTT Order placement failed: {}".format(e))

def TradeRegularOrder(
        symbol,
        price,
        squareoff,
        stoploss,
        trailing_stoploss,
        direction,
        qty
        ):
    logging.debug("TradeRegularOrder called")
    # Place an order
    try:
        if(symbol_to_type[symbol]=="EQ"):
            exch="NSE"
        else:
            exch="NFO"

        logging.debug("sending order")        
        order_id = sendOrder(
                         variety_=kite.VARIETY_REGULAR,
                         tradingsymbol_=symbol,
                         exchange_=exch,
                         transaction_type_=direction,
                         quantity_=qty,
                         order_type_=kite.ORDER_TYPE_LIMIT,
                         price_=price,
                         squareoff_=squareoff,
                         stoploss_=stoploss,
                         trailing_stoploss_=trailing_stoploss,
                         product_=kite.PRODUCT_MIS)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("TradeRegularOrder Order placement failed: {}".format(e))
        return 0

def TradeRegularMISOrder(
        symbol,
        price,
        squareoff,
        stoploss,
        trailing_stoploss,
        direction,
        qty
        ):
    logging.debug("TradeRegularMISOrder called")
    # Place an order
    try:
        if(symbol_to_type[symbol]=="EQ"):
            exch="NSE"
        else:
            exch="NFO"

        logging.debug("sending order")        
        order_id = sendOrder(
                         variety_=kite.VARIETY_REGULAR,
                         tradingsymbol_=symbol,
                         exchange_=exch,
                         transaction_type_=direction,
                         quantity_=qty,
                         order_type_=kite.ORDER_TYPE_LIMIT,
                         price_=price,
                         squareoff_=squareoff,
                         stoploss_=stoploss,
                         trailing_stoploss_=trailing_stoploss,
                         product_=kite.PRODUCT_MIS)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("TradeRegularMISOrder Order placement failed: {}".format(e))
        return -1

def TradeBO(
        symbol,
        price,
        squareoff,
        stoploss,
        trailing_stoploss,
        direction,
        qty
        ):
    logging.debug("TradeBO called")
    return 0
    # Place an order
    try:
        if(symbol_to_type[symbol]=="EQ"):
            exch="NSE"
        else:
            exch="NFO"

        order_id = sendOrder(
                         variety_=kite.VARIETY_BO,
                         tradingsymbol_=symbol,
                         exchange_=exch,
                         transaction_type_=direction,
                         quantity_=qty,
                         order_type_=kite.ORDER_TYPE_LIMIT,
                         price_=price,
                         squareoff_=squareoff,
                         stoploss_=stoploss,
                         trailing_stoploss_=trailing_stoploss,
                         product_=kite.PRODUCT_MIS)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("TradeBO Order placement failed: {}".format(e))                         
        return 0

def TradeCO(
        symbol,
        price,
        trigger_price,
        squareoff,
        stoploss,
        trailing_stoploss,
        direction,
        qty
        ):
    logging.debug("TradeCO called")
    # Place an order
    try:
        if(symbol_to_type[symbol]=="EQ"):
            exch="NSE"
        else:
            exch="NFO"

        order_id = sendOrder(
                         variety_=kite.VARIETY_CO,
                         tradingsymbol_=symbol,
                         exchange_=exch,
                         transaction_type_=direction,
                         quantity_=qty,
                         order_type_=kite.ORDER_TYPE_LIMIT,
                         price_=price,
                         trigger_price_=trigger_price,
                         #trigger_price_=trigger_price,
                         squareoff_=squareoff,
                         stoploss_=stoploss,
                         trailing_stoploss_=trailing_stoploss,
                         product_=kite.PRODUCT_CO)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("TradeCO Order placement failed: {}".format(e))                         
        return 0

my_mutex = threading.Lock()

def test_func(symbol_l,id_):
    s=symbol_l
    p=id_
    #time.sleep(1)
    #print(s+":"+str(p))

def openOrderCount(symbol_):
    try:
        lorders = kite.orders()
        #print(lorders)
        openOrder=0
        for k in lorders:
            if(k['tradingsymbol'] == symbol_ and (k['status']=="OPEN" or k['status']=="AMO REQ RECEIVED")):
                if(k['order_id'] not in squareoff_orders):
                    return -1
            #if(k['status']=="OPEN"):
            if(k['status']=="OPEN" or k['status']=="AMO REQ RECEIVED"):
                openOrder+=1
        return openOrder
    except Exception as e:
        return 0
    logging.error(str("openOrderCount:Error fetching orders").format(e))
    
def OrderAlreadySent(symbol_):
    try:
        lorders = kite.orders()
        for k in lorders:
            #if(k['tradingsymbol'] == symbol_ and (k['status']=="COMPLETE" or k['status']=="OPEN")):
            if(k['tradingsymbol'] == symbol_ and k['status']=="OPEN"):
                return True
        return False        
    except Exception as e:
        logging.error(str("OrderAlreadySent:Error fetching orders").format(e))
        return True

_NeedmarginUpdate=True
_marginAvailable=0
def isMarginAvailable(segment='equity',price=1,qty=25):
    global _NeedmarginUpdate
    global _marginAvailable
    if(not _NeedmarginUpdate):
        print("Margin:"+str(5*_marginAvailable)+" price:"+str(price*qty))
        if( (5*_marginAvailable) >= price*qty ):
            return True
        return False
    margin = kite.margins()
    net_ = margin[segment]
    print(net_)
    if ( net_['enabled']):
        print(str(net_['net'])+" "+str(price*qty))
        if(5*net_['net'] >= price*qty ):
            _marginAvailable=net_['net']
            _NeedmarginUpdate=False
            print("Margin:"+str(5*_marginAvailable)+" price:"+str(price*qty))
            return True
    return False

def loop_func(
        symbol_,
        direction_,
        price_,
        strategyId_,
        type_
    ):
    logging.debug("loop_func"+symbol_+":"+type_)
    price_ = float(price_)
    delta=price_*0.1
    if(type_=="BNF"):
        delta=getTgt(strategyId_,type_)
    elif(type_=="EQ"):
        delta=price_*getEQTgt(strategyId_)

    if(type_=="NIFTY"):
        return

    delta = round(delta,2)

    try:
        #if(True):
        if(not OrderAlreadySent(symbol_)):
        #if( not ExistsInOpenOrdersInProcess(symbol_)):
            #delta = rounded_percentage(price=float(price_),percent=15) #OPT
            #delta = getDeltaForEQ(price_) #EQ
            logging.info("IOI "+str(symbol_)+" price:"+str(price_)+" delta:"+str(delta)+":"+type_+":"+direction_)
            #ordersInProcessing.remove(symbol_)
            #return
            bsLock.acquire()
            if(symbol_ in blockedSymbols ):
                bsLock.release()
                return -1
            bsLock.release()
            Qty = getQtyToTrade(strategyId_,type_)
            #if(not isMarginAvailable(price=price_,qty=Qty)):
            if(not isMarginAvailable(price=price_,qty=25)):
                RemoveFromOrdersInProcess(symbol_)
                logging.info("Ignoring IOI due to insufficient funds")
                return
            if(direction_=="BUY"):
                target=price_+delta
                sl=price_-delta
            elif(direction_=="SELL"):
                target=price_-delta
                sl=price_+delta

            oid=TradeBO(
                    symbol=symbol_,
                    price=price_,
                    squareoff=target,
                    stoploss=sl,
                    trailing_stoploss=delta,
                    direction=direction_,
                    qty=Qty
                    )
            if(oid==-1):
                return
            if type_=="EQ":
                delta=(price_*0.002)
                MA=getMA(symbol_)
                if(delta<1):
                    delta=1
                if(direction_=="BUY"):
                    sl=price_-delta
                    if(MA>0 and MA<price_ and MA>(price_-0.09*price_)):
                        sl=MA
                elif(direction_=="SELL"):
                    sl=price_+delta
                    if(MA>0 and MA>price_ and MA<(price_+0.09*price_)):
                        sl=MA
                logging.info("Sending TradeCO for:"+str(symbol_)+" price:"+str(price_)+" tp:"+str(round(sl,1))+" MA:"+str(MA))
                oid=TradeCO(
                        symbol=symbol_,
                        price=price_,
                        trigger_price=round(sl,1),
                        squareoff=target,
                        stoploss=sl,
                        trailing_stoploss=delta,
                        direction=direction_,
                        qty=Qty
                        )
                if(oid==-1):
                    return
                elif(oid!=0):
                    success=False
                    ctr=0
                    while(success!=True and ctr<=5):
                        try:
                            lorders = kite.orders()
                        except Exception as e:
                            logging.info("Error in getting order:".format(e))
                            time.sleep(1)
                            continue
                        for _o in lorders:
                            if oid==_o['parent_order_id']:
                                poid=oid
                                success=True
                                toid = _o['order_id']
                                co_sl_orders[poid]=toid
                                #squareoff_orders[_o['parent_order_id']]=_o['order_id']
                                squareoff_orders[_o['order_id']]=_o['parent_order_id']
                                print("Adding:"+str(_o['order_id'])+" as squareoff order fo:"+str(_o['parent_order_id']))
                                tnoid = _o['variety']+_o['tradingsymbol']+_o['product']
                                positionsLock.acquire()
                                if(intraday_positions.__contains__(tnoid)):
                                    print(str(tnoid)+" found in intra_pos for:"+str(toid)+" poid:"+str(poid))
                                    #if(intraday_positions[tnoid][0]['opp_order_raised'] == False):
                                    print("Updating opp order id for")
                                    intraday_positions[tnoid][0]['opp_orderid'] = toid
                                    intraday_positions[tnoid][0]['opp_order_raised'] = True
                                    intraday_positions[tnoid][0]['trigger_price'] = _o['trigger_price']
                                positionsLock.release()
                        if(success==False):
                            time.sleep(1)
                            print("Trying to get trigger order for oid:"+str(oid))
                        ctr+=1
            if(oid==0):
                    oid=TradeRegularMISOrder(
                        symbol=symbol_,
                        price=price_,
                        squareoff=target,
                        stoploss=sl,
                        trailing_stoploss=delta,
                        direction=direction_,
                        qty=Qty
                        )
            if(oid==-1):
                return
            if(oid==0):
                    oid=TradeRegularOrder(
                        symbol=symbol_,
                        price=price_,
                        squareoff=target,
                        stoploss=sl,
                        trailing_stoploss=delta,
                        direction=direction_,
                        qty=Qty
                        )
            if(oid==-1):
                return
            if(oid==0):
                TradeGTT(
                    symbol=symbol_,
                    price=price_,
                    squareoff=target,
                    stoploss=sl,
                    trailing_stoploss=delta,
                    direction=direction_,
                    qty=Qty
                    )
            orderIds[oid]=strategyId_
        else:
            logging.info("Skipping "+str(symbol_)+" price:"+str(price_)+" already present")
    except Exception as e:
        RemoveFromOrdersInProcess(symbol_)
        logging.info("Error in loop_func:".format(e))
        print(repr(e))

ordersInProcessing = set()
def AddToOpenOrdersInProcess(a):
    #opLock.acquire()
    ordersInProcessing.add(a)
    #opLock.release()
def RemoveFromOrdersInProcess(a):
    #opLock.acquire()
    ordersInProcessing.discard(a)
    #if(ordersInProcessing.__contains__(a)):
    #    ordersInProcessing.remove(a)
    #opLock.release()
def ExistsInOpenOrdersInProcess(a):
    #opLock.acquire()
    if a in ordersInProcessing:
        #opLock.release()
        return True
    #opLock.release()
    return False
lastltptime=datetime.datetime.now()
def processIoi(msg_):
    tokens = msg_.split(',')
    a = str(tokens[0])
    b = float(tokens[1])
    c = str(tokens[2])
    d = int(tokens[3])
    e = str(tokens[4].rstrip('\n'))

    #LTP,33300,LTP,BANKNIFTY,LTP
    if (a=="LTP"):
        token_price_ltp[d]=b
        return
    if b==0:
        b = token_price_ltp[symbols_token[a]]
        if b==0:
            RemoveFromOrdersInProcess(a)
            #print("Price is 0 in cache")
            return
    if c=="SELL" and e!="EQ":
        print("Ignoring non EQ SELL ioi");
        RemoveFromOrdersInProcess(a)
        return
    if(e!="EQ"):
        if(datetime.datetime.now()<lastrejectedtime):
            print("Ignoring non EQ ioi as last reject time was:"+str(lastrejectedtime))
            RemoveFromOrdersInProcess(a)
            return
    #if(a=="SAIL" or a=="GAIL" or a=="BHEL" or a=="ONGC"):
    if d==1:
        if(a in blockList):
            RemoveFromOrdersInProcess(a)
            return
    if( ( (datetime.datetime.now().hour ==9 and datetime.datetime.now().minute >= 17) 
            or (datetime.datetime.now().hour >9) )
            and datetime.datetime.now().hour < 15
            or datetime.datetime.today().weekday() >=5
            ):
            #and (datetime.datetime.now() >= lastrejectedtime + datetime.timedelta(seconds = 30)) ):
            #and (datetime.datetime.now() >= lastrejectedtime + datetime.timedelta(minutes = 1)) ):
        OrdersLock.acquire()
        try:
            openorders = openOrderCount(a)
            pos_size = liveOrderCount.get(str(d)+e,0)
            #print(str(d)+e+":Open orders:"+str(openorders)+" pos_siz:"+str(pos_size))
            #if(openorders!=-1 and openorders<TOTALOPENORDERS and pos_size<maxOrders(d,e) and pos_size<TOTALOPENORDERS):
            if(openorders!=-1):
                if(openorders<TOTALOPENORDERS):
                    if(pos_size<maxOrders(d,e)):
                        if(pos_size<TOTALOPENORDERS):
                            loop_func(symbol_=a,direction_=c,price_=b,strategyId_=d,type_=e)
                        else:
                            print("Open orders pos_size:"+str(pos_size)+" more than totalopenorders:"+str(TOTALOPENORDERS))
                            RemoveFromOrdersInProcess(a)
                    else:
                        print("Open orders pos_size:"+str(pos_size)+" more than maxOrders:"+str(maxOrders(d,e))+" for strategy:"+str(d))
                        RemoveFromOrdersInProcess(a)
                else:
                    print("Open orders:"+str(openorders)+" more than totalopenorders:"+str(TOTALOPENORDERS))
                    RemoveFromOrdersInProcess(a)
            else:
                print("Already order open for:"+a)
                RemoveFromOrdersInProcess(a)
        except Exception as e:
            RemoveFromOrdersInProcess(a)
            OrdersLock.release()
            logging.info("Error in processIoi:".format(e))
            print(repr(e))
            return
        OrdersLock.release()
        #else:
        #    print("Max orders limit reached")
    else:
        RemoveFromOrdersInProcess(a)
        logging.info("Time criteria not satisfied :"+str(lastrejectedtime))
        logging.info("Ignoring :"+msg_)

#print(len(sys.argv))
#if(len(sys.argv) <= 2):
#    print("Pass the Queue name as argument")
#    sys.exit()
#    quit()

texitFlag=0
class IOIProcessor (threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
       print("Starting " + self.name)
       if(self.name == "CANCEL"):
           cancel_squareoff_open_orders(self.name)
       elif(self.name == "updateCO"):
           trailCO(self.name)
       elif(self.name == "ltpreader"):
           #print("IOIP now:"+str(datetime.datetime.now())+" lastrejectedtime:"+str(lastrejectedtime)+" diff:"+str(lastrejectedtime + datetime.timedelta(seconds = 30)))
           readLtpFromFifo(self.name)
       #else:
       #   process_data(self.name,self.q)
       print("Exiting " + self.name)


def populateExistingData():
    passiveStatusCache.clear()
    squareoff_orders.clear()
    korders = kite.orders()
    tmpOrdersDict = {}
    tmpOrdersTPDict = {}
    logging.info("TEST::preparePDHSymbols:passiveStatusCache:"+str(passiveStatusCache))
    for order in korders:
        #if("AMO REQ RECEIVED" == order['status']):
        #print(order)
        if("OPEN" == order['status'] or order['status'] == "TRIGGER PENDING" or order['status']=="AMO REQ RECEIVED"):
            try:
                if(order['parent_order_id']==None or order['parent_order_id']==0):
                    kite.cancel_order(variety=order['variety'],order_id=order['order_id'])
                else:
                    co_sl_orders[order['order_id']]=order['parent_order_id']
                    squareoff_orders[order['order_id']]=order['parent_order_id']
                    Noid = order['variety']+order['tradingsymbol']+order['product']
                    if(intraday_positions.__contains__(Noid)):
                        intraday_positions[Noid][0]["opp_order_raised"] = True
                        intraday_positions[Noid][0]["opp_orderid"] = order['order_id']
                        #Below line is not required as EMA will be used now
                        if(order['trigger_price'] > 0):
                            intraday_positions[Noid][0]["trigger_price"] = order['trigger_price']
                    else:
                        tmpOrdersDict[Noid]=order['order_id']
                        tmpOrdersTPDict[Noid]=order['trigger_price']
            except Exception as e:
                logging.debug("Cannot cancel order:".format(e)) 
        else:
            extract_order_update(order)
    for o in tmpOrdersDict:
        if(intraday_positions.__contains__(o)):
            intraday_positions[o][0]["opp_order_raised"] = True
            intraday_positions[o][0]["opp_orderid"] = tmpOrdersDict[o]
            intraday_positions[o][0]["trigger_price"] = tmpOrdersTPDict[o]

    with open("passiveorders") as f:
        lorders = f.readlines()
    i=0
    tmpCache = {}
    logging.info("TEST::preparePDHSymbols:passiveStatusCache:"+str(passiveStatusCache))
    while i<len(lorders):
        _tokens = lorders[i].split(',')
        id_ = int(_tokens[0])
        ticker = int(_tokens[1])
        TS = _tokens[2].rstrip('\n')
        squareoff_orders[id_]=ticker
        passiveOrders.append(id_)

        idx=""
        if(ticker==BNF_TICKER):
            idx="BNF"
        elif(ticker==NIFTY_TICKER):
            idx="NIFTY"

        for ordr in korders:
            if(ordr['status']!="COMPLETE"):
                continue
            try:
                logging.info(ordr)
                if(int(ordr['order_id'])==id_):
                    price=ordr['price']
                    if(price==0):
                        price=ordr['average_price']
                    logging.info("xxxxxxxxxxxxxxxxxxxxxxxxx"+str(price))
                    tmpCache[TS]=price
            except Exception as e:
                logging.error(repr(e))
        if(len(tmpCache)%2==0):
            passivelockActivated[idx]=9999999
            passiveStatusCache[idx]=tmpCache

        i = i + 1

    #return
    logging.info("TEST::preparePDHSymbols:passiveStatusCache:"+str(passiveStatusCache))
    logging.info("TEST::preparePDHSymbols:passiveOrders:"+str(passiveOrders))
    print("###intrday_pos:"+str(intraday_positions))
    print("passiveStatusCache:"+str(passiveStatusCache))
    print("passiveOrders:"+str(passiveOrders))
    print("squareoff_orders:"+str(squareoff_orders))

def extract_order_update(t):
    global lastrejectedtime
    oid = int(t['order_id'])
    ts_ = t['tradingsymbol']
    qty_ = t['quantity']
    prd_ = t['product']
    var_ = t['variety']
    _key="NA" 
    if(var_ == "amo" ):
        var_ = kite.VARIETY_REGULAR
    Noid = var_+t['tradingsymbol']+t['product']
    ltype = isIndexOption(t['instrument_token'])
    if(symbol_to_type.__contains__(ts_)):
        stype = symbol_to_type[ts_]
    else:
        return
    if(stype=="EQ"):
        _key = str(orderIds.get(t['order_id'],1))+stype
    else:
        _key = str(orderIds.get(t['order_id'],1))+ltype
    if(t['status']=="REJECTED" or t ['status']=="CANCELLED"):
        #lastrejectedtime = datetime.datetime.now()
        if "NIFTY" in t['tradingsymbol']:
            lastrejectedtime = datetime.datetime.now() + datetime.timedelta(minutes = 5)
        RemoveFromOrdersInProcess(ts_)
        return
        positionsLock.acquire()
        if(intraday_positions.__contains__(Noid)):
            logging.info("Deleting as rejected:"+str(Noid))
            opp_id = intraday_positions[Noid][0]['opp_orderid']
            if(squareoff_orders.__contains__(opp_id)):
                logging.info("Deleting from squareoff too:"+str(opp_id))
                del squareoff_orders[opp_id]
            del intraday_positions[Noid]
        if(liveOrderCount.__contains__(_key)):
            liveOrderCount[_key] -= 1
        positionsLock.release()
        return
    elif(t['status']=="TRIGGER PENDING"):
    #Sometimes this comes before open order
        if(t['parent_order_id']==None or t['parent_order_id']==0):
            print("parent_order_id not found:"+str(t['parent_order_id']))
            return
        else:
            poid = t['parent_order_id']
            toid = t['order_id']
            tnoid = t['variety']+t['tradingsymbol']+t['product']
            if(intraday_positions.__contains__(tnoid)):
                print(str(tnoid)+" found in intra_pos for:"+str(toid)+" poid:"+str(poid))
                if(intraday_positions[tnoid][0]['opp_order_raised'] == False):
                    print("Updating opp order id of")
                    positionsLock.acquire()
                    intraday_positions[tnoid][0]['opp_order'] = toid
                    intraday_positions[tnoid][0]['opp_order_raised'] = True
                    if(t['trigger_price']!=0):
                        intraday_positions[tnoid][0]["trigger_price"] = t['trigger_price']
                    positionsLock.release()
                    squareoff_orders[poid] = toid
            else:
                print(str(tnoid)+" not found in intra_pos for:"+str(toid)+" poid:"+str(poid))
    elif(t['status']=="COMPLETE"):
        logging.info("called extract_order_update:"+format(t))
        global _NeedmarginUpdate
        _NeedmarginUpdate=True
        found = False
        processed = False
        deleteoid=0
        print("Waiting for Lock")
        positionsLock.acquire()
        print("Checking for:"+str(Noid)+" in intraday_pos")
        if(intraday_positions.__contains__(Noid)):
            processed = True
            pos = intraday_positions[Noid][0]
            existing_trans_type = pos['transaction_type']
            existing_qty_ = pos['quantity']
            if(t['transaction_type'] != existing_trans_type):
                logging.info(str(Noid)+":"+":"+str(existing_trans_type)+":"+t['transaction_type']+":"+str(existing_qty_)+":"+str(qty_))
                if(existing_qty_+qty_ == 0 or existing_qty_==qty_):
                    RemoveFromOrdersInProcess(ts_)
                    if "NIFTY" in t['tradingsymbol']:
                        lastrejectedtime = datetime.datetime.now() + datetime.timedelta(minutes = 5)
                    #print(intraday_positions[Noid][0])
                    #It may happen that other prcoess is hanged and we wont get order update. Need to modify this logic
                    if(intraday_positions[Noid][0]['opp_order_raised']):
                        opp_oid = intraday_positions[Noid][0]['opp_orderid']
                        if(squareoff_orders.__contains__(opp_oid)):
                            del squareoff_orders[opp_oid]
                    print("Deleting from squareoff as complete:"+str(Noid))
                    logging.info("Deleting as order complete:"+str(Noid))
                    if(liveOrderCount.__contains__(_key)):
                        print("liveOrderCount for key:"+str(_key) +" is:"+str(liveOrderCount[_key]))
                        liveOrderCount[_key] -= 1
                        print("liveOrderCount for key:"+str(_key) +" is:"+str(liveOrderCount[_key]))
                    del intraday_positions[Noid]
                    print("EOU now:"+str(datetime.datetime.now())+" lastrejectedtime:"+str(lastrejectedtime)+" diff:"+str(lastrejectedtime + datetime.timedelta(seconds = 30)))
                elif(qty_ < existing_qty_):
                    intraday_positions[Noid][0]['quantity'] = existing_qty_ - qty_
                elif(qty_ > existing_qty_):
                    intraday_positions[Noid][0]['quantity'] = qty_ - existing_qty_
                positionsLock.release()
                return
            else:
                intraday_positions[Noid][0]['quantity'] += t['filled_quantity']
                print("Check if this is partial fill or duplicate update."+
                        "As of now udate qty to:"+str(intraday_positions[Noid][0]['quantity'])+" for Noid:"+str(Noid))
                logging.info("Update:"+str(t)+" pos:"+str(intraday_positions[Noid][0]))
                positionsLock.release()
                return
        else:
            print("New order update received, adding to intraday_pos")
            positions_ = []
            dataMap = {}
            dataMap["order_id"] = t['order_id']
            dataMap["variety"] = var_
            dataMap["exchange"] = t['exchange']
            dataMap["tradingsymbol"] = t['tradingsymbol']
            dataMap["instrument_token"] = t['instrument_token']
            dataMap["transaction_type"] = t['transaction_type']
            dataMap["order_type"] = t['order_type']
            dataMap["validity"] = t['validity']
            dataMap["product"] = t['product']
            dataMap["quantity"] = t['quantity']
            dataMap["average_price"] = t['average_price']
            dataMap["trigger_price"] = t['trigger_price']
            dataMap["price"] = t['price']
            if(squareoff_orders.__contains__(t['order_id'])):
                dataMap["opp_order_raised"] = True
                dataMap["opp_orderid"] = squareoff_orders[t['order_id']]
            elif(co_sl_orders.__contains__(t['order_id'])): #CO Orders
                dataMap["opp_order_raised"] = True
                dataMap["opp_orderid"] = co_sl_orders[t['order_id']]
            else:
                print("Opp order not found for:"+str(t['order_id']))
                dataMap["opp_order_raised"] = False
                dataMap["opp_orderid"] = 0
            dataMap["strategyId"] = orderIds.get(t['order_id'],1)
            dataMap["tkey"] = _key

            positions_.append(dataMap)
            intraday_positions[t['variety']+t['tradingsymbol']+t['product']] = positions_

            if(liveOrderCount.__contains__(_key)):
                liveOrderCount[_key] += 1
            else:
                liveOrderCount[_key] = 1
            print("liveOrderCount for key:"+str(_key) +" is:"+str(liveOrderCount[_key]))
            AddToOpenOrdersInProcess(ts_)
        positionsLock.release()

def readLtpFromFifo(treadName):
    global lastltptime
    #token_price_ltp[2029825]=630
    with open(FIFO) as fifo:
        while True:
            data = fifo.read()
            if len(data) == 0:
                continue
            #print("line:"+data)
            lines=data.split("\n")
            lastltptime = datetime.datetime.now()
            for line in lines:
                if len(line) == 0:
                    continue
                try:
                    tokens = line.split(',')
                    tok = int(tokens[0])
                    price = float(tokens[1].rstrip('\n'))
                    token_price_ltp[tok]=price

                    #if(datetime.datetime.now().second==0 and tok in fut_eq_map):
                    #    if(price<token_price_ltp[fut_eq_map[tok]]):
                    #        logging.info("FUT is less than spot for:"+raw_symbols[tok])
                    #        print("FUT is less than spot for:"+raw_symbols[tok])
                    if(tok in token_ceioi_price):
                        if(price<=token_ceioi_price[tok]):
                            #logging.info("AJIT::Buy "+str(raw_symbols[tok])+" as below our level");
                            if(((datetime.datetime.now().hour==9 and datetime.datetime.now().minute>=15)) or (datetime.datetime.now().hour>9)):
                                msg="Buy%20"+str(raw_symbols[tok])+"%20as%20below%20our%20level"
                                urllib.request.urlopen(f"https://api.telegram.org/bot709093354:AAGNzbXb-SxcPIVrIF8S4m8xT2SSlVsnaNw/sendMessage?chat_id=@asachtp&text={msg}")
                                del token_ceioi_price[tok]
                        elif(price>token_high_price[tok]):
                            msg="Buy%20"+str(raw_symbols[tok])+"%20as%20above%20PDH%20level"
                            urllib.request.urlopen(f"https://api.telegram.org/bot709093354:AAGNzbXb-SxcPIVrIF8S4m8xT2SSlVsnaNw/sendMessage?chat_id=@asachtp&text={msg}")
                            del token_ceioi_price[tok]
                    elif(tok in token_peioi_price):
                        if(price>=token_peioi_price[tok]):
                            #logging.info("AJIT::Sell "+str(raw_symbols[tok])+" as above our level");
                            if((datetime.datetime.now().hour==9 and datetime.datetime.now().minute>=15) or (datetime.datetime.now().hour>9)):
                                msg="Sell%20"+str(raw_symbols[tok])+"%20as%20Above%20our%20level"
                                urllib.request.urlopen(f"https://api.telegram.org/bot709093354:AAGNzbXb-SxcPIVrIF8S4m8xT2SSlVsnaNw/sendMessage?chat_id=@asachtp&text={msg}")
                                del token_peioi_price[tok]
                        elif(price<token_low_price[tok]):
                            msg="Sell%20"+str(raw_symbols[tok])+"%20as%20Below%20PDL%20level"
                            urllib.request.urlopen(f"https://api.telegram.org/bot709093354:AAGNzbXb-SxcPIVrIF8S4m8xT2SSlVsnaNw/sendMessage?chat_id=@asachtp&text={msg}")
                            del token_peioi_price[tok]
                    #logging.error("LTP time:"+str(lastltptime))
                    #print(str(tok)+":"+str(price))
                except Exception as e:
                    logging.info("Error processing ltp update:".format(e)+" line:"+str(line)+" tok:"+str(tok)) 
                    logging.error(repr(e))
#Need to test below func and monitor cpu utilization
def readLtpFromFifo2(treadName):
    while True:
        with open(FIFO) as fifo:
            while True:
                data = fifo.read()
                if len(data) == 0:
                    break
                lines=data.split("\n")
                for line in lines:
                    if len(line) == 0:
                        continue
                    try:
                        tokens = line.split(',')
                        tok = int(tokens[0])
                        price = float(tokens[1].rstrip('\n'))
                        token_price_ltp[tok]=price
                        print(str(tok)+":"+str(price))
                    except Exception as e:
                        logging.info("Error processing ltp update:".format(e)+" line:"+str(line)+" tok:"+str(tok)) 
def readLtpFromFifo1(treadName):
    #with open(FIFO) as fifo:
    #fifo = os.open(FIFO,os.O_RDONLY)
    while True:
            pipein = open(FIFO, 'r')
            line = pipein.readline().rstrip('\n')
            if len(line) == 0:
                continue
            #line = fifo.read()
            try:
                tokens = line.split(',')
                tok = int(tokens[0])
                price = float(tokens[1].rstrip('\n'))
                token_price_ltp[tok]=price
                print(str(tok)+":"+str(price))
            except Exception as e:
                logging.info("Error processing ltp update:".format(e)+" line:"+str(line)+" tok:"+str(tok)) 
            #print(str(token_price_ltp[tok]))
            #if len(line) == 0:
            #    print("Writer closed")
            #    break
            #print('Read: "{0}"'.format(line))
def OpenPositionsCount():
    _pos = kite.positions()['day']
    _cnt=0
    for kpos in _pos:
        if(kpos['quantity']!=0):
            _cnt += 1
    return _cnt

def squareoff_all_Openorders():
    logging.info("called squareoff_all_Openorders")
    done=False
    while not done:
        try:
            lorders = kite.orders()
            done=True
        except Exception as e:
            logging.error("Error getting positions:".format(e))
            done=False
    for k in lorders:
        var = k['variety']
        oid = k['order_id']
        #if(k['status'] == "OPEN" or k['status'] == "TRIGGER PENDING"):
        if(k['status'] == "OPEN"):
            logging.info("cancelling %s %s" % (oid,var))
            try:
                kite.cancel_order(variety=var,order_id=oid)
            except Exception as e:
                logging.error("Cannot cancel order:".format(e))
        elif(k['status'] == "TRIGGER PENDING"):
            logging.info("exiting %s %s" % (oid,var))
            try:
                kite.exit_order(variety=var,order_id=oid)
            except Exception as e:
                logging.error("Cannot exit order:".format(e))
    #Sleep is required for us to wait for intraday_pos to be cleared after exiting orders
    time.sleep(5)
    positionsLock.acquire()
    dpositions = dict(intraday_positions)
    positionsLock.release()
    for key in dpositions:
        print("key:"+str(key))
        for j in dpositions[key]:
            print("j:"+str(j))
            if(j['quantity']==0):
                continue
            order_id = sendOppOrder(j,"MARKET",0)


def reconPositions():
    try:
        _pos = kite.positions()['day']
    except Exception as e:
        logging.error("Error getting positions:".format(e))
    deleteList = []
    positionsLock.acquire()
    for key in intraday_positions:
        #j = dpositions[key]
        #print("key:"+str(key))
        for j in intraday_positions[key]:
            #print("j:"+str(j))
            var = j['variety']
            oid = j['order_id']
            ts = j['tradingsymbol']
            pdt = j['product']
            itoken = int(j['instrument_token'])
            avgpx = j['price']
            if(avgpx==0):
                avgpx = j['average_price']
            Noid=var+ts+pdt
            found=False
            for kpos in _pos:
                #kpos = _pos[item]
                if(kpos['quantity']==0):
                    continue
                print(kpos)
                if (kpos['tradingsymbol']==ts and kpos['product']==pdt):
                    found=True
                    print(kpos)
                    if(kpos['quantity']!=j['quantity']):
                        intraday_positions[Noid][0]['quantity']=kpos['quantity']
                        if(kpos['quantity'] > 0):
                            intraday_positions[Noid][0]['transaction_type']="BUY"
                        else:
                            intraday_positions[Noid][0]['transaction_type']="SELL"
                        #intraday_positions[Noid][0]["opp_order_raised"] = True
                        #intraday_positions[Noid][0]["opp_orderid"] = order['order_id']
                        break
            if(not found):
                deleteList.append(Noid)
    for oid in deleteList:
        if(intraday_positions.__contains__(oid)):
            opp_id = intraday_positions[oid][0]['opp_orderid']
            if(squareoff_orders.__contains__(opp_id)):
                print("Deleting from squareoff too:"+str(opp_id))
                del squareoff_orders[opp_id]
            _key = intraday_positions[oid][0]['tkey']
            if(liveOrderCount.__contains__(_key)):
                liveOrderCount[_key] -= 1
            RemoveFromOrdersInProcess(intraday_positions[oid][0]['tradingsymbol'])
            del intraday_positions[oid]
    positionsLock.release()
    print("###intrday_pos:"+str(intraday_positions))
    logging.info("###intrday_pos:"+str(intraday_positions))

def populateCE():
    try:
        with open('ce.csv') as f:
            lines = f.readlines()
        for i in lines:
            #logging.error("XXXXXXXXXXXXXXXXXXXXXXX"+i)
            tokens = i.strip('\n').split(',')
            a = int(tokens[0])
            b = float(tokens[1])
            token_ceioi_price[a]=b
            logging.error("Error downloading CE signals:"+str(token_ceioi_price))
    except Exception as e:
        logging.error("Error downloading CE signals:"+str(e))
    logging.info("ceioi populated")
def populatePE():
    try:
        with open('pe.csv') as f:
            lines = f.readlines()
        for i in lines:
            #logging.error("XXXXXXXXXXXXXXXXXXXXXXX"+i)
            tokens = i.strip('\n').split(',')
            a = int(tokens[0])
            b = float(tokens[1])
            token_peioi_price[a]=b
    except Exception as e:
        logging.error("Error downloading PE signals:"+str(e))
    logging.info("peioi populated")
def populateOpen():
    try:
        with open('open.csv') as f:
            lines = f.readlines()
        for i in lines:
            tokens = i.strip('\n').split(',')
            a = str(tokens[0])
            b = float(tokens[1])
            token_open_price[a]=b
    except Exception as e:
        logging.error("Error downloading open data:"+str(e))
    print("Open populated")

def populateClose():
    try:
        with open('close.csv') as f:
            lines = f.readlines()
        for i in lines:
            try:
                tokens = i.strip('\n').split(',')
                a = str(tokens[0])
                b = float(tokens[1])
                #print(symbols_token[a])
                token_close_price[symbols_token[a]]=b
            except Exception as e:
                logging.error("Error processing close data for:"+str(e))
                #print(repr(e))
                continue
        print(token_close_price[BNF_TICKER])
        print(token_close_price[NIFTY_TICKER])
    except Exception as e:
        logging.error("Error processing close data:"+str(e))
        print(repr(e))
    print("Close populated")
def populateHigh():
    try:
        with open('high.csv') as f:
            lines = f.readlines()
        for i in lines:
            try:
                tokens = i.strip('\n').split(',')
                a = str(tokens[0])
                b = float(tokens[1])
                c = float(tokens[2])
                token_high_price[symbols_token[a]]=b
                token_low_price[symbols_token[a]]=c
            except Exception as e:
                logging.error("Error processing prev high data for:"+str(e))
                continue
        print(token_high_price[BNF_TICKER])
        print(token_high_price[NIFTY_TICKER])
    except Exception as e:
        logging.error("Error processing prev high data:"+str(e))
        print(repr(e))
    logging.info("Prev High populated")
def populateCpr():
    try:
        with open('cpr.csv') as f:
            lines = f.readlines()
        for i in lines:
            try:
                tokens = i.strip('\n').split(',')
                a = str(tokens[0])
                b = float(tokens[1])
                token_cpr_price[symbols_token[a]]=b
            except Exception as e:
                logging.error("Error processing cpr data for:"+str(e))
                continue
        print(token_cpr_price[BNF_TICKER])
        print(token_cpr_price[NIFTY_TICKER])
    except Exception as e:
        logging.error("Error processing daily cpr data:"+str(e))
        print(repr(e))
    try:
        for itr in pdh_tokens:
            print(token_cpr_price[itr])
    except Exception as e:
        pass
    logging.info("CPR populated:"+str(len(token_cpr_price)))
#populateClose()

pdh_tokens = [3861249,60417,2714625,134657,140033,3834113,794369,2953217,2889473,2952193,857857,340481,2800641,356865,900609,85761,2455041,2796801,3443457,815617,1068033,953345]
high_Success_list = [140033,2889473]
pdh_order_token = []
def preparePDHSymbols():
    print("preparePDHSymbols called")
    time.sleep(1)    
    try:
        for itr in pdh_tokens:
            logging.info("sym:"+str(raw_symbols[itr])+" prevhigh:"+str(token_high_price[itr])+" preopen:"+str(token_price_ltp[itr]))
            if(token_price_ltp[itr] > token_high_price[itr]):
                pdh_order_token.append(itr)
        logging.info("Found "+str(len(pdh_order_token))+" PDH symbols")
        if(len(pdh_order_token)>0):
            logging.info(pdh_order_token)
        msg="Sell%20"
        for token in pdh_order_token:
            ltp=token_price_ltp[token]
            delta=ltp*0.01
            Qty=int(int(PDH_RISK)/delta)

            #For High Probability stocks double the Risk , Double the Qty
            if( token in high_Success_list):
                Qty=Qty*1

            #loop_func(symbol_=raw_symbols[token],direction_="SELL",price_=ltp,strategyId_=99,type_="EQ")
            #continue
            #oid=TradeCO(
            #    symbol=raw_symbols[token],
            #    price=token_price_ltp[token],
            #    trigger_price=round(ltp+delta,1),
            #    squareoff=0,
            #    stoploss=ltp+delta,
            #    trailing_stoploss=delta,
            #    direction="SELL",
            #    qty=Qty
            #    )
            oid=TradeGTT(
                symbol=raw_symbols[token],
                price=token_price_ltp[token],
                squareoff=round(token_cpr_price[token] + (0.002*ltp),1),
                stoploss=round(ltp+delta,1),
                trailing_stoploss=delta,
                direction="BUY",
                qty=Qty
                )
            tmpID=TradeRegularMISOrder(
                symbol=raw_symbols[token],
                price=token_price_ltp[token],
                squareoff=None,
                stoploss=None,
                trailing_stoploss=None,
                direction="SELL",
                qty=Qty
                )
            msg=msg+str(raw_symbols[token])+","
        msg=msg+"%20PDH"
        urllib.request.urlopen(f"https://api.telegram.org/bot709093354:AAGNzbXb-SxcPIVrIF8S4m8xT2SSlVsnaNw/sendMessage?chat_id=@asachtp&text={msg}")

    except Exception as e:
        logging.error("Error sending PDH orders:"+str(e))
        print(repr(e))

    try:
        time.sleep(5)
        reconPositions()
        #Below is requird because, order updates are not processed in passive setup (lightweight)
        logging.info("Calling populate data from PDH")
        populateExistingData()
        logging.info("preparePDHSymbols:passiveStatusCache:"+str(passiveStatusCache))
    except Exception as e:
        logging.error("Issue with populateExistingData"+str(e))
        logging.error(repr(e))

passiveOrders = []
def exitShortStraddle(idx):
    reconPositions()
    #with open("passiveorders") as f:
    #    lorders = f.readlines()
    #i=0
    #while i<len(lorders):
    #    passiveOrders.append(int(lorders[i]))

    positionsLock.acquire()
    dpositions = dict(intraday_positions)
    positionsLock.release()
    #print(token_price_ltp)
    for key in dpositions:
        #j = dpositions[key]
        print("key:"+str(key))
        for j in dpositions[key]:
            print("j:"+str(j))
            if(j['quantity']==0):
                continue
            logging.error(passiveOrders)
            if(int(j['order_id']) in passiveOrders or j['order_id'] in passiveOrders):
                if(idx=="BNF" and squareoff_orders[int(j['order_id'])]==BNF_TICKER):
                    order_id = sendOppOrder(j,"MARKET",0)
                    passiveOrders.remove(int(j['order_id']))
                elif(idx=="NIFTY" and squareoff_orders[int(j['order_id'])]==NIFTY_TICKER):
                    order_id = sendOppOrder(j,"MARKET",0)
                    passiveOrders.remove(int(j['order_id']))
            else:
                logging.error("Not a passive order:"+str(j['order_id']))
                logging.error(repr(e))

passiveStatusCache = {}
passivelockActivated = {}
def sendShortStraddle(idx,direction):
    print("called sendShortStraddle with idx:"+idx+" direction:"+direction)
    passiveStatusCache.clear()
    squareoff_orders.clear()
    passiveOrders.clear()
    qty=0
    if(idx=="NIFTY"):
        qty=NIFTY_PASSIVE_QTY
    elif(idx=="BNF"):
        qty=BNF_PASSIVE_QTY
    if(direction=="UP"):
        TS1=raw_symbols[shortStraddleOption("PE",idx)]
        TS2=raw_symbols[shortStraddleOption("CE",idx)]
    else:
        TS1=raw_symbols[shortStraddleOption("CE",idx)]
        TS2=raw_symbols[shortStraddleOption("PE",idx)]
    SSOID1=sendOrder(
                 variety_=kite.VARIETY_REGULAR,
                 tradingsymbol_=TS1,
                 exchange_="NFO",
                 transaction_type_="SELL",
                 quantity_=qty,
                 order_type_=kite.ORDER_TYPE_MARKET,
                 price_=0,
                 product_=kite.PRODUCT_MIS)
    SSOID2=sendOrder(
                 variety_=kite.VARIETY_REGULAR,
                 tradingsymbol_=TS2,
                 exchange_="NFO",
                 transaction_type_="SELL",
                 quantity_=qty,
                 order_type_=kite.ORDER_TYPE_MARKET,
                 price_=0,
                 product_=kite.PRODUCT_MIS)
    passivelockActivated[idx]=9999999
    #SSOID1=datetime.datetime.now().microsecond
    #SSOID2=datetime.datetime.now().microsecond+1
    if(SSOID1!=None and SSOID2!=None and int(SSOID1) > 0 and int(SSOID2) > 0):
        ticker=0
        if(idx=="BNF"):
            ticker=BNF_TICKER
        elif(idx=="NIFTY"):
            ticker=NIFTY_TICKER
        f=open("passiveorders","a+")
        f.write(str(SSOID1)+','+str(ticker)+','+str(TS1)+'\n')
        f.write(str(SSOID2)+','+str(ticker)+','+str(TS2)+'\n')
        f.close()
        squareoff_orders[SSOID1]=ticker
        squareoff_orders[SSOID2]=ticker
        passiveOrders.append(SSOID1)
        passiveOrders.append(SSOID2)
        tmpCache = {}
        tmpCache[TS1]=0
        tmpCache[TS2]=0
        passiveStatusCache[idx]=tmpCache
    print("sendShortStraddle:passiveStatusCache:"+str(passiveStatusCache))

    #reconPositions()
    #Below is requird because, order updates are not processed in passive setup (lightweight)
    #populateExistingData()

def readMA():
    import urllib.request
    try:
        contents = urllib.request.urlopen("http://"+DATA_HOST+"/madata.txt").read().decode().rstrip('\n')
        for i in contents.splitlines():
            tokens = i.split(',')
            a = str(tokens[0])
            b = float(tokens[1])
            c = float(tokens[2])
            maCache[a]=b
            emaCache[a]=c
    except Exception as e:
        logging.error("Error downloading files:"+str(e))
    #print(maCache)
    print("MA done")

def cancel_squareoff_open_orders(threadName):
    itr = 0
    global lastrejectedtime
    global straddleadjusted
    global lastltptime
    lastrejectedtime = datetime.datetime.now()
    print("CSOO now:"+str(datetime.datetime.now())+" lastrejectedtime:"+str(lastrejectedtime)+" diff:"+str(lastrejectedtime + datetime.timedelta(seconds = 30)))
    shortStraddle_done=False
    if(datetime.datetime.now().hour==9 and datetime.datetime.now().minute>=16):
        shortStraddle_done=True
    time.sleep(30)
    populateClose()
    populateHigh()
    populateCpr()
    while True:
        try:
            #Inititate Short Straddle at 9:15
            if( shortStraddle_done==False and datetime.datetime.today().weekday() >=0 and datetime.datetime.today().weekday() <=5):
                if(datetime.datetime.now().hour==9 and datetime.datetime.now().minute==14 and datetime.datetime.now().second>=59):
                #if(True):
                    #set 0 below for testing on Monday
                    if( datetime.datetime.today().weekday() >=SHORT_STRADDLE_FROM_DAY and datetime.datetime.today().weekday() <=SHORT_STRADDLE_TO_DAY):
                        shortStraddle_done=True
                        #token_price_ltp[BNF_TICKER]=35120.3
                        #token_price_ltp[NIFTY_TICKER]=15720.2
                        #sendShortStraddle()
                        with open("passiveorders", 'w+'): pass
                        if(token_price_ltp[BNF_TICKER]>0 and token_price_ltp[BNF_TICKER] > token_close_price[BNF_TICKER]):
                            bnfdirection="UP"
                        else:
                            bnfdirection="DOWN"
                        if(token_price_ltp[NIFTY_TICKER]>0 and token_price_ltp[NIFTY_TICKER] > token_close_price[NIFTY_TICKER]):
                            nfdirection="UP"
                        else:
                            nfdirection="DOWN"
                        time.sleep(0.998)
                        t1 = threading.Thread(target=sendShortStraddle, args=("BNF",bnfdirection,))
                        #t2 = threading.Thread(target=sendShortStraddle, args=("NIFTY",nfdirection,))
                        t1.start()
                        #t2.start() #AMIT
                    #token_high_price[3834113]=195
                    #token_price_ltp[3834113]=200
                    #t3 = threading.Thread(target=preparePDHSymbols,)
                    #t3.start()
                #Done sleep until 9:16
                elif(datetime.datetime.now().hour==9 and datetime.datetime.now().minute<=16):
                    #print("Waiting for SS")
                    continue
            time.sleep(30)
            if(datetime.datetime.now() >= lastltptime + datetime.timedelta(seconds = 60) ):
                logging.error("LTP not received from 1 min:"+str(lastltptime))
                print("LTP not received from 1 min")
            #if(datetime.datetime.now() >= lastltptime + datetime.timedelta(seconds = 600) ):
            #    squareoff_all_Openorders()
            if(datetime.datetime.now().hour==15 and datetime.datetime.now().minute==14 and len(intraday_positions)>0):
                reconPositions()
                squareoff_all_Openorders()

            exitedList = []
            if(itr%2==0):
                for idx in passiveStatusCache:
                    item = passiveStatusCache[idx]
                    cost=0
                    currentCost=0
                    profitable_leg = None
                    CURR_QTY=0
                    CURR_LOTS=0
                    LEG_LIMIT=0
                    if(idx == "BNF"):
                        CURR_QTY=BNF_PASSIVE_QTY
                        CURR_LOTS=BNF_PASSIVE_LOTS
                        LEG_LIMIT=BNF_PROFIT_LEG_PRICE
                    elif(idx == "NIFTY"):
                        CURR_QTY=NIFTY_PASSIVE_QTY
                        CURR_LOTS=NIFTY_PASSIVE_LOTS
                        LEG_LIMIT=NIFTY_PROFIT_LEG_PRICE
                    for ts in item:
                        cost+=item[ts]
                        currentCost+=token_price_ltp[symbols_token[ts]]
                        print(str(idx)+" currentCost:"+str(currentCost))
                        logging.info("LTP:"+ts+":"+str(token_price_ltp[symbols_token[ts]])+" for:"+idx)
                       #Will see how to implement this for exit
                        if(token_price_ltp[symbols_token[ts]] < LEG_LIMIT):
                            profitable_leg = ts
                            logging.info(str(ts)+": is profitable with ltp:"+str(token_price_ltp[symbols_token[ts]])+" limit:"+str(LEG_LIMIT))
                    currentCost=currentCost*CURR_QTY
                    cost=cost*CURR_QTY
                    logging.info(str(idx)+" currentCost:"+str(currentCost)+" cost:"+str(cost)+" pnl:"+str(cost-currentCost))
                    #Add logic to exit profitable leg as per the day
                    if(currentCost-cost >= PASSIVE_MAXLOSS_PER_BASKET * CURR_LOTS):
                        logging.info("SL for passive hit")
                        exitShortStraddle(idx)
                        exitedList.append(idx)
                    if(passivelockActivated[idxx]>0 and currentCost>(passivelockActivated[idxx] + (PASSIVE_TRAIL * CURR_LOTS))):
                        logging.error("Exiting:Locking was activated and current cost reduced from:"+str(passivelockActivated[idx])+" to:"+str(currentCost))
                        exitShortStraddle(idx)
                        exitedList.append(idx)
                    elif(cost-currentCost>=PASSIVE_PROFIT * CURR_LOTS):
                        if(currentCost<passivelockActivated[idx]):
                            print("Locking Activated "+str(idx)+" currentCost:"+str(currentCost))
                            logging.error("Locking Activated "+str(idx)+" currentCost:"+str(currentCost))
                            passivelockActivated[idx]=currentCost
                for item in exitedList:
                    del passiveStatusCache[item]
            itr = itr + 1
        except Exception as e:
            logging.error("Exception in CANCEL thread:"+str(e))
            logging.error(repr(e))

def modifyCO(j,price):
    print("modifyCO called for:"+str(j['opp_orderid'])+" price:"+str(price))
    price=round(price,1)
    if(j['opp_orderid']==0):
        return -1

    return kite.modify_order(
             variety=j['variety'],
             order_id=j['opp_orderid'],
             price=price,
             trigger_price=price
            )

def sendOppOrder(j,otype,price):
    print("sendOppOrder called")
    price=round(price,1)
    qty=(j['quantity'])
    if(j['transaction_type'] == "BUY"):
        direction="SELL"
        if price!=0:
            price=price-0.05
    else:
        direction="BUY"
        if price!=0:
            price=price+0.05

    if(qty<0):
        qty=qty*-1
    
    variety = j['variety']
    if(j['variety'] == "amo" ):
        variety = kite.VARIETY_REGULAR

    return sendOrder(
         variety_=j['variety'],
         tradingsymbol_=j['tradingsymbol'],
         exchange_=j['exchange'],
         transaction_type_=direction,
         quantity_=qty,
         order_type_=otype,
         price_=price,
         product_=j['product'])

def trailCO(threadName):
    itr = 0
    global lastrejectedtime
    lastrejectedtime = datetime.datetime.now()
    print("CSCO now:"+str(datetime.datetime.now())+" lastrejectedtime:"+str(lastrejectedtime)+" diff:"+str(lastrejectedtime + datetime.timedelta(seconds = 30)))
    while True:
        time.sleep(60)
        if(datetime.datetime.now().minute%5==0):
            print("Running:"+threadName)
            time.sleep(22)
            try:
                try:
                    readMA()
                except Exception as e:
                    logging.error("Error downloading MA files:"+str(e))
                try:
                    lorders = kite.orders()
                except Exception as e:
                    logging.debug("Error getting orders:".format(e)) 
                    continue
                #print("lorders:"+str(lorders))
                positionsLock.acquire()
                dpositions = dict(intraday_positions)
                positionsLock.release()
                needRecon=False
                for key in dpositions:
                    #j = dpositions[key]
                    print("key:"+str(key))
                    for j in dpositions[key]:
                        if( j['order_id'] in passiveOrders):
                            continue
                        #print("j:"+str(j))
                        if(j['quantity']==0):
                            continue
                        var = j['variety']
                        oid = j['order_id']
                        otoken = j['tradingsymbol']
                        itoken = int(j['instrument_token'])
                        Noid=j['variety']+j['tradingsymbol']+j['product']
                        tgrpx = j['trigger_price']
                        if(tgrpx==0):
                            tgrpx = j['price']
                        avgpx = j['price']
                        if(avgpx==0):
                            avgpx = j['average_price']
                        ts = j['transaction_type']
                        lastpx = token_price_ltp[itoken]
                        MA = getMA(otoken)
                        EMA = getEMA(otoken)

                        print(otoken+" lastpx:"+str(lastpx))
                        if(lastpx == 0 and EMA==0):
                            continue
                    
                        #ltype = isIndexOption(itoken)
                        stype = symbol_to_type[otoken]

                        print(stype+" avgpx:"+str(avgpx)+" oid:"+str(oid)+" oppoid:"+str(j['opp_orderid']))
                        exited=False
                        try:
                            if(var==kite.VARIETY_CO):
                                print("Found CO")
                                if(ts == "BUY"):
                                    mod_price=tgrpx
                                    process=False
                                    if(lastpx >= (avgpx+ 0.030*avgpx)):
                                        kite.exit_order(variety=j['variety'],order_id=j['order_id'])
                                        process=False
                                    elif(EMA==0 or EMA>lastpx):
                                        if(lastpx<200):
                                            mod_price=lastpx-0.5
                                        elif(lastpx<500):
                                            mod_price=lastpx-1
                                        elif(lastpx<1000):
                                            mod_price=lastpx-2
                                        elif(lastpx<2000):
                                            mod_price=lastpx-3
                                        process=True
                                    else:
                                        if(abs(EMA-lastpx)>=0.01*lastpx):
                                            EMA=lastpx-1 #In case of big gap between EMA and px
                                        else:
                                            EMA=EMA-0.2 #Four ticks below EMA
                                        mod_price=EMA
                                        process=True
                                    print("mod_price:"+str(mod_price)+" avgpx:"+str(avgpx)+" lastpx:"+str(lastpx)+" tgrpx:"+str(tgrpx))
                                    if(mod_price<=tgrpx):
                                        print("mod_price <= tgrpx so ignoring")
                                        process=False
                                    if(process):
                                        if(mod_price<token_price_ltp[j['instrument_token']]):
                                            print("mod_price is less than ltp so considering for ltp:"+str(token_price_ltp[j['instrument_token']]))
                                            try:
                                                print("...............Modifying price from:"+str(tgrpx)+" to:"+str(mod_price))
                                                if(modifyCO(j,mod_price)!=-1):
                                                    positionsLock.acquire()
                                                    intraday_positions[Noid][0]['trigger_price']=round(mod_price,1)
                                                    positionsLock.release()
                                            except Exception as e:
                                                logging.info("Error in modifying CO :"+str(j['opp_orderid']))
                                                print(repr(e))
                                                if("exceeded" in repr(e)):
                                                   kite.exit_order(variety=j['variety'],order_id=j['order_id'])
                                                elif("processed" in repr(e)):
                                                    needRecon=True
                                elif(ts == "SELL"):
                                    mod_price=tgrpx
                                    process=False
                                    if(lastpx <= (avgpx- 0.030*avgpx)):
                                        kite.exit_order(variety=j['variety'],order_id=j['order_id'])
                                        process=False
                                    elif(EMA==0 or EMA<lastpx):
                                        if(lastpx<200):
                                            mod_price=lastpx+0.5
                                        elif(lastpx<500):
                                            mod_price=lastpx+1
                                        elif(lastpx<1000):
                                            mod_price=lastpx+2
                                        elif(lastpx<2000):
                                            mod_price=lastpx+3
                                        process=True
                                    else:
                                        if(abs(EMA-lastpx)>=0.01*lastpx):
                                            EMA=lastpx+1 #In case of big gap between EMA and px
                                        else:
                                            EMA=EMA+0.2 #Four ticks above EMA
                                        mod_price=EMA
                                        process=True
                                    print("mod_price:"+str(mod_price)+" avgpx:"+str(avgpx)+" lastpx:"+str(lastpx)+" tgrpx:"+str(tgrpx))
                                    if(mod_price>=tgrpx):
                                        print("mod_price >= tgrpx so ignoring")
                                        process=False
                                    if(process):
                                        if(mod_price>token_price_ltp[j['instrument_token']]):
                                            print("mod_price is greater than ltp so considering for ltp:"+str(token_price_ltp[j['instrument_token']]))
                                            try:
                                                print("...............Modifying price from:"+str(tgrpx)+" to:"+str(mod_price))
                                                if(modifyCO(j,mod_price)!=-1):
                                                    positionsLock.acquire()
                                                    intraday_positions[Noid][0]['trigger_price']=mod_price
                                                    positionsLock.release()
                                            except Exception as e:
                                                logging.info("Error in modifying CO :"+str(j['opp_orderid']))
                                                print(repr(e))
                                                if("exceeded" in repr(e)):
                                                    kite.exit_order(variety=j['variety'],order_id=j['order_id'])
                                                elif("processed" in repr(e)):
                                                    needRecon=True
                        except Exception as e:
                            logging.debug("Error getting orders:".format(e)) 
            except Exception as e:
                logging.debug("Error getting orders:".format(e)) 
                continue

populateCE()
populatePE()
ioithreadList = ["IOI Thread-1", "IOI Thread-2", "IOI Thread-3","CANCEL","ltpreader","updateCO"]
ioiqueueLock = threading.Lock()
positionsLock = threading.Lock()
bsLock = threading.Lock()
opLock = threading.Lock()
OrdersLock = threading.Lock()
ioithreads = []
ioithreadID = 1

for tName in ioithreadList:
   thread = IOIProcessor(ioithreadID, tName)
   thread.start()
   ioithreads.append(thread)
   ioithreadID += 1

populateExistingData()
if False:
    order_id = sendOrder(
        variety_=kite.VARIETY_REGULAR,
        tradingsymbol_="TCS",
        exchange_="NSE",
        transaction_type_="BUY",
        quantity_=1,
        order_type_=kite.ORDER_TYPE_LIMIT,
        price_=3120,
        product_=kite.PRODUCT_MIS)
    oid1 = TradeGTT(
        symbol="INFY",
        price=1380,
        squareoff=1450,
        stoploss=1290,
        trailing_stoploss=5,
        direction="BUY",
        qty=1
        )
#readMA()
#print(str(getMA("APOLLOTYRE")))
#print(str(getEMA("APOLLOTYRE")))
#reconPositions()
#sudo rabbitmqctl list_queues name messages_ready messages_unacknowledged

#with open('my_dict.json', 'w') as f:
#    json.dump(my_dict, f)

# elsewhere...

#with open('my_dict.json') as f:
#    my_dict = json.load(f)
