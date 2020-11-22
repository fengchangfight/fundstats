# -*- coding:utf-8 -*-

# this program only gives selling suggestion, to actually finish selling, there are other manual works like sell and marking as complete

import pandas as pd
import datetime
from datetime import date
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from prettytable import *
import re
from termcolor import colored

trade_file='/Users/xiefengchang/life/fund_trade.xlsx'
#test_trade_file='/Users/xiefengchang/life/fund_trade_test.xlsx'

def formatDate(dt):
    format = "%Y-%m-%d";
    return dt.strftime(format)

def generateRealCodeFromIntCode(intCode):
    ret = str(int(intCode))
    if(len(ret)==6):
        return ret
    else:
        leadingZeros = '0'* (6-len(ret))
        return str(leadingZeros+ret)

# if today is weekend , return last Friday, otherwise get today 
def normalizeDate(dt):
    year, week_num, day_of_week = dt.isocalendar()
    if(day_of_week==6):
        return dt - datetime.timedelta(days=1)
    elif(day_of_week==7):
        return dt - datetime.timedelta(days=2)
    else:
        return dt

def getDataOneDate4Code(code, dt):
    # print("处理日期和股票:{0},{1}".format(datestr, code))
    url = "https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code="+code+"&sdate="+formatDate(dt+datetime.timedelta(days=-1))+"&edate="+formatDate(dt)
    # print(url)
    requests.DEFAULT_RETRIES = 500
    s = requests.session()
    s.keep_alive = False
    retry = Retry(connect=10, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    try:
        # print("debug========={0}".format(url))
        rsp = s.get(url, timeout=5);
    except requests.exceptions.Timeout as err: 
        print(err)
        time.sleep(1)
        # print("debug===retry======{0}".format(url))
        rsp = s.get(url, timeout=5);
    # sleep some sec/min and retry here!
    onedayfunddata = BeautifulSoup(rsp.text, 'html.parser')
    tab = onedayfunddata.findAll('tbody')[0]
    netvalue = '0.0'
    # print("debug=======reach tang")
    # print(tab)
    for tr in tab.findAll('tr'):
        if tr.findAll('td') and len((tr.findAll('td'))) == 7:
            netvalue = str(tr.select('td:nth-of-type(2)')[0].getText().strip())
            break
    return netvalue

def printSellInfo(codestr, name, buydate, price2sell, reason):
    print("Sell this fund {0}({1}) for {2}, due to the reason {3}".format(name, codestr, price2sell, reason))

def calcSellPrice(buyTotal, buyDatePrice, currentPrice):
    return buyTotal*(currentPrice/buyDatePrice)

if __name__ == "__main__":
    excel_data_df = pd.read_excel(trade_file, sheet_name='Sheet1')
    df = pd.DataFrame(excel_data_df, columns= ['代码','名称','买入总价','买入日期','是否完结','止盈目标','止损目标'])

    for index, row in df.iterrows():
        code = row['代码']
        name = row['名称']
        zhiying = row['止盈目标']
        zhisun = row['止损目标']
        if row['是否完结']==1:
            continue
        normalizedCurrentDate = normalizeDate(date.today())
        buyDate = row['买入日期']
        delta = (normalizedCurrentDate - buyDate.date()).days
        priceOfCurrentDate = float(getDataOneDate4Code(generateRealCodeFromIntCode(code), normalizedCurrentDate))
        priceOfBuyDate = float(getDataOneDate4Code(generateRealCodeFromIntCode(code), normalizeDate(buyDate.date())))
        
        changeRate = (priceOfCurrentDate-priceOfBuyDate)/priceOfBuyDate
        
        color='white'
        if(priceOfCurrentDate>priceOfBuyDate):
            color='red'
        elif(priceOfCurrentDate<priceOfBuyDate):
            color='green'
        print(colored("基本信息: 代码:{0}, 名称:{1}, 买入日期:{2},买入总价:{3},当前日期:{4}， 买入价: {5}, 当前价: {6}, 涨跌幅:{7}".format(generateRealCodeFromIntCode(code), name, formatDate(buyDate), row['买入总价'] , formatDate(normalizedCurrentDate), priceOfBuyDate, priceOfCurrentDate, "{0:.1%}".format(changeRate)),color))        
        if(delta>=365):
            printSellInfo(generateRealCodeFromIntCode(code),row['名称'],row['买入日期'], calcSellPrice(row['买入总价'], priceOfBuyDate, priceOfCurrentDate),"超过一年了，赶紧买！！！")
            continue
        
        if((priceOfCurrentDate-priceOfBuyDate)/priceOfBuyDate>zhiying):
            printSellInfo(generateRealCodeFromIntCode(code),row['名称'],row['买入日期'], calcSellPrice(row['买入总价'], priceOfBuyDate, priceOfCurrentDate),"赚了超过{0}了，赶紧止盈!!!".format(zhiying))
            continue

        if((priceOfCurrentDate-priceOfBuyDate)/priceOfBuyDate<zhisun):
            printSellInfo(generateRealCodeFromIntCode(code),row['名称'],row['买入日期'], calcSellPrice(row['买入总价'], priceOfBuyDate, priceOfCurrentDate),"跌破{0}了，赶紧止损!!!".format(zhisun))
        
    
    
