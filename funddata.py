# -*- coding:utf-8 -*-


import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from prettytable import *
import re
from datetime import date
import datetime
import json
import pandas as pd
import csv

#  注意，周末是拿不到基金净值数据的，所以日期要normalize到工作日
def formatDate(dt):
    format = "%Y-%m-%d";
    return dt.strftime(format)

todayStr = formatDate(date.today())
rootPath = "/root"
outfile = rootPath+"/"+todayStr+".csv"

def get_url(url, params=None, proxies=None):
    rsp = requests.get(url, params=params, proxies=proxies)
    #rsp.raise_for_status()
    if(rsp.status_code!=200):
        return -1
    else:
        return rsp.text

def getNameByCode(code):
    print("===getting name of code: {0}".format(code))
    url = 'http://fundgz.1234567.com.cn/js/'+code+'.js'
    resp = get_url(url)
    if(resp==-1):
        return -1
    m = re.search('"name":"(.+?)",', resp)
    found = None
    if m:
        found = m.group(1)
    if(not found):
        return -1
    print("name:{0}".format(found))
    return found
    
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
    url = "https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code="+code+"&sdate="+formatDate(dt+datetime.timedelta(days=-1))+"&edate="+formatDate(dt)
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
    netvalue = ''
    # print("debug=======reach tang")
    for tr in tab.findAll('tr'):
        if tr.findAll('td') and len((tr.findAll('td'))) == 7:
            netvalue = str(tr.select('td:nth-of-type(2)')[0].getText().strip())
            break
    return netvalue

# input: code
# output: 
# code, name, 
# today nav, 
# one year ago nav, 
# 2 year ago nav, 
# 3 year ago nav, 
# increase percentage by 1 year, 
# increase percentage by 2 year, 
# increase percentage by 3 year, 
# increase percentage by 4 year
# 获取基金名api: http://fundgz.1234567.com.cn/js/001186.js?rt=1463558676006
# 获取所有基金列表api: http://fund.eastmoney.com/js/fundcode_search.js
# 从基金获取其某日净值api: https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code=003511&sdate=2018-02-22&edate=2018-02-22
def getonefund(code, fh):
    # get name by code
    name = getNameByCode(code)
    if(name==-1):
        print("Cannot get name of {0}".format(code))
        return
    # print("debug====reach 1")
    # generate 4 dates, for each date, call data api for it, and get back 8 data
    today = normalizeDate(date.today())
    oneYearAgo = normalizeDate(date.today() - datetime.timedelta(days=1*365))
    twoYearAgo = normalizeDate(date.today() - datetime.timedelta(days=2*365))
    threeYearAgo = normalizeDate(date.today() - datetime.timedelta(days=3*365))
    fourYearAgo = normalizeDate(date.today() - datetime.timedelta(days=4*365))
    # print("debug====reach 2")

    todayNetValue = getDataOneDate4Code(code, today)
    # print("debug====reach 2.1")
    oneYearAgoNetValue = getDataOneDate4Code(code, oneYearAgo)
    # print("debug====reach 2.2")
    twoYearAgoNetValue = getDataOneDate4Code(code, twoYearAgo)
    # print("debug====reach 2.3")
    threeYearAgoNetValue = getDataOneDate4Code(code, threeYearAgo)
    # print("debug====reach 2.4")
    fourYearAgoNetValue = getDataOneDate4Code(code, fourYearAgo)
    # print("debug====reach 3")

    oneYearIncrease = 0.0
    twoYearIncrease = 0.0
    threeYearIncrease = 0.0 
    fourYearIncrease = 0.0

    if(not todayNetValue):
        print("No data for today, maybe this fund is unavailable")
        return 

    if oneYearAgoNetValue:
        oneYearIncrease = (float(todayNetValue)-float(oneYearAgoNetValue))/float(oneYearAgoNetValue)

    if twoYearAgoNetValue:
        twoYearIncrease = (float(todayNetValue)-float(twoYearAgoNetValue))/float(twoYearAgoNetValue)

    if threeYearAgoNetValue:
        threeYearIncrease = (float(todayNetValue)-float(threeYearAgoNetValue))/float(threeYearAgoNetValue)

    if fourYearAgoNetValue:
        fourYearIncrease = (float(todayNetValue)-float(fourYearAgoNetValue))/float(fourYearAgoNetValue)
    # print("debug====reach 4")

    # print("=====basic info======")
    # print("Code is: {0}".format(code))
    # print("Name is: {0}".format(name))
    # print("======net value=======")
    # print("Today net value: {0}".format(todayNetValue))
    # if oneYearAgoNetValue:
    #     print("One year ago net value: {0}".format(oneYearAgoNetValue))
    # if twoYearAgoNetValue:
    #     print("Two year ago net value: {0}".format(twoYearAgoNetValue))
    # if threeYearAgoNetValue:
    #     print("Three year ago net value: {0}".format(threeYearAgoNetValue))
    # if fourYearAgoNetValue:
    #     print("Four year ago net value: {0}".format(fourYearAgoNetValue))
    # print("========增长率========")
    # if oneYearAgoNetValue:
    #     print("One year increase:{0}".format(str(float(oneYearIncrease)*100)+'%'))
    # if twoYearAgoNetValue:
    #     print("two year increase:{0}".format(str(float(twoYearIncrease)*100)+'%'))
    # if threeYearAgoNetValue:
    #     print("three year increase:{0}".format(str(float(threeYearIncrease)*100)+'%'))
    # if fourYearAgoNetValue:
    #     print("four year increase:{0}".format(str(float(fourYearIncrease)*100)+'%'))

    print("======appending===={0}===".format(code))    
    appendlisttocsvfile(fh, [code, name, todayNetValue, oneYearAgoNetValue, "{0:.0%}".format(oneYearIncrease), twoYearAgoNetValue, "{0:.0%}".format(twoYearIncrease), threeYearAgoNetValue, "{0:.0%}".format(threeYearIncrease), fourYearAgoNetValue, "{0:.0%}".format(fourYearIncrease)])
    print("====append finish==={0}=".format(code))
   

def getallfund():
    # get all codes
    # loop through these codes, for each code, get it's name and data, append the record data to csv separated by column
    r = requests.get('http://fund.eastmoney.com/js/fundcode_search.js')
    cont = re.findall('var r = (.*])', r.text)[0]
    # print(cont)
    ls = json.loads(cont)  # 将字符串个事的list转化为list格式
    all_fundCode = pd.DataFrame(ls, columns=['基金代码', '基金名称缩写', '基金名称', '基金类型', '基金名称拼音'])  # list转为DataFrame
    codeList = all_fundCode['基金代码'].tolist()
    return codeList

def appendlisttocsvfile(fh, li):
    employee_writer = csv.writer(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)    
    employee_writer.writerow(li)    

def testSingle(code):
    name = getNameByCode(code)
    if(name==-1):
        print("Cannot get name of {0}".format(code))
        return
    # generate 4 dates, for each date, call data api for it, and get back 8 data
    today = normalizeDate(date.today())
    oneYearAgo = normalizeDate(date.today() - datetime.timedelta(days=1*365))
    twoYearAgo = normalizeDate(date.today() - datetime.timedelta(days=2*365))
    threeYearAgo = normalizeDate(date.today() - datetime.timedelta(days=3*365))
    fourYearAgo = normalizeDate(date.today() - datetime.timedelta(days=4*365))
    print("today: {0}, one year ago: {1}, two year ago:{2}, three year ago:{3},  four year ago:{4}".format(today, oneYearAgo, twoYearAgo, threeYearAgo, fourYearAgo))
    todayNetValue = getDataOneDate4Code(code, today)
    oneYearAgoNetValue = getDataOneDate4Code(code, oneYearAgo)
    twoYearAgoNetValue = getDataOneDate4Code(code, twoYearAgo)
    threeYearAgoNetValue = getDataOneDate4Code(code, threeYearAgo)
    fourYearAgoNetValue = getDataOneDate4Code(code, fourYearAgo)
    print("today nv: {0}, one year ago nv: {1}, two year ago nv:{2}, three year ago nv:{3},  four year ago nv:{4}".format(todayNetValue, oneYearAgoNetValue, twoYearAgoNetValue, threeYearAgoNetValue, fourYearAgoNetValue))

def getAll():
    codelist = getallfund()
    print("Overall number of code: {0}".format(len(codelist)))
    with open(outfile, mode='w',encoding='utf-8-sig') as fh:
        # add header
        appendlisttocsvfile(fh, ["代码","名称","当前净值","一年前净值", "一年增长率", "两年前净值", "两年增长率", "三年前净值", "三年增长率", "四年前净值", "四年增长率"])
        for code in codelist:
          getonefund(code, fh)
        print("======finish all {0} code========".format(len(codelist)))

if __name__ == "__main__":
    testSingle("501050")
    # getAll()
        
    
