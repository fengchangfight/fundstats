# -*- coding:utf-8 -*-
import pandas as pd
import math
from datetime import date

def formatDate(dt):
    format = "%Y-%m-%d";
    return dt.strftime(format)

todayStr = formatDate(date.today())

input = "/root/funddata/funddata_"+todayStr+".csv"
output = "/root/funddata/funddata_"+todayStr+"_recommend_1year_crazy.csv"
blacklistfile = "/root/funddata/blacklist.txt"
blacklist =  set(open(blacklistfile).read().split())
def zhangfu(num1, num2):
    return (num2-num1)/num1

if __name__ == "__main__":
    iter_csv = pd.read_csv(input, encoding='gbk', iterator=True, chunksize=1000)
    df = pd.concat([chunk[(zhangfu(chunk[u'一年前净值'],chunk[u'当前净值'])>1)] for chunk in iter_csv])
    boolean_series = ~df[u'代码'].isin(blacklist)
    filtered_df = df[boolean_series]
    filtered_df.to_csv(output, encoding='utf-8-sig', index=False)
