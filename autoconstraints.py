MAXPROFIT=10000
MAXLOSS=-5000
MAX_EQ_COST=50000
TOTALOPENORDERS=100

COOLOFF1=300
COOLOFF2=60
COOLOFF3=60
COOLOFF4=60
COOLOFF5=60
COOLOFF6=300
coolOff = {}
coolOff["1"] = 0
coolOff["2"] = 0
coolOff["3"] = 0
coolOff["4"] = 0
coolOff["5"] = 0
coolOff["6"] = 0
StrategyWiseTradeInfo = {}
StrategyWiseTradeInfo["BNF_LOT_SIZE"] = 25 
StrategyWiseTradeInfo["NIFTY_LOT_SIZE"] = 50
#Strategy 1
StrategyWiseTradeInfo["1_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["1_EQMAXORDERS"] = 10
StrategyWiseTradeInfo["1_BNFMAXPROFITPERLOT"] = 60
StrategyWiseTradeInfo["1_BNFMAXLOSSPERLOT"] = 40
StrategyWiseTradeInfo["1_BNF_TRADE_LOTS"] = 1 
StrategyWiseTradeInfo["1_BNFTRADE_QTY"] = StrategyWiseTradeInfo["BNF_LOT_SIZE"]*StrategyWiseTradeInfo["1_BNF_TRADE_LOTS"]
StrategyWiseTradeInfo["1_EQMAXPROFITPERTRADE"] = 0.01
StrategyWiseTradeInfo["1_EQMAXLOSSPERTRADE"] = 0.005
StrategyWiseTradeInfo["1_EQTRADE_QTY"] = 25
#Strategy 6
StrategyWiseTradeInfo["6_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["6_EQMAXORDERS"] = 10
StrategyWiseTradeInfo["6_BNFMAXPROFITPERLOT"] = 25
StrategyWiseTradeInfo["6_BNFMAXLOSSPERLOT"] = 40
StrategyWiseTradeInfo["6_BNF_TRADE_LOTS"] = 2
StrategyWiseTradeInfo["6_BNFTRADE_QTY"] = StrategyWiseTradeInfo["BNF_LOT_SIZE"]*StrategyWiseTradeInfo["6_BNF_TRADE_LOTS"]
StrategyWiseTradeInfo["6_EQMAXPROFITPERTRADE"] = 0.015
StrategyWiseTradeInfo["6_EQMAXLOSSPERTRADE"] = 0.01
StrategyWiseTradeInfo["6_EQTRADE_QTY"] = 25
#Strategy 2
StrategyWiseTradeInfo["2_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["2_EQMAXORDERS"] = 2
StrategyWiseTradeInfo["2_BNFMAXPROFITPERLOT"] = 60
StrategyWiseTradeInfo["2_BNFMAXLOSSPERLOT"] = 30
StrategyWiseTradeInfo["2_BNF_TRADE_LOTS"] = 2
StrategyWiseTradeInfo["2_BNFTRADE_QTY"] = StrategyWiseTradeInfo["BNF_LOT_SIZE"]*StrategyWiseTradeInfo["2_BNF_TRADE_LOTS"]
StrategyWiseTradeInfo["2_EQMAXPROFITPERTRADE"] = 0.01
StrategyWiseTradeInfo["2_EQMAXLOSSPERTRADE"] = 0.01
StrategyWiseTradeInfo["2_EQTRADE_QTY"] = 25
#Strategy 3
StrategyWiseTradeInfo["3_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["3_EQMAXORDERS"] = 2
StrategyWiseTradeInfo["3_BNFMAXPROFITPERLOT"] = 25
StrategyWiseTradeInfo["3_BNFMAXLOSSPERLOT"] = 30
StrategyWiseTradeInfo["3_BNF_TRADE_LOTS"] = 2
StrategyWiseTradeInfo["3_BNFTRADE_QTY"] = StrategyWiseTradeInfo["BNF_LOT_SIZE"]*StrategyWiseTradeInfo["3_BNF_TRADE_LOTS"]
StrategyWiseTradeInfo["3_EQMAXPROFITPERTRADE"] = 0.02
StrategyWiseTradeInfo["3_EQMAXLOSSPERTRADE"] = 0.02
StrategyWiseTradeInfo["3_EQTRADE_QTY"] = 25

StrategyWiseTradeInfo["4_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["4_EQMAXORDERS"] = 2
StrategyWiseTradeInfo["5_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["5_EQMAXORDERS"] = 2
StrategyWiseTradeInfo["6_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["6_EQMAXORDERS"] = 10
StrategyWiseTradeInfo["7_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["7_EQMAXORDERS"] = 10
StrategyWiseTradeInfo["8_BNFMAXORDERS"] = 1
StrategyWiseTradeInfo["8_EQMAXORDERS"] = 10

StrategyWiseTradeInfo["98_EQTRADE_QTY"] = 1
StrategyWiseTradeInfo["98_EQMAXORDERS"] = 100

def getPauseTime(strategyId):
    if(strategyId==4):
        strategyId=2
    elif(strategyId==5):
        strategyId=3
    val = coolOff.get(strategyId,60)
    return val

def getQtyToTrade(strategyId,symbol):
    if(strategyId==4):
        strategyId=2
    elif(strategyId==5):
        strategyId=3
    if(strategyId==98):
        return 1
    return 25
    val = StrategyWiseTradeInfo.get(str(strategyId)+"_"+symbol+"TRADE_QTY",0)
    if(val == 0):
        if(symbol=="BNF"):
            return 25
        if(symbol=="NIFTY"):
            return 50
        else:
            return 25
    return val

def maxOrders(strategyId,symbol):
    val = StrategyWiseTradeInfo.get(str(strategyId)+"_"+symbol+"MAXORDERS",1)
    #print("sid:"+str(strategyId)+" sym:"+symbol+" val:"+str(val))
    return val
def getSl(strategyId,symbol):
    if(strategyId==4):
        strategyId=2
    elif(strategyId==5):
        strategyId=3
    val = StrategyWiseTradeInfo.get(str(strategyId)+"_"+symbol+"MAXLOSSPERLOT",25)
    return val
def getTgt(strategyId,symbol):
    if(strategyId==4):
        strategyId=2
    elif(strategyId==5):
        strategyId=3
    val = StrategyWiseTradeInfo.get(str(strategyId)+"_"+symbol+"MAXPROFITPERLOT",30)
    return val
def getEQSl(strategyId):
    if(strategyId==4):
        strategyId=2
    elif(strategyId==5):
        strategyId=3
    val = StrategyWiseTradeInfo.get(str(strategyId)+"_"+"EQ"+"MAXLOSSPERTRADE",0.0001)
    return val
def getEQTgt(strategyId):
    if(strategyId==4):
        strategyId=2
    elif(strategyId==5):
        strategyId=3
    val = StrategyWiseTradeInfo.get(str(strategyId)+"_"+"EQ"+"MAXPROFITPERTRADE",0.01)
    #print("sid:"+str(strategyId)+" val:"+str(val))
    return val
