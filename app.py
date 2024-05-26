from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import tempfile, os
import datetime
import googlemaps
import time
import traceback
import json
import os
import requests
import pandas as pd
from datetime import datetime

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
gmaps = googlemaps.Client(key='AIzaSyDMLx-tmT9oiAb20Phg0SDdSZzJCWpi7Bw')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    sticker_message = StickerSendMessage(
        package_id=event.message.package_id,
        sticker_id=event.message.sticker_id
    )
    flex_message = TextSendMessage(
            text='快速查詢～',
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="停車場", text="停車場")),
                QuickReplyButton(action=MessageAction(label="加油站", text="加油站")),
                QuickReplyButton(action=MessageAction(label="超商", text="超商")),
                QuickReplyButton(action=MessageAction(label="服務區休息站", text="服務區休息站"))
            ])
        )
    line_bot_api.reply_message(event.reply_token, flex_message)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global search_keyword  
    search_keyword = event.message.text
    if search_keyword == "使用說明":
        how_to_use = '使用說明：\n一、傳貼圖以快速點選加油站、停車場等位置查詢，或是輸入想查詢的附近位置關鍵字。\n二、跟隨指示導入現在位置。\n三、獲得查詢下前三近的地點資訊。\n四、點入欲前往的地點以使用googlemaps導航前往。'
        message = TextSendMessage(text=how_to_use)
        line_bot_api.reply_message(event.reply_token, message)
    elif search_keyword == "服務區" or search_keyword == "休息站" or search_keyword == "服務區休息站":
        flex_message = TextSendMessage(
            text='請輸入北上或南下資訊',
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="北上國1", text="北上國1")),
                QuickReplyButton(action=MessageAction(label="南下國1", text="南下國1")),
                QuickReplyButton(action=MessageAction(label="北上國3", text="北上國3")),
                QuickReplyButton(action=MessageAction(label="南下國3", text="南下國3")),
                QuickReplyButton(action=MessageAction(label="國5", text="國5"))
            ])
        )
        line_bot_api.reply_message(event.reply_token, flex_message)
    else:
        flex_message = TextSendMessage(
            text='請導入您的位置',
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=LocationAction(label="位置"))
            ])
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    location = {'lat': latitude, 'lng': longitude}
    dis = []
    drtime = []
    origin = (latitude,longitude)
    ns = ''
    plmessages = []
    if search_keyword == "北上國1" or search_keyword == "南下國1":
        df = pd.read_csv('國1.csv')
        filtered_df = df[df['北上1/南下2/雙向3'] == 3 ]
        if search_keyword == "北上國1":
            filtered_df2 = df[df['北上1/南下2/雙向3'] == 1 ]
            ns = '1位置'
        else:
            filtered_df2 = df[df['北上1/南下2/雙向3'] == 2 ]
            ns = '2位置'
        result_df = pd.concat([filtered_df, filtered_df2], axis=0)
        result_df['距離'] = None
        result_df['行車時間'] = None
        for value in result_df[ns]:
            loc = value.split(',')
            wish_loc = (loc[0],loc[1])
            now = datetime.now()
            distance_matrix_result = gmaps.distance_matrix(origins=[origin],
                                               destinations=[wish_loc],
                                               mode="driving",
                                               departure_time=now)   
            if distance_matrix_result['rows']:
                elements = distance_matrix_result['rows'][0]['elements'][0]
                if elements['status'] == 'OK':
                    distance = elements['distance']['text']
                    duration = elements['duration']['text']
                else:
                    distance = None
                    duration = None
            else:
                distance = None
                duration = None
            dis.append(distance)
            drtime.append(duration)
        result_df['距離'] = dis
        result_df['行車時間'] = drtime
        result_df['距離'] = result_df['距離'].str.replace(r'[a-zA-Z]', '', regex=True)
        result_df['距離'] = pd.to_numeric(result_df['距離'])
        result_df_sorted = result_df.sort_values(by='距離')
        df_reset = result_df_sorted.reset_index(drop=True)
        for i in range(3):
            place_name = df_reset['名稱'][i]
            place_dis = df_reset['距離'][i]
            str_loc = str(df_reset['1位置'][i])
            place_loc = str_loc.split(',')
            place_lat = place_loc[0]
            place_lng = place_loc[1]
            maps_url = f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}"
            if float(place_lat) >= float(latitude):
                place_ns = '北'
            else:
                place_ns = '南'
            place_drtime = df_reset['行車時間'][i]
            place_message = TextSendMessage(
                        text=f"{place_ns}\n名稱: {place_name}\n行車時間：{place_drtime}\n地圖: {maps_url}"
                    )
            plmessages.append(place_message)
        line_bot_api.reply_message(event.reply_token, plmessages)
   
    elif search_keyword == "北上國3" or search_keyword == "南下國3":
        df = pd.read_csv('國3.csv')
        filtered_df = df[df['北上1/南下2/雙向3'] == 3 ]
        if search_keyword == "北上國3":
            filtered_df2 = df[df['北上1/南下2/雙向3'] == 1 ]
            ns = '1位置'
        else:
            filtered_df2 = df[df['北上1/南下2/雙向3'] == 2 ]
            ns = '2位置'
        result_df = pd.concat([filtered_df, filtered_df2], axis=0)
        result_df['距離'] = None
        result_df['行車時間'] = None
        for value in result_df[ns]:
            loc = value.split(',')
            wish_loc = (loc[0],loc[1])
            now = datetime.now()
            distance_matrix_result = gmaps.distance_matrix(origins=[origin],
                                               destinations=[wish_loc],
                                               mode="driving",
                                               departure_time=now)   
            if distance_matrix_result['rows']:
                elements = distance_matrix_result['rows'][0]['elements'][0]
                if elements['status'] == 'OK':
                    distance = elements['distance']['text']
                    duration = elements['duration']['text']
                else:
                    distance = None
                    duration = None
            else:
                distance = None
                duration = None
            dis.append(distance)
            drtime.append(duration)
        result_df['距離'] = dis
        result_df['行車時間'] = drtime
        result_df['距離'] = result_df['距離'].str.replace(r'[a-zA-Z]', '', regex=True)
        result_df['距離'] = pd.to_numeric(result_df['距離'])
        result_df_sorted = result_df.sort_values(by='距離')
        df_reset = result_df_sorted.reset_index(drop=True)
        for i in range(3):
            place_name = df_reset['名稱'][i]
            place_dis = df_reset['距離'][i]
            str_loc = str(df_reset['1位置'][i])
            place_loc = str_loc.split(',')
            place_lat = place_loc[0]
            place_lng = place_loc[1]
            maps_url = f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}"
            if float(place_lat) >= float(latitude):
                place_ns = '北'
            else:
                place_ns = '南'
            place_drtime = df_reset['行車時間'][i]
            place_message = TextSendMessage(
                        text=f"{place_ns}\n名稱: {place_name}\n行車時間：{place_drtime}\n地圖: {maps_url}"
                    )
            plmessages.append(place_message)
        line_bot_api.reply_message(event.reply_token, plmessages)
    elif search_keyword == "國5":
        df = pd.read_csv('國5.csv')
        result_df = df[df['北上1/南下2/雙向3'] == 3 ]
        result_df['距離'] = None
        result_df['行車時間'] = None
        for value in result_df['1位置']:
            loc = value.split(',')
            wish_loc = (loc[0],loc[1])
            now = datetime.now()
            distance_matrix_result = gmaps.distance_matrix(origins=[origin],
                                               destinations=[wish_loc],
                                               mode="driving",
                                               departure_time=now)   
            if distance_matrix_result['rows']:
                elements = distance_matrix_result['rows'][0]['elements'][0]
                if elements['status'] == 'OK':
                    distance = elements['distance']['text']
                    duration = elements['duration']['text']
                else:
                    distance = None
                    duration = None
            else:
                distance = None
                duration = None
            dis.append(distance)
            drtime.append(duration)
        result_df['距離'] = dis
        result_df['行車時間'] = drtime
        result_df['距離'] = result_df['距離'].str.replace(r'[a-zA-Z]', '', regex=True)
        result_df['距離'] = pd.to_numeric(result_df['距離'])
        result_df_sorted = result_df.sort_values(by='距離')
        df_reset = result_df_sorted.reset_index(drop=True)
        for i in range(2):
            place_name = df_reset['名稱'][i]
            place_dis = df_reset['距離'][i]
            str_loc = str(df_reset['1位置'][i])
            place_loc = str_loc.split(',')
            place_lat = place_loc[0]
            place_lng = place_loc[1]
            maps_url = f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}"
            if float(place_lat) >= float(latitude):
                place_ns = '北'
            else:
                place_ns = '南'
            place_drtime = df_reset['行車時間'][i]
            place_message = TextSendMessage(
                        text=f"{place_ns}\n名稱: {place_name}\n行車時間：{place_drtime}\n地圖: {maps_url}"
                    )
            plmessages.append(place_message)
        line_bot_api.reply_message(event.reply_token, plmessages)
    else:
        try:
            places_result = gmaps.places_nearby(location, keyword=search_keyword, radius=500)
            if 'results' in places_result and places_result['results']:
                messages = []
                for place in places_result['results'][:3]:
                    place_name = place['name']
                    place_address = place.get('vicinity', 'No address provided')
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}"
                    score = place['user_ratings_total']
                    location_message = TextSendMessage(
                        text=f"{place_name}\n地址: {place_address}\n評分：{score}\n地圖: {maps_url}"
                    )
                    messages.append(location_message)
                line_bot_api.reply_message(event.reply_token, messages)
            else:
                error_text = TextSendMessage(text='500公尺內沒有目標地點')
                line_bot_api.reply_message(event.reply_token, error_text)
        except Exception as e:
            app.logger.error(f"Error: {str(e)}")
            error_text = TextSendMessage(text='發生錯誤，請稍後再試')
            line_bot_api.reply_message(event.reply_token, error_text)

@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    welcome_msg = '您的副駕駛已經上線～\n使用說明：\n一、傳貼圖以快速點選加油站、停車場等位置查詢，或是輸入想查詢的附近位置關鍵字。\n二、跟隨指示導入現在位置。\n三、獲得查詢下前三近的地點資訊。\n四、點入欲前往的地點以使用googlemaps導航前往。'
    message = TextSendMessage(text = welcome_msg)
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run()
