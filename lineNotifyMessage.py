

# 程式運行前 需先開啟ngork.exe
# 1.輸入ngrok http (你的Port ex:5000)
# 2.再將Forwarding 網址貼入 Line Developer 的 URL網址並獲取認證成功 (若失敗請先執行此python)
# 3.即可運行本端lineNofifyMessage.py程式

#  == == == == == == == == == == == == ==測試專區 == == == == == == == == == == == ==
# # 匯入requests套件
# import requests

# # 指定取得日期
# dateStr = "20220928"

# # 爬取股價資訊
# requestData = requests.get(
#     'https://mis.twse.com.tw/stock/fibest.jsp?goback=1&stock=00878')
# stockInfo = requestData.text.split('\n')
# # 顯示取得股價資訊
# print(requestData.text)
# == == == == == == == == == == == == ==爬蟲資訊並傳回LineFunction == == == == == == == == == == == ==

from __future__ import unicode_literals
import requests
import json
import pandas as pd
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import configparser
import random
import datetime
import sys
import numpy as np
from datetime import datetime

app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))


# 獲取天氣資訊
def GetWeather():

    url = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": "CWB-A1647FD7-D138-4A02-9DA3-DCBEE061E938",
        "locationName": "臺中市",
    }

    response = requests.get(url, params=params)
    print(response.status_code)

    if response.status_code == 200:
        # print(response.text)
        data = json.loads(response.text)

        location = data["records"]["location"][0]["locationName"]

        weather_elements = data["records"]["location"][0]["weatherElement"]
        start_time = weather_elements[0]["time"][0]["startTime"]
        end_time = weather_elements[0]["time"][0]["endTime"]
        weather_state = weather_elements[0]["time"][0]["parameter"]["parameterName"]
        rain_prob = weather_elements[1]["time"][0]["parameter"]["parameterName"]
        min_tem = weather_elements[2]["time"][0]["parameter"]["parameterName"]
        comfort = weather_elements[3]["time"][0]["parameter"]["parameterName"]
        max_tem = weather_elements[4]["time"][0]["parameter"]["parameterName"]

        # print(location)
        # print(start_time)
        # print(end_time)
        # print(weather_state)
        # print(rain_prob)
        # print(min_tem)
        # print(comfort)
        # print(max_tem)

        wheaterData = "地區:"+location + "\n" + start_time + "\n" + end_time + "\n" + "天氣狀況:" + weather_state + \
            "\n" + "降雨機率:"+rain_prob+"\n" + "最低溫:" + \
            min_tem + "\n" + "最高溫:" + max_tem+"\n" + "體感:" + comfort
        return wheaterData
        print(wheaterData)
    else:
        print("Can't get data!")


# 獲取股票資訊
def Get_StockPrice(Symbol, Date):

    url = f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={Date}&stockNo={Symbol}'

    data = requests.get(url).text
    # print(data)
    json_data = json.loads(data)

    Stock_data = json_data['data']

    StockPrice = pd.DataFrame(Stock_data, columns=[
                              'Date', 'Volume', 'Volume_Cash', 'Open', 'High', 'Low', 'Close', 'Change', 'Order'])

    StockPrice['日期'] = StockPrice['Date'].str.replace(
        '/', '').astype(int) + 19110000
    StockPrice['日期'] = pd.to_datetime(StockPrice['日期'].astype(str))
    StockPrice['Volume'] = StockPrice['Volume'].str.replace(
        ',', '').astype(float)/1000
    StockPrice['Volume_Cash'] = StockPrice['Volume_Cash'].str.replace(
        ',', '').astype(float)
    StockPrice['Order'] = StockPrice['Order'].str.replace(
        ',', '').astype(float)

    StockPrice['Open'] = StockPrice['Open'].str.replace(',', '').astype(float)
    StockPrice['High'] = StockPrice['High'].str.replace(',', '').astype(float)
    StockPrice['Low'] = StockPrice['Low'].str.replace(',', '').astype(float)
    StockPrice['Close'] = StockPrice['Close'].str.replace(
        ',', '').astype(float)

    StockPrice = StockPrice.set_index('日期', drop=True)

    StockPrice = StockPrice[['Open', 'High', 'Low', 'Close', 'Volume']]

    filter = StockPrice['Open']

    GetMyStockInfo = filter.to_json()

    # GetMyStockInfo = GetMyStockInfo.replace('{', '')

    GetMyStockInfo = json.dumps(StockPrice)
    # GetMyStockInfo = GetMyStockInfo.replace(',', '\n')
    # GetMyStockInfo = GetMyStockInfo.replace('\"', '')
    # GetMyStockInfo = GetMyStockInfo.replace('\Open\:', '')

    return GetMyStockInfo


# if __name__ == "__main__":
#     data = Get_StockPrice('00878', '20230311')
#     print(data)
#     app.run()

    # if __name__ == '__main__':

    # 接收 LINE 的資訊


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # print(body, signature)
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def prettyEcho(event):

    sendString = ""
    if "股票資訊" in event.message.text:
        # sendString = GetStockInfo()
        # sendString = "不可愛"
        print(sendString)
    elif "天氣如何呢?" in event.message.text:
        # type(get_data())
        sendString = GetWeather()

    else:
        sendString = event.message.text

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=sendString)

    )

# 回傳股價資訊


def GetStockInfo():
    GetDate = datetime.now()

    TodayDay = GetDate.day
    TodayMonth = GetDate.month
    TodayYears = GetDate.year
    if TodayMonth < 10:
        TodayMonth = "0"+str(TodayMonth)

    TotalDate = str(TodayYears)+str(TodayMonth)+str(TodayDay)
    data = Get_StockPrice('00878', TotalDate)

    print(data)

    return data


if __name__ == "__main__":
    app.run()
