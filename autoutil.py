import logging

import datetime
import os
import time

from inspect import currentframe

logging.basicConfig(
         format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
         level=logging.INFO,
         datefmt='%Y-%m-%d %H:%M:%S')

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

BNF_TICKER=260105
NIFTY_TICKER=256265
INDIA_VIX=264969

PDH_RISK=1000
BNF_PASSIVE_LOTS=1
BNF_PASSIVE_QTY=BNF_PASSIVE_LOTS*25
NIFTY_PASSIVE_LOTS=1
NIFTY_PASSIVE_QTY=NIFTY_PASSIVE_LOTS*50
PASSIVE_PROFIT=2000
PASSIVE_TRAIL=1100
BNF_PROFIT_LEG_PRICE=20
NIFTY_PROFIT_LEG_PRICE=10
PASSIVE_MAXLOSS_PER_BASKET=5000
SHORT_STRADDLE_FROM_DAY=0
SHORT_STRADDLE_TO_DAY=4

#Below if is for Monday testing
if(datetime.datetime.today().weekday()==10):
    PASSIVE_PROFIT=200
    PASSIVE_TRAIL=140
    #Profit leg to be tested later
    BNF_PROFIT_LEG_PRICE=100
    NIFTY_PROFIT_LEG_PRICE=80

if(datetime.datetime.today().weekday()==0):
    PASSIVE_PROFIT=1200
    PASSIVE_TRAIL=1100
    BNF_PROFIT_LEG_PRICE=100
    NIFTY_PROFIT_LEG_PRICE=80
elif(datetime.datetime.today().weekday()==1):
    PASSIVE_PROFIT=2000
    PASSIVE_TRAIL=1100
    BNF_PROFIT_LEG_PRICE=60
    NIFTY_PROFIT_LEG_PRICE=80
elif(datetime.datetime.today().weekday()==2):
    PASSIVE_PROFIT=3000
    PASSIVE_TRAIL=2200
    BNF_PROFIT_LEG_PRICE=30
    NIFTY_PROFIT_LEG_PRICE=30
elif(datetime.datetime.today().weekday()==3):
    PASSIVE_PROFIT=4000
    PASSIVE_TRAIL=3200
elif(datetime.datetime.today().weekday()==4):
    PASSIVE_PROFIT=1200
    PASSIVE_TRAIL=1100
    BNF_PROFIT_LEG_PRICE=100
    NIFTY_PROFIT_LEG_PRICE=80

i=0
token_price_count = {}
token_price_ltp = {}
maCache = {}
emaCache = {}
emaNineCache = {}
token_last_bQty = {}
token_last_sQty = {}
token_open_price = {}
token_close_price = {}
token_high_price = {}
token_low_price = {}
token_cpr_price = {}
raw_symbols = {}
symbols_token = {}
symbol_seg = {}
cache_ = {}
spTypeMap = {}
lot_size = {}
symbol_to_type = {}
liveOrderCount = {}
fut_eq_map = {}
token_ceioi_price = {}
token_peioi_price = {}

intraday_positions = {}
lastrejectedtime = datetime.datetime.now()
lastrejectedtime = lastrejectedtime.replace(hour=9, minute=0, second=0, microsecond=0)

def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_lineno

with open('OptionsEQ.csv') as f:
#with open('instruments.xml') as f:
    lines = f.readlines()
    for record in lines:
        _tokens = record.split(',')
        id_ = int(_tokens[0])
        sym_ = _tokens[2]
        eqsym_ = _tokens[3]
        sp_ = _tokens[6]
        lot_ = int(_tokens[8])
        seg_ = _tokens[9]
        type_ = _tokens[10]

        lot_size[sym_] = lot_
        symbol_to_type[sym_] = seg_

        params = []
        tmpDict = {}
        tmpDict["symbol"] = sym_
        tmpDict["segment"] = seg_
        tmpDict["type"] = type_
        tmpDict["sp"] = sp_
        tmpDict["lotsize"] = lot_
        params.append(tmpDict)

        raw_symbols[id_] = sym_
        symbols_token[sym_] = id_
        sym=""
        #print(str(id_)+"$"+sym_)
        token_price_ltp[id_] = 0
        if("NIFTY" not in sym_):
            maCache[sym_] = 0
            emaCache[sym_] = 0
            emaNineCache[sym_] = 0
        symbol_seg[id_] = seg_
        cache_[id_] = params

        spTypeMap[sp_+seg_] = id_

        if(type_=="NFO-FUT"):
            eqsym_=eqsym_.strip('\"')
            if(eqsym_=="NIFTY"):
                eqsym_="NIFTY 50"
            elif(eqsym_=="BANKNIFTY"):
                eqsym_="NIFTY BANK"
            elif(eqsym_=="FINNIFTY"):
                eqsym_="NIFTY FIN SERVICE"
            #print(eqsym_)
            fut_eq_map[id_]=symbols_token[eqsym_]

def instrType(rtoken):
    val = cache_.get(rtoken,"Not Found")
    if(val=="Not Found"):
        return val
    for f in val:
        item = f.get("segment","Not Found")
        type_ = f.get("type","Not Found")
        if(type_=="INDICES"):
            return "INDEX"
        else:
            return item
    return "Not Found"

def isFuture(rtoken):
    val = cache_.get(rtoken,"Not Found")
    if(val=="Not Found"):
        return False
    for f in val:
        item = f.get("type","Not Found")
        if item == "NFO-FUT":
            return True
    return False

def isIndexOption(rtoken):
    val = cache_.get(rtoken,"Not Found")
    if(val=="Not Found"):
        return "NA"
    for f in val:
        item = f.get("type","Not Found")
        if item == "NFO-OPT":
            sym = raw_symbols[rtoken]
            if "BANKNIFTY" in sym:
                return "BNF"
            if "NIFTY" in sym:
                return "NIFTY"
    return "NA"

def isBankNifty(rtoken):
    val = cache_.get(rtoken,"Not Found")
    if(val=="Not Found"):
        return False
    for f in val:
        item = f.get("type","Not Found")
        if item == "INDICES":
            sym = raw_symbols[rtoken]
            #sym = f.get("symbol","Not Found")
            if "NIFTY BANK" in sym:
                return True
    return False

def getTickerSp(rtoken):
    val = cache_.get(rtoken,0)
    for f in val:
        item = f.get("sp",0)
        return item
    return 0

def getBNFITMCEVal():
    val=int(token_price_ltp[BNF_TICKER])
    if(val==0):
        return 0
    val = int((val / 100)) - 1
    val = val * 100
    return int(val)

def getidxITMCEVal(val,idx):
    #print("getidxITMCEVal val:"+str(val))
    if(val==0):
        return 0
    mul=100
    if(idx=="NIFTY"):
        mul=50
    elif(idx=="BNF"):
        mul=100
    val = int((val / mul)) - 1
    val = val * mul
    print("getidxITMCEVal val:"+str(val))
    return int(val)

def getidxITMPEVal(val,idx):
    print("getidxITMPEVal val:"+str(val))
    if(val==0):
        return 0
    mul=100
    if(idx=="NIFTY"):
        mul=50
    elif(idx=="BNF"):
        mul=100
    val = int((val / mul)) + 1
    val = val * mul
    print("getidxITMPEVal val:"+str(val))
    return int(val)

def getgenITMOption(ce_pe,lp,idx):
    if(ce_pe == "CE"):
        return spTypeMap[str(getidxITMCEVal(lp,idx))+ce_pe]
    elif(ce_pe == "PE"):
        return spTypeMap[str(getidxITMPEVal(lp,idx))+ce_pe]
    return 0

def getBNFITMPEVal():
    val=int(token_price_ltp[BNF_TICKER])
    if(val==0):
        return 0
    val = int((val / 100)) + 2
    val = val * 100
    return int(val)

def getATMCEVal(val,idx):
    #val=int(token_price_ltp[BNF_TICKER])
    if(val==0):
        return 0
    mul=100
    if(idx=="NIFTY"):
        mul=50
    elif(idx=="BNF"):
        mul=100
    val = int((val / mul)) - 0
    val = val * mul
    return int(val)

def getATMPEVal(val,idx):
    #val=int(token_price_ltp[BNF_TICKER])
    if(val==0):
        return 0
    mul=100
    if(idx=="NIFTY"):
        mul=50
    elif(idx=="BNF"):
        mul=100
    val = int((val / mul)) + 1
    val = val * mul
    return int(val)

def getITMOption(ce_pe):
    #print(".xx...."+str(token_price_ltp[BNF_TICKER]))
    if(ce_pe == "CE"):
        #print(str(getBNFITMCEVal()))
        return spTypeMap[str(getBNFITMCEVal())+ce_pe]
    elif(ce_pe == "PE"):
        return spTypeMap[str(getBNFITMPEVal())+ce_pe]
    return 0

def shortStraddleOption(ce_pe,idx):
    if(idx=="NIFTY"):
        val=int(token_price_ltp[NIFTY_TICKER])
    elif(idx=="BNF"):
        val=int(token_price_ltp[BNF_TICKER])
    if(val==0):
        return 0
    #print("....val:"+str(val))
    if(val%100<50):
        #print("getgenITMOption:"+str(getgenITMOption(ce_pe,val,idx)))
        return spTypeMap[str(getATMCEVal(val,idx))+ce_pe]
    else:
        #print("getgenITMOption:"+str(getgenITMOption(ce_pe,val,idx)))
        return spTypeMap[str(getATMPEVal(val,idx))+ce_pe]
def shortStrangleOption(ce_pe,idx,diff):
    if(idx=="NIFTY"):
        val=int(token_price_ltp[NIFTY_TICKER])
    elif(idx=="BNF"):
        val=int(token_price_ltp[BNF_TICKER])
    if(val==0):
        return 0
    #print("....val:"+str(val))
    if(val%100<50):
        #print("getgenITMOption:"+str(getgenITMOption(ce_pe,val,idx)))
        return spTypeMap[str(getATMCEVal(val,idx)-diff)+ce_pe]
    else:
        #print("getgenITMOption:"+str(getgenITMOption(ce_pe,val,idx)))
        return spTypeMap[str(getATMPEVal(val,idx)-diff)+ce_pe]
def getMA(symbol):
    try:
        if("BANKNIFTY" in symbol):
            return maCache["NIFTY BANK"]
        elif("FINNIFTY" in symbol):
            return maCache["NIFTY FINANCIAL SERVICES"]
        elif("NIFTY" in symbol):
            return maCache["NIFTY 50"]
        else:
            return maCache[symbol]
    except Exception as e:
        print(repr(e))
        return 0;
    
def getEMA(symbol):
    try:
        if("BANKNIFTY" in symbol):
            return emaCache["NIFTY BANK"]
        elif("FINNIFTY" in symbol):
            return emaCache["NIFTY FINANCIAL SERVICES"]
        elif("NIFTY" in symbol):
            return emaCache["NIFTY 50"]
        else:
            return emaCache[symbol]
    except Exception as e:
        print(repr(e))
        return 0;

def getNineEMA(symbol):
    try:
        if("BANKNIFTY" in symbol):
            return emaNineCache["NIFTY BANK"]
        elif("FINNIFTY" in symbol):
            return emaNineCache["NIFTY FINANCIAL SERVICES"]
        elif("NIFTY" in symbol):
            return emaNineCache["NIFTY 50"]
        else:
            return emaNineCache[symbol]
    except Exception as e:
        print(repr(e))
        return 0;
