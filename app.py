from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import tempfile, os
import datetime
import googlemaps
import time
import traceback

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
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg == "停車場" or msg == "加油站":
        flex_message = TextSendMessage(
            text='請導入您的位置',
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=LocationAction(label="位置"))
            ])
        )
        line_bot_api.reply_message(event.reply_token, flex_message)
    else:
        sendback = TextSendMessage(text='請重新輸入')
        line_bot_api.reply_message(event.reply_token, sendback)

@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    location = {}
    location.update({'lat': latitude, 'lng': longitude})
    places_result = gmaps.places_nearby(location, type = 'gas_station', radius=500)
    if len(places_result) < 5:
        for place in places_result['results']:
            loc = place['icon']
            line_bot_api.reply_message(event.reply_token, loc)
    else:
        i = 0
        for place in places_result['results']:
            if i < 5:
                loc = str(place['icon'])
                line_bot_api.reply_message(event.reply_token, loc)
                i += 1
            else:
                break
                
            
            

@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text='您的線上副駕駛已經上線～～')
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run()
