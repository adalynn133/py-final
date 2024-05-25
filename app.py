from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
#======python的函數庫==========
import tempfile, os
import datetime
import googlemaps
import time
import traceback
#======python的函數庫==========

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
        flex_message = TextSendMessage(text='請導入您的位置',
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=LocationAction(label="位置"))
                               ]))
        line_bot_api.reply_message(event.reply_token, flex_message)
        try:
            
    else:
        sendback = TextSendMessage(text='請重新輸入')
        line_bot_api.reply_message(event.reply_token, sendback)
        
    
 def handle_location_message(event):
    latitude = event.message.latitude
    longitude = event.message.longitude

    reply_text = f"Your location is (Lat: {latitude}, Long: {longitude})"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )    
    
        

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text='您的線上副駕駛已經上線～～')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    app.run()
