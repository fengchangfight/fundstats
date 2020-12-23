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

trade_file = '/root/funddata/fund_trade.xlsx'
# test_trade_file='/Users/xiefengchang/life/fund_trade_test.xlsx'
out_file = "/mnt/fcnotes//funddecision.html"


def formatDate(dt):
    format = "%Y-%m-%d"
    return dt.strftime(format)


def generateRealCodeFromIntCode(intCode):
    ret = str(int(intCode))
    if(len(ret) == 6):
        return ret
    else:
        leadingZeros = '0' * (6-len(ret))
        return str(leadingZeros+ret)

# if today is weekend , return last Friday, otherwise get today


def normalizeDate(dt):
    year, week_num, day_of_week = dt.isocalendar()
    if(day_of_week == 6):
        return dt - datetime.timedelta(days=1)
    elif(day_of_week == 7):
        return dt - datetime.timedelta(days=2)
    else:
        return dt


def getDataOneDate4Code(code, dt):
    # print("处理日期和股票:{0},{1}".format(datestr, code))
    url = "https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code="+code + \
        "&sdate="+formatDate(dt+datetime.timedelta(days=-1)
                             )+"&edate="+formatDate(dt)
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
        rsp = s.get(url, timeout=5)
    except requests.exceptions.Timeout as err:
        print(err)
        time.sleep(1)
        # print("debug===retry======{0}".format(url))
        rsp = s.get(url, timeout=5)
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
    f.write("Sell this fund {0}({1}) for {2}, due to the reason {3}".format(
        name.encode("utf8"), codestr, price2sell, reason)+"\n".encode("gbk"))


if __name__ == "__main__":
    excel_data_df = pd.read_excel(
        trade_file, sheet_name='Sheet1', encoding='utf8')
    df = pd.DataFrame(excel_data_df, columns=[
                      u'代码', u'名称', u'买入总价', u'买入日期', u'是否完结', u'止盈目标', u'止损目标', u'投资周期', u'分红累加', u'分红份额'])

    f = open(out_file, "w")
    f.write("更新日期：{0}\n".format(datetime.date.today()))
    for index, row in df.iterrows():
        code = row[u'代码']
        name = row[u'名称']
        zhiying = row[u'止盈目标']
        zhisun = row[u'止损目标']
        touzizhouqi = row[u'投资周期']
        if row[u'是否完结'] == 1:
            continue
        normalizedCurrentDate = normalizeDate(date.today())
        buyDate = row[u'买入日期']
        delta = (normalizedCurrentDate - buyDate.date()).days
        priceOfCurrentDate = float(getDataOneDate4Code(
            generateRealCodeFromIntCode(code), normalizedCurrentDate))
        priceOfBuyDate = float(getDataOneDate4Code(
            generateRealCodeFromIntCode(code), normalizeDate(buyDate.date())))

        changeRate = (priceOfCurrentDate-priceOfBuyDate)/priceOfBuyDate

        row_template = "<p style=\"color:{0}\">{1}</p>"
        color = 'black'
        if(priceOfCurrentDate > priceOfBuyDate):
            color = 'red'
        elif(priceOfCurrentDate < priceOfBuyDate):
            color = 'green'
        rowdata = (row_template.format(color, "基本信息: 代码:{0}, 名称:{1}, 买入日期:{2},买入总价:{3},当前日期:{4}， 买入价: {5}, 当前价: {6}, 涨跌幅:{7}".format(generateRealCodeFromIntCode(
            code), name.encode("utf8"), formatDate(buyDate), row[u'买入总价'], formatDate(normalizedCurrentDate), priceOfBuyDate, priceOfCurrentDate, "{0:.1%}".format(changeRate)))+"\n")
        f.write(rowdata)

        shijimairuzongjia = row[u'买入总价']*0.9995
        mairufene = shijimairuzongjia/priceOfBuyDate
        zongfene = row[u'分红份额']+mairufene
        dangqianzongjia = priceOfCurrentDate*zongfene+row[u'分红累加']

        if(delta >= touzizhouqi):
            printSellInfo(generateRealCodeFromIntCode(
                code), row[u'名称'], row[u'买入日期'], zongfene*priceOfCurrentDate, "超过投资周期{0}天了，赶紧卖！！！".format(touzizhouqi))
            continue

        if((dangqianzongjia-shijimairuzongjia)/shijimairuzongjia > zhiying):
            printSellInfo(generateRealCodeFromIntCode(
                code), row[u'名称'], row[u'买入日期'], zongfene*priceOfCurrentDate, "赚了超过{0}了，赶紧止盈!!!".format(str(zhiying)))
            continue

        if((dangqianzongjia-shijimairuzongjia)/shijimairuzongjia < zhisun):
            printSellInfo(generateRealCodeFromIntCode(
                code), row[u'名称'], row[u'买入日期'], zongfene*priceOfCurrentDate, "跌破{0}了，赶紧止损!!!".format(str(zhisun)))

    f.close()
