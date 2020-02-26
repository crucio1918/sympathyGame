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
import time

playerdict = {}   #playerID(user_id)とPlayerインスタンスの紐付け

playerIDs_SO = []   #ShuffleされたplayerIDs

playerIDs_DO =[]    #参加順のplayerIDs

actedNum = 0    #status中で行動を終えたプレイヤーの数

themes1 = ['a','b','c','d','e']

themes2 = ['f','g','h','i','j']

status = 'suspend'

class Player():
  def __init__(self, name,):
    self.name = name
    self.answer = ''
    self.voted = False
    self.ansVote = 0    #得票数

def question(num):
        text ='お題は「%s × %s」です。'%(
          themes1[random.randint(0, len(themes1)-1)], 
          themes2[random.randint(0, len(themes2)-1)]
          )
        TextSendMessage('%sさんの番です'%playerdict{playerIDs_SO[num]}.name)
        TextSendMessage('抽選中・・・')
        time.sleep(3.0)
        TextSendMessage(text)
        global actedNum
        actedNum+=1

def createConfirm():
  confirm_temprate_message = TemplateSendMessage(
      alt_text='Confirm template',
      template=ConfirmTemplate(
          text='参加する？',
          actions=[
              PostbackAction(
                  label='postback',
                  display_text='postback text',
                  data='participate'
              ),
              MessageAction(
                  label='postback',
                  data='close'
              )
          ]
      )
  )


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
def handle_text_message(event):
  global playerdict
  global playerIDs_SO
  global playerIDs_DO
  global actedNum
  global status
  text = event.message.text
  profile = line_bot_api.get_profile(event.source.user_id)

  if text == '強制終了':
    status == 'suspend'
  else:

    if status == 'suspend':
      if text =='開始':
        playerdict = {}
        playerIDs_SO = []
        playerIDs_DO = []
        actedNum = 0
        createConfirm()
        line_bot_api.reply_message(event.reply_token,confirm_temprate_message
        )
        status = 'inviting'

    elif status == 'inviting':
      if text == '参加':
        if profile.user_id in playerIDs_SO:
          TextSendMessage('参加済み')
        else:
          playerdict{profile.user_id} = Player(profile.display_name)
          playerIDs_SO.append(profile.user_id)
      elif text == '募集締め切り':
        TextSendMessage('募集終了')
        text = '参加メンバーは以下の通り\n'
        for playerId in playerIDs_SO:
          i = 1
          text += '%d. %s/n'%(i, playerdict{playerId}.display_name)
        playerIDs_DO = playerIDs_SO
        random.shuffle(playerIDs_SO)
        question(actedNum)
        status = 'playing'

    elif status == 'playing':
      if actedNum == len(playerIDs_SO):
        TextSendMessage('回答終了。投票に移る')
        actedNum = 0
        text =''
        i = 1
        for playerID in playerIDs_SO:
          text += ('answer%d: %s\n'%(i, playerdict{playerIDs_SO}.answer))
          i+=1
        text.rstrip('\n')
        TextSendMessage(text)
        status = 'voting'
      else:
        if profile.user_id == playerIDs_SO[actedNum]:
          playerdict{profile.user_id}.answer = text
          question(actedNum)
        else:
          TextSendMessage('%sさんの番です'%playerdict{playerIDs_SO[actedNum]}.name)

    elif status == 'voting':
      if not playerdict{profile.user_id}.voted:
        vote_num = text
        if 1 <= vote_num and vote_num <= len(playerIDs_SO):
          playerdict{profile.user_id}.ansVote+=1
          playerdict{profile.user_id}.voted = True
          actedNum+=1
        else:
          TextSendMessage('answer%s is not exists'%text)
      else:
        TextSendMessage('already voted')
      if actedNum == len(playerIDs_SO):
        text = ''
        winnerIDs = []
        most = 0
        for playerID in playerIDs_DO:
          if playerdict{playerID}.ansVote == most:
            winnerIDs.append(playerID)
          elif playerdict{playerID}.ansVote > most:
            winnerIDs = [playerID]
        for winnerID in winnerIDs:
          text+= 'と%sさん'%playerdict{winnerID}.name
        text.lstrip('と')
        text+='です。'
        TextSendMessage(text)
        status = 'suspend'

  @handler.add(PostbackEvent)
  def on_postback(event):
    global status
    global playerIDs_SO
    global playerIDs_DO
    global playerdict

    if status == 'inviting':
      profile = line_bot_api.get_profile(event.source.user_id)
      reply_token = event.reply_token
      postback_msg = event.postback.data
      if postback_msg == 'participate':
        if not profile.user_id in playerIDs_SO:
          playerdict{profile.user_id} = Player(profile.display_name)
          playerIDs_SO.append(profile.user_id)
      elif postback_msg == 'close':
        TextSendMessage('募集終了')
        text = '参加メンバーは以下の通り\n'
        for playerId in playerIDs_SO:
          i = 1
          text += '%d. %s/n'%(i, playerdict{playerId}.display_name)
        playerIDs_DO = playerIDs_SO
        random.shuffle(playerIDs_SO)
        question(actedNum)
        status = 'playing'

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)