from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, VideoSendMessage, StickerSendMessage
)
import os
app = Flask(__name__)
#環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
import random

def myIndex(l, x):
    if x in l:
        return l.index(x)
    else:
        return -1

hands = ["グー","チョキ","パー"]

def hands_to_int(userhand):
    return myIndex(hands, userhand)

def select_bothand():
    return random.randint(0, 2)

def judge(userhand, bothand):
    if userhand == -1:
        message = "グー、チョキ、パーをカタカナで入力してね"

    else:
        #0:あいこ　1:botの勝ち　2:userの勝ち
        status = (userhand - bothand + 3) % 3
        message = "botは" + hands[bothand] + "でふ\n"

        if status == 0:
            message += "あいこだよーん"
        elif status == 1:
            message += "あなたのか...負けダヨーン"
        elif status == 2:
            message += "あなたの勝ち\nたまたまだね"

    return message

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = judge(hands_to_int(event.message.text), select_bothand())
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)