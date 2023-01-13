# import libraries and functions

from flask import Flask, request, abort, redirect

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, FlexSendMessage
)
import os
from dotenv import load_dotenv
import functions.fmsg, functions.intersects
import json
import time
from pytz import timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# load env file to get private tokens
load_dotenv()

# LINE API
# channel access token can be obtained via Messaging API
ch_token = os.getenv("CHANNEL_ACCESS_TOKEN")
# channel secret can be obtained via Messaging API
ch_secret = os.getenv("CHANNEL_SECRET")

sheets_name = os.getenv("SHEETS_NAME")

# load tokens
line_bot_api = LineBotApi(ch_token)
handler = WebhookHandler(ch_secret)

# set template folder (html files) and static folder (css/js files)
app = Flask(__name__, template_folder='templateFiles', static_folder='staticFiles')

tz = timezone('Asia/Bangkok')

# Set up the credentials for the API client
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('keys/googleSheets/creds.json', scope)
client = gspread.authorize(credentials)

# Open the spreadsheet
spreadsheet = client.open(sheets_name)

gc = gspread.authorize(credentials)
sh = gc.open(sheets_name)


# set the default website page
@app.route('/')
@app.route('/index')
def index():
    return redirect("https://lin.ee/ulsoFXm")


# Check data ของผู้เข้าร่วมงาน
@app.route("/qrcheckdata", methods=['POST'])
def qrcheckdata():
    # get request body as text
    body = request.get_data(as_text=True)
    body = json.loads(body)
    eventName = body["eventName"]
    ticketToken = body["ticketToken"]

    # รับค่าจาก JSON
    event_name = eventName
    ticket_token = ticketToken

    worksheet = sh.worksheet(event_name)

    row = worksheet.find(ticket_token).row

    # Get name and school of customer
    name = worksheet.cell(row, 1).value + " " + worksheet.cell(row, 2).value
    school = worksheet.cell(row, 5).value
    customer_info = {"name": name, "school": school}

    return customer_info


# Check-in ผู้เข้าร่วมงาน
@app.route("/qrcheckin", methods=['POST'])
def qrcheckin():
    try:
        # get request body as text
        body = request.get_data(as_text=True)
        body = json.loads(body)
        eventName = body["eventName"]
        ticketToken = body["ticketToken"]

        # รับค่าจาก JSON
        event_name = eventName
        ticket_token = ticketToken

        worksheet = sh.worksheet(event_name)

        row = worksheet.find(ticket_token).row
        # Fill the row with green color
        worksheet.format("{}:{}".format(row, row), {
            "backgroundColor": {
                "red": 0.0,
                "green": 1.0,
                "blue": 0.0
            }})
    except:
        abort(400)

    return "OK"


# set the callback page for webhook
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# LINE OA
@app.route("/@lineoa")
def lineoa():
    return redirect("https://lin.ee/ulsoFXm")


# PDF
@app.route("/pdfth")
def pdfth():
    return redirect("https://bccscholar.com/staticFiles/pdf/BCC_Scholar_2023_TH.pdf")


# check message
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # ตั๋วของคุณ
    if (event.message.text == "ตั๋วของฉัน"):
        if (os.path.exists('data/{}.json'.format(event.source.user_id))):
            with open('data/{}.json'.format(event.source.user_id), 'r', encoding="utf8") as user:
                userData = json.load(user)
                if len(userData["events"]) == 0:
                    flex = functions.fmsg.warningFlex(
                        "ท่านไม่ได้สมัครกิจกรรม")
                    replyObj = FlexSendMessage(alt_text='ท่านไม่ได้สมัครกิจกรรม', contents=flex)
                else:
                    for events in userData["events"]:
                        eventName = events
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(userData["events"][events]["startTime"] + 25200))
                        with open('data/events.json', 'r', encoding="utf8") as eventD:
                            eventData = json.load(eventD)
                            place = eventData[events]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(
                            userData["events"][events]["ticketToken"])
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)
                        line_bot_api.push_message(event.source.user_id,
                                                  FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
        else:
            flex = functions.fmsg.warningFlex(
                "ท่านไม่ได้สมัครกิจกรรม")
            replyObj = FlexSendMessage(alt_text='ท่านไม่ได้สมัครกิจกรรม', contents=flex)

    # send the reply message
    line_bot_api.reply_message(event.reply_token, replyObj)


# start the website
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=443, ssl_context=("keys/ssl/cert.pem", "keys/ssl/key.key"))
