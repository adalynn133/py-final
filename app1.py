from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

from linebot.models import *
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import csv
import googlemaps


#======這裡是呼叫的檔案內容=====
from message import *
from new import *
from Function import *
#======這裡是呼叫的檔案內容=====

#======python的函數庫==========
import tempfile, os
import datetime
import time
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi('HX0LHrZ4D9bnlbWRmem+ftHEeHaVLmUBnxIUcMQOHZliV1zRjcIXcIncRF+p5bevd2Y8m6Vll5HfansF+YAWYC+sAJ5TFbm4qb9pGwqc+zd6OnAmgHmQzfNnv2fWVIbSpJ1XrcifzoHDasOjUFDu7QdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('b775c751858b39e2a6721376c3d8a095')
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

flex_message = FlexSendMessage(
        alt_text= '請選擇搜尋類別',
        contents={"type": "bubble","hero": {"type": "image","size": "full","aspectRatio": "20:13","aspectMode": "cover","action": {"type": "uri","uri": "https://line.me/"},"position": "absolute","url": "https://www.freepik.com/search?format=search&img=1&last_filter=img&last_value=1&query=Car&type=icon"},"footer": {"type": "box","layout": "vertical","spacing": "sm","contents": [{"type": "button","style": "link","height": "sm","action": {"type": "message","label": "加油站","text": "加油站"}},{"type": "button","style": "link","height": "sm","action": {"type": "message","label": "停車場","text": "停車場"}}],"flex": 0}}
)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg == "停車場" or "加油站":
        @handler.add(MessageEvent, message=LocationMessage)
        def handle_location(event):
            my_lat = event.message.latitude
            my_lon = event.message.longitude
            location = {}
            location.update({'lat': my_lat, 'lng': my_lon})
            places_result = gmaps.places_nearby(location, keyword= msg, radius=1000)
            i = 0
            for place in places_result['results']:
                if i < 5:
                    re = place['name'],place['vicinity']
                    line_bot_api.reply_message(event.reply_token, re)
                    i += 1
                else:
                    break

@handler.add(MessageEvent, message=LocationMessage)
def handle_location2(event):
    my_lat = event.message.latitude
    my_lon = event.message.longitude
    location = {}
    location.update({'lat': my_lat, 'lng': my_lon})
    line_bot_api.reply_message(event.reply_token, "請輸入搜尋類別")
    flex_message = FlexSendMessage(
        alt_text= '請選擇搜尋類別',
        contents={
  "type": "bubble",
  "hero": {
    "type": "image",
    "size": "full",
    "aspectRatio": "20:13",
    "aspectMode": "cover",
    "action": {
      "type": "uri",
      "uri": "https://line.me/"
    },
    "position": "absolute",
    "url": "https://www.freepik.com/search?format=search&img=1&last_filter=img&last_value=1&query=Car&type=icon"
  },
  "footer": {
    "type": "box",
    "layout": "vertical",
    "spacing": "sm",
    "contents": [
      {
        "type": "button",
        "style": "link",
        "height": "sm",
        "action": {
          "type": "message",
          "label": "加油站",
          "text": "加油站"
        }
      },
      {
        "type": "button",
        "style": "link",
        "height": "sm",
        "action": {
          "type": "message",
          "label": "停車場",
          "text": "停車場"
        }
      }
    ],
    "flex": 0
  }
}
    )
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message2(event):
        msg = event.message.text
        places_result = gmaps.places_nearby(location, keyword= msg, radius=1000)
        i = 0
        for place in places_result['results']:
            if i < 5:
                re = place['name'],place['vicinity']
                line_bot_api.reply_message(event.reply_token, re)
                i += 1
            else:
                break
    



@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text='您的副駕駛已經上線～～～')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
