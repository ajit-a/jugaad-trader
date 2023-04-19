set -x

source env/bin/activate
trap kill_pids 1 2 3 6 9

kill_pids()
{
  for index in ${!pids[*]}
  do
	  kill -9 ${pids[$index]}
  done
}
pids=()

sudo service httpd start
HOUR=`date --date="-${BACK} day 5 hour 30 min" +%H`
MINS=`date --date="-${BACK} day 5 hour 30 min" +%M`

if [ x$1 = "x" ]
then
	echo "Running jugaad, no access token required"
	#exit
fi
#python3 OMS_passive_bulk.py $1 $API_SECRET $API_KEY > oms.log 2> oms.err &
pids+=($!)

#while [ $HOUR -lt 9 ]
#do
#        sleep 60
#	HOUR=`date --date="-${BACK} day 5 hour 30 min" +%H`
#done
#MINS=`date --date="-${BACK} day 5 hour 30 min" +%M`
#while [ $MINS -le 10 ]
#do
#        sleep 10
#        MINS=`date --date="-${BACK} day 5 hour 30 min" +%M`
#done

rm -f idx1.txt
python3 indices_download.py idx1.txt
awk -F'"' -v OFS='' '{ for (i=2; i<=NF; i+=2) gsub(",", "", $i) } 1' idx1.txt > idx.txt
BNF_CLOSING=`egrep -w "NIFTY BANK" idx.txt|cut -d, -f7|sed s/,//g|cut -d. -f1`
NIFTY_CLOSING=`egrep -w "NIFTY 50" idx.txt|cut -d, -f7|sed s/,//g|cut -d. -f1`
#BNF_CLOSING=`mysql -h ${MS_HOST} -u root -pamit -P${MS_PORT}  -s -N -e "select round(closing_index_value) from tradeanalysis.eodindexrate where index_name=\"Nifty Bank\" order by index_date desc limit 1;"`
#NIFTY_CLOSING=`mysql -h ${MS_HOST} -u root -pamit -P${MS_PORT}  -s -N -e "select round(closing_index_value) from tradeanalysis.eodindexrate where index_name=\"Nifty 50\" order by index_date desc limit 1;"`

BNF_STRIKES="'"
BNF_CLOSING=`expr $BNF_CLOSING / 100`
BNF_CLOSING=`expr $BNF_CLOSING \\* 100`
i=20
while [ $i -ge 0 ]
do
	j=`expr 100 \\* $i`
	val=`expr $BNF_CLOSING - $j`
	BNF_STRIKES=${BNF_STRIKES}${val}"|"
	val=`expr $BNF_CLOSING + $j`
	BNF_STRIKES=${BNF_STRIKES}${val}"|"
	i=`expr $i - 1`
done
BNF_STRIKES=${BNF_STRIKES::-1}
BNF_STRIKES=$BNF_STRIKES"'"
NIFTY_STRIKES="'"
NIFTY_CLOSING=`expr $NIFTY_CLOSING / 100`
NIFTY_CLOSING=`expr $NIFTY_CLOSING \\* 100`
i=15
while [ $i -ge 0 ]
do
	j=`expr 50 \\* $i`
	val=`expr $NIFTY_CLOSING - $j`
	NIFTY_STRIKES=${NIFTY_STRIKES}${val}"|"
	val=`expr $NIFTY_CLOSING + $j`
	NIFTY_STRIKES=${NIFTY_STRIKES}${val}"|"
	i=`expr $i - 1`
done
NIFTY_STRIKES=${NIFTY_STRIKES::-1}
NIFTY_STRIKES=$NIFTY_STRIKES"'"

MS_HOST=127.0.0.1
MS_PORT=3306
DATA_HOST=127.0.0.1
TODAY=`date  --date="0 day" +%Y-%m-%d`
LWD=`mysql -h ${MS_HOST} -u root -pajit -P${MS_PORT} -s -N -e  "select tradeanalysis.getLastWorkingDate(\"${TODAY}\",1)"`
if [ $? -ne 0 ]
then
	LWD=`date  --date="-1 day" +%Y-%m-%d`
fi

D1=`date +%Y%m%d`
D2=`echo $LWD | sed s/-//g`
CD1=`echo $D1 | awk -f convertdate.awk`
CD2=`echo $D2 | awk -f convertdate.awk`

BACK=`expr $CD1 - $CD2`
BACK=`expr $BACK / 86400`
TODAY=`date  --date="-${BACK} day" +%Y-%m-%d`
OTODAY=`date  --date="0 day" +%Y-%m-%d`
WMONTH=`date --date="-${BACK} day" +%b |tr [:lower:] [:upper:]`
MONTH=`date --date="-${BACK} day" +%m`
DATE=`date --date="-${BACK} day" +%d`
YEAR=`date --date="-${BACK} day" +%Y`

REF="--referer https://archives.nseindia.com/products/content/equities/equities/homepage_eq.htm"
AGENT="--user-agent=\"Mozilla/5.0\""
FILE1=cm${DATE}${WMONTH}${YEAR}bhav.csv
FILE2=fo${DATE}${WMONTH}${YEAR}bhav.csv
FILE3=MTO_${DATE}${MONTH}${YEAR}.DAT
FILE4=ind_close_all_${DATE}${MONTH}${YEAR}.csv


STATUS=1
while [ $STATUS -ne 0 ]
do
  wget -c ${REF} ${AGENT} https://archives.nseindia.com/content/historical/EQUITIES/${YEAR}/${WMONTH}/${FILE1}.zip
  STATUS=$?
  sleep 1
done
STATUS=1
while [ $STATUS -ne 0 ]
do
  wget -c ${REF} ${AGENT} https://archives.nseindia.com/content/indices/${FILE4}
  STATUS=$?
  sleep 1
done
unzip ${FILE1}.zip
unzip ${FILE4}.zip
egrep ",EQ," ${FILE1} | cut -d',' -f1,6  > close.csv
sed -i '1d' ${FILE4}
cut -d',' -f1,6 ${FILE4} |tr '[:lower:]' '[:upper:]' >> close.csv
egrep ",EQ," ${FILE1} | cut -d',' -f1,4,5  > high.csv
cut -d',' -f1,4,5 ${FILE4} |tr '[:lower:]' '[:upper:]' >> high.csv
egrep ",EQ," ${FILE1} | awk -F"," '{sum[$1]=($4+$5+$6)/3} END{for (i in sum) print i","sum[i]}' > cpr.csv
cut -d',' -f1,4,5,6 ${FILE4} | awk -F"," '{sum[$1]=($2+$3+$4)/3} END{for (i in sum) print i","sum[i]}' >> cpr.csv
egrep ",EQ," ${FILE1} | awk -F"," '{sumPivot[$1]=($4+$5+$6)/3;sumBC[$1]=($4+$5)/2;sumTC[$1]=((($4+$5+$6)/3) - (($4+$5)/2)) + sumPivot[$1]} END{for (i in sumBC) print (sumBC[i]>sumTC[i])?i","sumBC[i]:i","sumTC[i]}' > TC.csv
cut -d',' -f1,4,5,6 ${FILE4} | awk -F"," '{sumPivot[$1]=($2+$3+$4)/3;sumBC[$1]=($2+$3)/2;sumTC[$1]=((($2+$3+$4)/3) - (($3+$4)/2)) + sumPivot[$1]} END{for (i in sumBC) print (sumBC[i]>sumTC[i])?i","sumBC[i]:i","sumTC[i]}' >> TC.csv
egrep ",EQ," ${FILE1} | awk -F"," '{sumPivot[$1]=($4+$5+$6)/3;sumBC[$1]=($4+$5)/2;sumTC[$1]=((($4+$5+$6)/3) - (($4+$5)/2)) + sumPivot[$1]} END{for (i in sumBC) print (sumBC[i]<sumTC[i])?i","sumBC[i]:i","sumTC[i]}' > BC.csv
cut -d',' -f1,4,5,6 ${FILE4} | awk -F"," '{sumPivot[$1]=($2+$3+$4)/3;sumBC[$1]=($2+$3)/2;sumTC[$1]=((($2+$3+$4)/3) - (($3+$4)/2)) + sumPivot[$1]} END{for (i in sumBC) print (sumBC[i]<sumTC[i])?i","sumBC[i]:i","sumTC[i]}' >> BC.csv
rm -f ${FILE1}
rm -f ${FILE4}
rm -f ${FILE1}.zip
getWMonth()
{
	M=$1
	case $M in
		1)
		echo "JAN"
		;;
		2)
		echo "FEB"
		;;
		3)
		echo "MAR"
		;;
		4)
		echo "APR"
		;;
		5)
		echo "MAY"
		;;
		6)
		echo "JUN"
		;;
		7)
		echo "JUL"
		;;
		8)
		echo "AUG"
		;;
		9)
		echo "SEP"
		;;
		O)
		echo "OCT"
		;;
		N)
		echo "NOV"
		;;
		D)
		echo "DEC"
		;;
		*)
		echo "ERROR"
		;;
	esac
}


if [ `date  +%a` = "Thu" ]
then
	YY=`date +%Y|cut -b3-`
	M=`date  +%m`
	DD=`date +%d`
else
#BANKNIFTY<YY><M><DD>strike<PE/CE>
	YY=`date -d "next thursday" +%Y|cut -b3-`
	M=`date -d "next thursday" +%m`
	DD=`date -d "next thursday" +%d`
fi

case $M in
	01)
		M="1"
		;;
	02)
		M="2"
		;;
	03)
		M="3"
		;;
	04)
		M="4"
		;;
	05)
		M="5"
		;;
	06)
		M="6"
		;;
	07)
		M="7"
		;;
	08)
		M="8"
		;;
	09)
		M="9"
		;;
	10)
		M="O"
		;;
	11)
		M="N"
		;;
	12)
		M="D"
		;;
esac


if test -s instruments.xml
then
FDATE=`stat --format=%w instruments.xml|cut -d' ' -f1`
if [ $FDATE != $OTODAY ]
then
curl "https://api.kite.trade/instruments" \
    -H "X-Kite-Version: 3" \
  -H "Authorization: token api_key:access_token" > instruments.xml
sed -i '1d' instruments.xml
fi
else
curl "https://api.kite.trade/instruments" \
    -H "X-Kite-Version: 3" \
  -H "Authorization: token api_key:access_token" > instruments.xml
sed -i '1d' instruments.xml
fi
cp OptionsEQ.csv OptionsEQ.csv_bkp
BNF_FILTER="BANKNIFTY${YY}${M}${DD}"
status=0
egrep ${BNF_FILTER} instruments.xml |egrep $BNF_STRIKES > OptionsEQ.csv 
status=$?
if [ $status -ne 0 ]
then
	DD=`date -d "next wednesday" +%d`
	BNF_FILTER="BANKNIFTY${YY}${M}${DD}"
	egrep ${BNF_FILTER} instruments.xml |egrep $BNF_STRIKES > OptionsEQ.csv 
	status=$?
fi
if [ $status -ne 0 ]
then
	DD=`date -d "next tuesday" +%d`
	BNF_FILTER="BANKNIFTY${YY}${M}${DD}"
	egrep ${BNF_FILTER} instruments.xml |egrep $BNF_STRIKES > OptionsEQ.csv 
	status=$?
fi
if [ $status -ne 0 ]
then
	wM=$(getWMonth ${M})
	BNF_FILTER="BANKNIFTY${YY}${wM}"
	egrep ${BNF_FILTER} instruments.xml |egrep $BNF_STRIKES > OptionsEQ.csv 
	status=$?
fi
NIFTY_FILTER="NIFTY${YY}${M}${DD}"
status=0
egrep ${NIFTY_FILTER} instruments.xml |egrep -v 'FINNIFTY|BANK'  |egrep $NIFTY_STRIKES >> OptionsEQ.csv 
status=$?
if [ $status -ne 0 ]
then
	DD=`date -d "next wednesday" +%d`
	NIFTY_FILTER="NIFTY${YY}${M}${DD}"
	egrep ${NIFTY_FILTER} instruments.xml |egrep -v 'FINNIFTY|BANK'|egrep $NIFTY_STRIKES >> OptionsEQ.csv 
	status=$?
fi
if [ $status -ne 0 ]
then
	DD=`date -d "next tuesday" +%d`
	NIFTY_FILTER="NIFTY${YY}${M}${DD}"
	egrep ${NIFTY_FILTER} instruments.xml |egrep -v 'FINNIFTY|BANK'|egrep $NIFTY_STRIKES >> OptionsEQ.csv 
	status=$?
fi
if [ $status -ne 0 ]
then
	wM=$(getWMonth ${M})
	NIFTY_FILTER="NIFTY${YY}${wM}"
	egrep ${NIFTY_FILTER} instruments.xml |egrep -v 'FINNIFTY|BANK'|egrep $NIFTY_STRIKES >> OptionsEQ.csv 
	status=$?
fi
egrep "INDICES" instruments.xml |grep "NSE" >> OptionsEQ.csv

rm -f symbols.txt
wget http://${DATA_HOST}/symbols.txt
mv symbols.txt symbols1.txt
egrep -v " " symbols1.txt > symbols.txt
SSYMBOLS=`cat symbols.txt|tr '\n' '|'`
SYMBOLS=${SSYMBOLS::-1}
egrep ",NSE" instruments.xml|grep "EQ"|egrep -w ${SYMBOLS} |egrep -v '\-BE|\-BZ|\-D2|\-E1|\-GB|\-GS|\-IT|\-IV|\-M1|\-N1|\-N2|\-N3|\-N4|\-N5|\-N6|\-N7|\-N8|\-N9|\-NA|\-NAV|\-NB|\-NC|\-ND|\-NE|\-NF|\-NG|\-NH|\-NI|\-NJ|\-NK|\-NL|\-NM|\-NN|\-NO|\-NP|\-NQ|\-NR|\-NS|\-NT|\-NU|\-NV|\-NW|\-NX|\-NY|\-NZ|\-P1|\-P2|\-RE|\-RR|\-SG|\-SM|\-SZ|\-TB|\-TEK|\-W1|\-W3|\-X1|\-Y1|\-Y2|\-Y3|\-Y4|\-Y5|\-Y6|\-Y7|\-Y8|\-Y9|\-YA|\-YB|\-YC|\-YG|\-YH|\-YI|\-YJ|\-YK|\-YL|\-YM|\-YN|\-YO|\-YP|\-YQ|\-YR|\-YS|\-YT|\-YU|\-YV|\-YW|\-YX|\-YY|\-YZ|\-Z1|\-Z2|\-Z3|\-Z4|\-Z5|\-Z6|\-Z7|\-Z8|\-Z9|\-ZA|\-ZB|\-ZC|\-ZD|\-ZE|\-ZF|\-ZG|\-ZH|\-ZI|\-ZJ|\-ZK' >> OptionsEQ.csv

if [ $status -ne 0 ]
then
	#Basically default formulated pattern is invalid
	egrep "NFO-FUT" instruments.xml |egrep ${wM} >> OptionsEQ.csv
fi

#cut -d, -f1 OptionsEQ.csv > bnf_instruments
egrep "NIFTY" OptionsEQ.csv | cut -d, -f1 > bnf_instruments
px=`egrep "NIFTY BANK" idx.txt|cut -d, -f2|sed s/,//g`
cg=`egrep "NIFTY BANK" idx.txt|cut -d, -f3|sed s/,//g`
#cg=`expr 100 \\* $cg`
if [ $(echo "$cg < 0" | bc) -eq 0 ]
#if [ $cg -gt 0 ]
then
	cg="UP"
else
	cg="DOWN"
fi
nfpx=`egrep -w "NIFTY 50" idx.txt|cut -d, -f2|sed s/,//g`
nfcg=`egrep -w "NIFTY 50" idx.txt|cut -d, -f3|sed s/,//g`
#nfcg=`expr 100 \\* $nfcg`
if [ $(echo "$nfcg < 0" | bc) -eq 0 ]
#if [ $nfcg -gt 0 ]
then
	nfcg="UP"
else
	nfcg="DOWN"
fi
#python3 OMS_passive.py $1 $px $cg $nfpx $nfcg > oms.log 2> oms.err &
echo $px,$cg,$nfpx,$nfcg > ltp_direction.txt
tkn_count=`wc -l bnf_instruments|cut -d' ' -f1`
if [ $tkn_count -eq 0 ]
then
	./stop.sh
	echo "Empty token files...Exiting"
fi
python3 OMS_passive_bulk.py $1 $API_SECRET $API_KEY > oms.log 2> oms.err &
python3 AutoTraderLTP.py bnf_instruments $API_KEY > ltp.log &
pids+=($!)
