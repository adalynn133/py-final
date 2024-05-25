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
                QuickReplyButton(action=MessageAction(label="超商", text="超商"))

            ])
        )
    line_bot_api.reply_message(event.reply_token, flex_message)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global search_keyword  
    search_keyword = event.message.text
    if search_keyword == "使用說明":
        how_to_use = '您的副駕駛已經上線～\n使用說明：\n一、傳貼圖以快速點選加油站、停車場等位置查詢，或是輸入想查詢的附近位置關鍵字。\n二、跟隨指示導入現在位置。\n三、獲得查詢下前三近的地點資訊。\n四、點入欲前往的地點以使用googlemaps導航前往。'
        message = TextSendMessage(text=how_to_use)
        line_bot_api.reply_message(event.reply_token, message)
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
