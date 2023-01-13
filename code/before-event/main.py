"""
Status:
0 = Student
1 = Teacher
2 = Parent

Degree:
0 = Primary School
1 = Middle School
2 = High School
"""

# import libraries and functions
from flask import Flask, request, abort, render_template, redirect

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
)
import os
from dotenv import load_dotenv
import functions.fmsg, functions.intersects
import requests
import secrets
import qrcode
from PIL import Image
import json
import urllib.parse
import time
from datetime import timezone, timedelta
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

# load tokens
line_bot_api = LineBotApi(ch_token)
handler = WebhookHandler(ch_secret)

sheets_name = os.getenv("SHEETS_NAME")

# set template folder (html files) and static folder (css/js files)
app = Flask(__name__, template_folder='templateFiles', static_folder='staticFiles')

tz = timezone('Asia/Bangkok')

# Set up the credentials for the API client
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('keys/googleSheets/creds.json', scope)
client = gspread.authorize(credentials)

# Open the spreadsheet and get the first worksheet
spreadsheet = client.open(sheets_name)

gc = gspread.authorize(credentials)
sh = gc.open(sheets_name)


# set the default website page
@app.route('/')
@app.route('/index')
def index():
    return redirect("https://lin.ee/ulsoFXm")


# set the register website page
@app.route("/register_thai.html")
def register_thai():
    # return the html file
    return render_template('register_thai.html')


# set the register website page
@app.route("/register_en.html")
def register_en():
    # return the html file
    return render_template('register_eng.html')


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


# set the callback page for webhook
@app.route("/richmenu", methods=['POST'])
def richmenu():
    # get request body as text
    body = request.get_data(as_text=True).replace("+", " ")

    # handle webhook body
    data = body.split("&")
    with open("data/template.json", "r", encoding="utf8") as t:
        jdata = json.load(t)
        jdata["firstName"] = urllib.parse.unquote(data[0].split("first name=", 1)[1])
        jdata["lastName"] = urllib.parse.unquote(data[1].split("last name=", 1)[1])
        jdata["phone"] = urllib.parse.unquote(data[2].split("phone=", 1)[1])
        jdata["email"] = urllib.parse.unquote(data[3].split("email=", 1)[1])
        jdata["school"] = urllib.parse.unquote(data[6].split("school=", 1)[1])
        jdata["status"] = urllib.parse.unquote(data[4].split("job=", 1)[1])
        jdata["degree"] = urllib.parse.unquote(data[5].split("degree=", 1)[1])
        jdata["events"] = {}
        line_bot_api.link_rich_menu_to_user(data[7].split("userid=", 1)[1], "richmenu-ca71354ad09efcd9b250ee0b8a77e1e6")
        with open("data/" + data[7].split("userid=", 1)[1] + ".json", "w", encoding="utf-8") as outfile:
            outfile.write(str(jdata).replace("'", '"'))
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
    # Primary
    if (event.message.text == "เลือกกิจกรรมระดับประถมศึกษา"):
        flex = functions.fmsg.primarySectionListFlex()
        replyObj = FlexSendMessage(alt_text='รายชื่อฝ่ายระดับประถมศึกษา', contents=flex)

    # Open House
    elif (event.message.text == "Open House ประถมศึกษา"):
        flex = functions.fmsg.primaryOpenHouse()
        replyObj = FlexSendMessage(alt_text='Open House ประถมศึกษา', contents=flex)

    # Open House 8:00
    elif (event.message.text == "Open House ประถมศึกษา รอบ 8:00 น."):
        flex = functions.fmsg.primaryOpenHouse8()
        replyObj = FlexSendMessage(alt_text='Open House ประถมศึกษา รอบ 8:00 น.', contents=flex)

    # Open House 8:00
    elif (event.message.text == "ลงสมัคร Primary Open House รอบ 8:00 น."):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Primary Open House รอบ 08:00 น."]["count"] >= 50:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Primary Open House รอบ 08:00 น.", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Primary Open House รอบ 08:00 น."]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Primary Open House รอบ 08:00 น.": eventData["Primary Open House รอบ 08:00 น."]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Primary Open House รอบ 08:00 น."].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Primary Open House รอบ 08:00 น."
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(
                                                 eventData["Primary Open House รอบ 08:00 น."]["startTime"] + 25200))
                        place = eventData["Primary Open House รอบ 08:00 น."]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)
                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

                        events = "Primary Open House รอบ 08:00 น."
                        worksheet = spreadsheet.worksheet("Primary Open House รอบ 08.00 น.")
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"], data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)


    # Open House 12:00
    elif (event.message.text == "Open House ประถมศึกษา รอบ 12:00 น."):
        flex = functions.fmsg.primaryOpenHouse12()
        replyObj = FlexSendMessage(alt_text='Open House ประถมศึกษา รอบ 12:00 น.', contents=flex)

    # ลงสมัคร Primary Open House รอบ 12:00 น.
    elif (event.message.text == "ลงสมัคร Primary Open House รอบ 12:00 น."):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Primary Open House รอบ 12:00 น."]["count"] >= 50:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Primary Open House รอบ 12:00 น.", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Primary Open House รอบ 12:00 น."]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Primary Open House รอบ 12:00 น.": eventData["Primary Open House รอบ 12:00 น."]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Primary Open House รอบ 12:00 น."].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Primary Open House รอบ 12:00 น."
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(
                                                 eventData["Primary Open House รอบ 12:00 น."]["startTime"] + 25200))
                        place = eventData["Primary Open House รอบ 12:00 น."]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)
                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

                        events = "Primary Open House รอบ 12:00 น."
                        worksheet = spreadsheet.worksheet("Primary Open House รอบ 12.00 น.")
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"], data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)



    # Scholar Quiz
    elif (event.message.text == "Scholar Quiz"):
        flex = functions.fmsg.scholarQuiz()
        replyObj = FlexSendMessage(alt_text='Scholar Quiz', contents=flex)

    # ลงสมัคร Scholar Quiz (การแข่งขันทางวิชาการ)
    elif (event.message.text == "ลงสมัคร Scholar Quiz (การแข่งขันทางวิชาการ)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                userData = json.load(user)
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if (userData["status"] == "0" and userData["degree"] == "0"):
                        if functions.intersects.intersects("Scholar Quiz วิชาการ", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            flex = functions.fmsg.teamOptionFlex("Scholar Quiz วิชาการ")
                            replyObj = FlexSendMessage(alt_text='ทีม', contents=flex)
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # สร้างทีมใหม่ Scholar Quiz วิชาการ
    elif (event.message.text == "สร้างทีมใหม่ Scholar Quiz วิชาการ"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                userData = json.load(user)
                if (userData["school"] in eventData["Scholar Quiz วิชาการ"]["school"]):
                    if eventData["Scholar Quiz วิชาการ"]["school"][userData["school"]] >= 2:
                        flex = functions.fmsg.warningFlex("จำนวนผู้สมัครของ{}เต็มแล้ว".format(userData["school"]))
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                            userData = json.load(user)
                            if (userData["status"] == "0" and userData["degree"] == "0"):
                                if functions.intersects.intersects("Scholar Quiz วิชาการ", event.source.user_id):
                                    flex = functions.fmsg.warningFlex(
                                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                else:
                                    with open("data/events.json", "w", encoding="utf-8") as eventD:
                                        eventData["Scholar Quiz วิชาการ"]["school"][userData["school"]] += 1
                                        eventD.write(str(eventData).replace("'", '"'))
                                    teamToken = secrets.token_hex(2)
                                    while (os.path.exists("teams/{}.json".format(teamToken))):
                                        teamToken = secrets.token_hex(2)
                                    with open("teams/template.json", "r", encoding="utf-8") as teamT:
                                        teamData = json.load(teamT)
                                        teamData["eventName"] = "Scholar Quiz วิชาการ"
                                        teamData["teamId"] = teamToken
                                        teamData["school"] = userData["school"]
                                        x = {event.source.user_id: userData["status"]}
                                        teamData["members"].update(x)
                                        with open("teams/{}.json".format(teamToken), "w", encoding="utf-8") as team:
                                            team.write(str(teamData).replace("'", '"'))
                                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                                            eventData["Scholar Quiz วิชาการ"]["count"] += 1
                                            eventD.write(str(eventData).replace("'", '"'))
                                        token = secrets.token_hex(16)
                                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                            token = secrets.token_hex(16)
                                        img = qrcode.make(token)
                                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                                        with open("data/" + event.source.user_id + ".json", "w",
                                                  encoding="utf-8") as user:
                                            new_data = {"Scholar Quiz วิชาการ": eventData["Scholar Quiz วิชาการ"]}
                                            userData["events"].update(new_data)
                                            new_data = {"ticketToken": token}
                                            userData["events"]["Scholar Quiz วิชาการ"].update(new_data)
                                            new_data = {"teamToken": teamToken}
                                            userData["events"]["Scholar Quiz วิชาการ"].update(new_data)
                                            user.write(str(userData).replace("'", '"'))
                                        eventName = "Scholar Quiz วิชาการ"
                                        firstName = userData["firstName"]
                                        lastName = userData["lastName"]
                                        school = userData["school"]
                                        when = time.strftime("%d/%m/%Y %H:%M",
                                                             time.localtime(
                                                                 eventData["Scholar Quiz วิชาการ"][
                                                                     "startTime"] + 25200))
                                        place = eventData["Scholar Quiz วิชาการ"]["place"]
                                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                         place,
                                                                         qr)

                                        events = "Scholar Quiz วิชาการ"
                                        worksheet = spreadsheet.worksheet(events)
                                        data = userData
                                        if data["status"] == "0":
                                            status = "นักเรียน"
                                        elif data["status"] == "1":
                                            status = "ครู"
                                        elif data["status"] == "2":
                                            status = "ผู้ปกครอง"

                                        if data["degree"] == "0":
                                            degree = "ประถม"
                                        elif data["degree"] == "1":
                                            degree = "ม.ต้น"
                                        elif data["degree"] == "2":
                                            degree = "ม.ปลาย"
                                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                               data["school"],
                                               status, degree, data["events"][events]["ticketToken"],
                                               data["events"][events]["teamToken"]]
                                        worksheet.append_row(row)

                                        replyObj = []
                                        replyObj.append(FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
                                        creator = userData["firstName"]
                                        flex = functions.fmsg.team(teamToken, eventName, creator)
                                        replyObj.append(FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))

                            else:
                                flex = functions.fmsg.warningFlex(
                                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                else:
                    with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                        userData = json.load(user)
                        if (userData["status"] == "0" and userData["degree"] == "0"):
                            if functions.intersects.intersects("Scholar Quiz วิชาการ", event.source.user_id):
                                flex = functions.fmsg.warningFlex(
                                    "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                with open("data/events.json", "w", encoding="utf-8") as eventD:
                                    new_data = {userData["school"]: 1}
                                    eventData["Scholar Quiz วิชาการ"]["school"].update(new_data)
                                    eventD.write(str(eventData).replace("'", '"'))
                                teamToken = secrets.token_hex(2)
                                while (os.path.exists("teams/{}.json".format(teamToken))):
                                    teamToken = secrets.token_hex(2)
                                with open("teams/template.json", "r", encoding="utf-8") as teamT:
                                    teamData = json.load(teamT)
                                    teamData["eventName"] = "Scholar Quiz วิชาการ"
                                    teamData["teamId"] = teamToken
                                    teamData["school"] = userData["school"]
                                    x = {event.source.user_id: userData["status"]}
                                    teamData["members"].update(x)
                                    with open("teams/{}.json".format(teamToken), "w", encoding="utf-8") as team:
                                        team.write(str(teamData).replace("'", '"'))
                                    with open("data/events.json", "w", encoding="utf-8") as eventD:
                                        eventData["Scholar Quiz วิชาการ"]["count"] += 1
                                        eventD.write(str(eventData).replace("'", '"'))
                                    token = secrets.token_hex(16)
                                    while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                        token = secrets.token_hex(16)
                                    img = qrcode.make(token)
                                    img.save("staticFiles/images/qrCode/{}.png".format(token))
                                    with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                        new_data = {"Scholar Quiz วิชาการ": eventData["Scholar Quiz วิชาการ"]}
                                        userData["events"].update(new_data)
                                        new_data = {"ticketToken": token}
                                        userData["events"]["Scholar Quiz วิชาการ"].update(new_data)
                                        new_data = {"teamToken": teamToken}
                                        userData["events"]["Scholar Quiz วิชาการ"].update(new_data)
                                        user.write(str(userData).replace("'", '"'))
                                    eventName = "Scholar Quiz วิชาการ"
                                    firstName = userData["firstName"]
                                    lastName = userData["lastName"]
                                    school = userData["school"]
                                    when = time.strftime("%d/%m/%Y %H:%M",
                                                         time.localtime(
                                                             eventData["Scholar Quiz วิชาการ"]["startTime"] + 25200))
                                    place = eventData["Scholar Quiz วิชาการ"]["place"]
                                    qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                    flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                     place,
                                                                     qr)

                                    events = "Scholar Quiz วิชาการ"
                                    worksheet = spreadsheet.worksheet(events)
                                    data = userData
                                    if data["status"] == "0":
                                        status = "นักเรียน"
                                    elif data["status"] == "1":
                                        status = "ครู"
                                    elif data["status"] == "2":
                                        status = "ผู้ปกครอง"

                                    if data["degree"] == "0":
                                        degree = "ประถม"
                                    elif data["degree"] == "1":
                                        degree = "ม.ต้น"
                                    elif data["degree"] == "2":
                                        degree = "ม.ปลาย"
                                    row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                           data["school"],
                                           status, degree, data["events"][events]["ticketToken"],
                                           data["events"][events]["teamToken"]]
                                    worksheet.append_row(row)

                                    replyObj = []
                                    replyObj.append(FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
                                    creator = userData["firstName"]
                                    flex = functions.fmsg.team(teamToken, eventName, creator)
                                    replyObj.append(FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))

                        else:
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # เข้าร่วมทีมที่มีอยู่แล้ว Scholar Quiz วิชาการ
    elif (event.message.text == "เข้าร่วมทีมที่มีอยู่แล้ว Scholar Quiz วิชาการ"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                userData = json.load(user)
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if (userData["status"] == "0" and userData["degree"] == "0"):
                        if functions.intersects.intersects("Scholar Quiz วิชาการ", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            replyObj = TextSendMessage(text='กรุณาพิมพ์รหัสทีมของคุณลงแชทนี้')

                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # ลงสมัคร Scholar Quiz (การประกวดร้องเพลง)
    elif (event.message.text == "ลงสมัคร Scholar Quiz (การประกวดร้องเพลง)"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            with open("data/events.json", "r", encoding="utf-8") as eventD:
                eventData = json.load(eventD)
                if (userData["school"] in eventData["Scholar Quiz ร้องเพลง"]["school"]):
                    if (eventData["Scholar Quiz ร้องเพลง"]["school"][userData["school"]] >= 1):
                        flex = functions.fmsg.warningFlex("จำนวนผู้สมัครของ{}เต็มแล้ว".format(userData["school"]))
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        if (userData["status"] == "0" and userData["degree"] == "0"):
                            if functions.intersects.intersects("Scholar Quiz ร้องเพลง", event.source.user_id):
                                flex = functions.fmsg.warningFlex(
                                    "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                with open("data/events.json", "w", encoding="utf-8") as eventD:
                                    eventData["Scholar Quiz ร้องเพลง"]["school"][userData["school"]] += 1
                                    eventD.write(str(eventData).replace("'", '"'))
                                token = secrets.token_hex(16)
                                while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                    token = secrets.token_hex(16)
                                img = qrcode.make(token)
                                img.save("staticFiles/images/qrCode/{}.png".format(token))
                                with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                    new_data = {"Scholar Quiz ร้องเพลง": eventData["Scholar Quiz ร้องเพลง"]}
                                    userData["events"].update(new_data)
                                    new_data = {"ticketToken": token}
                                    userData["events"]["Scholar Quiz ร้องเพลง"].update(new_data)
                                    user.write(str(userData).replace("'", '"'))
                                eventName = "Scholar Quiz ร้องเพลง"
                                firstName = userData["firstName"]
                                lastName = userData["lastName"]
                                school = userData["school"]
                                when = time.strftime("%d/%m/%Y %H:%M", time.localtime(
                                    eventData["Scholar Quiz ร้องเพลง"]["startTime"] + 25200))
                                place = eventData["Scholar Quiz ร้องเพลง"]["place"]
                                qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place,
                                                                 qr)

                                events = "Scholar Quiz ร้องเพลง"
                                worksheet = spreadsheet.worksheet(events)
                                data = userData
                                if data["status"] == "0":
                                    status = "นักเรียน"
                                elif data["status"] == "1":
                                    status = "ครู"
                                elif data["status"] == "2":
                                    status = "ผู้ปกครอง"

                                if data["degree"] == "0":
                                    degree = "ประถม"
                                elif data["degree"] == "1":
                                    degree = "ม.ต้น"
                                elif data["degree"] == "2":
                                    degree = "ม.ปลาย"
                                row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                       data["school"],
                                       status, degree, data["events"][events]["ticketToken"]]
                                worksheet.append_row(row)

                                replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                        else:
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                else:
                    if (userData["status"] == "0" and userData["degree"] == "0"):
                        if functions.intersects.intersects("Scholar Quiz ร้องเพลง", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            with open("data/events.json", "w", encoding="utf-8") as eventD:
                                new_data = {userData["school"]: 1}
                                eventData["Scholar Quiz ร้องเพลง"]["school"].update(new_data)
                                eventD.write(str(eventData).replace("'", '"'))
                            token = secrets.token_hex(16)
                            while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                token = secrets.token_hex(16)
                            img = qrcode.make(token)
                            img.save("staticFiles/images/qrCode/{}.png".format(token))
                            with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                new_data = {"Scholar Quiz ร้องเพลง": eventData["Scholar Quiz ร้องเพลง"]}
                                userData["events"].update(new_data)
                                new_data = {"ticketToken": token}
                                userData["events"]["Scholar Quiz ร้องเพลง"].update(new_data)
                                user.write(str(userData).replace("'", '"'))
                            eventName = "Scholar Quiz ร้องเพลง"
                            firstName = userData["firstName"]
                            lastName = userData["lastName"]
                            school = userData["school"]
                            when = time.strftime("%d/%m/%Y, %H:%M",
                                                 time.localtime(
                                                     eventData["Scholar Quiz ร้องเพลง"]["startTime"] + 25200))
                            place = eventData["Scholar Quiz ร้องเพลง"]["place"]
                            qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                            flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                            events = "Scholar Quiz ร้องเพลง"
                            worksheet = spreadsheet.worksheet(events)
                            data = userData
                            if data["status"] == "0":
                                status = "นักเรียน"
                            elif data["status"] == "1":
                                status = "ครู"
                            elif data["status"] == "2":
                                status = "ผู้ปกครอง"

                            if data["degree"] == "0":
                                degree = "ประถม"
                            elif data["degree"] == "1":
                                degree = "ม.ต้น"
                            elif data["degree"] == "2":
                                degree = "ม.ปลาย"
                            row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                   data["school"],
                                   status, degree, data["events"][events]["ticketToken"]]
                            worksheet.append_row(row)

                            replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)


    # Go
    elif (event.message.text == "การแข่งขันหมากล้อม"):
        flex = functions.fmsg.primaryGo()
        replyObj = FlexSendMessage(alt_text='การแข่งขันหมากล้อม', contents=flex)

    # ลงสมัคร การแข่งขันหมากล้อม
    elif (event.message.text == "ลงสมัคร การแข่งขันหมากล้อม"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            if ((userData["status"] == "0" and userData["degree"] == "0") or userData["status"] == "1"):
                if functions.intersects.intersects("แข่งหมากล้อม", event.source.user_id):
                    flex = functions.fmsg.warningFlex(
                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                else:
                    flex = functions.fmsg.teamOptionFlex("แข่งหมากล้อม")
                    replyObj = FlexSendMessage(alt_text='ทีม', contents=flex)
            else:
                flex = functions.fmsg.warningFlex(
                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # สร้างทีมใหม่ แข่งหมากล้อม
    elif (event.message.text == "สร้างทีมใหม่ แข่งหมากล้อม"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                userData = json.load(user)
                if (userData["school"] in eventData["แข่งหมากล้อม"]["school"]):
                    if eventData["แข่งหมากล้อม"]["school"][userData["school"]] >= 6:
                        flex = functions.fmsg.warningFlex("จำนวนผู้สมัครของ{}เต็มแล้ว".format(userData["school"]))
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                            userData = json.load(user)
                            if ((userData["status"] == "0" and userData["degree"] == "0") or userData["status"] == "1"):
                                if functions.intersects.intersects("แข่งหมากล้อม", event.source.user_id):
                                    flex = functions.fmsg.warningFlex(
                                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                else:
                                    with open("data/events.json", "w", encoding="utf-8") as eventD:
                                        eventData["แข่งหมากล้อม"]["school"][userData["school"]] += 1
                                        eventD.write(str(eventData).replace("'", '"'))
                                    teamToken = secrets.token_hex(2)
                                    while (os.path.exists("teams/{}.json".format(teamToken))):
                                        teamToken = secrets.token_hex(2)
                                    with open("teams/template.json", "r", encoding="utf-8") as teamT:
                                        teamData = json.load(teamT)
                                        teamData["eventName"] = "แข่งหมากล้อม"
                                        teamData["teamId"] = teamToken
                                        teamData["school"] = userData["school"]
                                        x = {event.source.user_id: userData["status"]}
                                        teamData["members"].update(x)
                                        with open("teams/{}.json".format(teamToken), "w", encoding="utf-8") as team:
                                            team.write(str(teamData).replace("'", '"'))
                                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                                            eventData["แข่งหมากล้อม"]["count"] += 1
                                            eventD.write(str(eventData).replace("'", '"'))
                                        token = secrets.token_hex(16)
                                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                            token = secrets.token_hex(16)
                                        img = qrcode.make(token)
                                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                                        with open("data/" + event.source.user_id + ".json", "w",
                                                  encoding="utf-8") as user:
                                            new_data = {"แข่งหมากล้อม": eventData["แข่งหมากล้อม"]}
                                            userData["events"].update(new_data)
                                            new_data = {"ticketToken": token}
                                            userData["events"]["แข่งหมากล้อม"].update(new_data)
                                            new_data = {"teamToken": teamToken}
                                            userData["events"]["แข่งหมากล้อม"].update(new_data)
                                            user.write(str(userData).replace("'", '"'))
                                        eventName = "แข่งหมากล้อม"
                                        firstName = userData["firstName"]
                                        lastName = userData["lastName"]
                                        school = userData["school"]
                                        when = time.strftime("%d/%m/%Y %H:%M",
                                                             time.localtime(
                                                                 eventData["แข่งหมากล้อม"]["startTime"] + 25200))
                                        place = eventData["แข่งหมากล้อม"]["place"]
                                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                         place,
                                                                         qr)

                                        events = "แข่งหมากล้อม"
                                        worksheet = spreadsheet.worksheet(events)
                                        data = userData
                                        if data["status"] == "0":
                                            status = "นักเรียน"
                                        elif data["status"] == "1":
                                            status = "ครู"
                                        elif data["status"] == "2":
                                            status = "ผู้ปกครอง"

                                        if data["degree"] == "0":
                                            degree = "ประถม"
                                        elif data["degree"] == "1":
                                            degree = "ม.ต้น"
                                        elif data["degree"] == "2":
                                            degree = "ม.ปลาย"
                                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                               data["school"],
                                               status, degree, data["events"][events]["ticketToken"],
                                               data["events"][events]["teamToken"]]
                                        worksheet.append_row(row)

                                        replyObj = []
                                        replyObj.append(FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
                                        creator = userData["firstName"]
                                        flex = functions.fmsg.team(teamToken, eventName, creator)
                                        replyObj.append(FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))

                            else:
                                flex = functions.fmsg.warningFlex(
                                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                else:
                    with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                        userData = json.load(user)
                        if ((userData["status"] == "0" and userData["degree"] == "0") or userData["status"] == "1"):
                            if functions.intersects.intersects("แข่งหมากล้อม", event.source.user_id):
                                flex = functions.fmsg.warningFlex(
                                    "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                with open("data/events.json", "w", encoding="utf-8") as eventD:
                                    new_data = {userData["school"]: 1}
                                    eventData["แข่งหมากล้อม"]["school"].update(new_data)
                                    eventD.write(str(eventData).replace("'", '"'))
                                teamToken = secrets.token_hex(2)
                                while (os.path.exists("teams/{}.json".format(teamToken))):
                                    teamToken = secrets.token_hex(2)
                                with open("teams/template.json", "r", encoding="utf-8") as teamT:
                                    teamData = json.load(teamT)
                                    teamData["eventName"] = "แข่งหมากล้อม"
                                    teamData["teamId"] = teamToken
                                    teamData["school"] = userData["school"]
                                    x = {event.source.user_id: userData["status"]}
                                    teamData["members"].update(x)
                                    with open("teams/{}.json".format(teamToken), "w", encoding="utf-8") as team:
                                        team.write(str(teamData).replace("'", '"'))
                                    with open("data/events.json", "w", encoding="utf-8") as eventD:
                                        eventData["แข่งหมากล้อม"]["count"] += 1
                                        eventD.write(str(eventData).replace("'", '"'))
                                    token = secrets.token_hex(16)
                                    while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                        token = secrets.token_hex(16)
                                    img = qrcode.make(token)
                                    img.save("staticFiles/images/qrCode/{}.png".format(token))
                                    with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                        new_data = {"แข่งหมากล้อม": eventData["แข่งหมากล้อม"]}
                                        userData["events"].update(new_data)
                                        new_data = {"ticketToken": token}
                                        userData["events"]["แข่งหมากล้อม"].update(new_data)
                                        new_data = {"teamToken": teamToken}
                                        userData["events"]["แข่งหมากล้อม"].update(new_data)
                                        user.write(str(userData).replace("'", '"'))
                                    eventName = "แข่งหมากล้อม"
                                    firstName = userData["firstName"]
                                    lastName = userData["lastName"]
                                    school = userData["school"]
                                    when = time.strftime("%d/%m/%Y %H:%M",
                                                         time.localtime(eventData["แข่งหมากล้อม"]["startTime"] + 25200))
                                    place = eventData["แข่งหมากล้อม"]["place"]
                                    qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                    flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                     place,
                                                                     qr)

                                    events = "แข่งหมากล้อม"
                                    worksheet = spreadsheet.worksheet(events)
                                    data = userData
                                    if data["status"] == "0":
                                        status = "นักเรียน"
                                    elif data["status"] == "1":
                                        status = "ครู"
                                    elif data["status"] == "2":
                                        status = "ผู้ปกครอง"

                                    if data["degree"] == "0":
                                        degree = "ประถม"
                                    elif data["degree"] == "1":
                                        degree = "ม.ต้น"
                                    elif data["degree"] == "2":
                                        degree = "ม.ปลาย"
                                    row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                           data["school"],
                                           status, degree, data["events"][events]["ticketToken"],
                                           data["events"][events]["teamToken"]]
                                    worksheet.append_row(row)

                                    replyObj = []
                                    replyObj.append(FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
                                    creator = userData["firstName"]
                                    flex = functions.fmsg.team(teamToken, eventName, creator)
                                    replyObj.append(FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))

                        else:
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # เข้าร่วมทีมที่มีอยู่แล้ว แข่งหมากล้อม
    elif (event.message.text == "เข้าร่วมทีมที่มีอยู่แล้ว แข่งหมากล้อม"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                userData = json.load(user)
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if ((userData["status"] == "0" and userData["degree"] == "0") or userData["status"] == "1"):
                        if functions.intersects.intersects("แข่งหมากล้อม", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            replyObj = TextSendMessage(text='กรุณาพิมพ์รหัสทีมของคุณลงแชทนี้')

                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)





    # Secondary
    elif (event.message.text == "เลือกกิจกรรมระดับมัธยมศึกษา"):
        flex = functions.fmsg.sectionListFlex()
        replyObj = FlexSendMessage(alt_text='รายชื่อฝ่ายระดับมัธยมศึกษา', contents=flex)



    # Scholar Competition
    elif (event.message.text == "Scholar Competitions"):
        flex = functions.fmsg.scholarCompetition()
        replyObj = FlexSendMessage(alt_text='รายชื่อกิจกรรมฝ่าย Scholar Competitions', contents=flex)


    # ประกวดวาดภาพระบายสี
    elif (event.message.text == "ประกวดวาดภาพระบายสี"):
        flex = functions.fmsg.artFlex()
        replyObj = FlexSendMessage(alt_text='ประกวดวาดภาพระบายสี', contents=flex)

    # ลงสมัครประกวดวาดภาพระบายสี ม.ต้น
    elif (event.message.text == "ลงสมัครประกวดวาดภาพระบายสี ม.ต้น"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            with open("data/events.json", "r", encoding="utf-8") as eventD:
                eventData = json.load(eventD)
                if (userData["school"] in eventData["ประกวดวาดภาพระบายสี ม.ต้น"]["school"]):
                    if (eventData["ประกวดวาดภาพระบายสี ม.ต้น"]["school"][userData["school"]] >= 2):
                        flex = functions.fmsg.warningFlex("จำนวนผู้สมัครของ{}เต็มแล้ว".format(userData["school"]))
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        if (userData["status"] == "0" and userData["degree"] == "1"):
                            if functions.intersects.intersects("ประกวดวาดภาพระบายสี ม.ต้น", event.source.user_id):
                                flex = functions.fmsg.warningFlex(
                                    "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                with open("data/events.json", "w", encoding="utf-8") as eventD:
                                    eventData["ประกวดวาดภาพระบายสี ม.ต้น"]["school"][userData["school"]] += 1
                                    eventD.write(str(eventData).replace("'", '"'))
                                token = secrets.token_hex(16)
                                while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                    token = secrets.token_hex(16)
                                img = qrcode.make(token)
                                img.save("staticFiles/images/qrCode/{}.png".format(token))
                                with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                    new_data = {"ประกวดวาดภาพระบายสี ม.ต้น": eventData["ประกวดวาดภาพระบายสี ม.ต้น"]}
                                    userData["events"].update(new_data)
                                    new_data = {"ticketToken": token}
                                    userData["events"]["ประกวดวาดภาพระบายสี ม.ต้น"].update(new_data)
                                    user.write(str(userData).replace("'", '"'))
                                eventName = "ประกวดวาดภาพระบายสี ม.ต้น"
                                firstName = userData["firstName"]
                                lastName = userData["lastName"]
                                school = userData["school"]
                                when = time.strftime("%d/%m/%Y %H:%M", time.localtime(
                                    eventData["ประกวดวาดภาพระบายสี ม.ต้น"]["startTime"] + 25200))
                                place = eventData["ประกวดวาดภาพระบายสี ม.ต้น"]["place"]
                                qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place,
                                                                 qr)

                                events = "ประกวดวาดภาพระบายสี ม.ต้น"
                                worksheet = spreadsheet.worksheet(events)
                                data = userData
                                if data["status"] == "0":
                                    status = "นักเรียน"
                                elif data["status"] == "1":
                                    status = "ครู"
                                elif data["status"] == "2":
                                    status = "ผู้ปกครอง"

                                if data["degree"] == "0":
                                    degree = "ประถม"
                                elif data["degree"] == "1":
                                    degree = "ม.ต้น"
                                elif data["degree"] == "2":
                                    degree = "ม.ปลาย"
                                row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                       data["school"],
                                       status, degree, data["events"][events]["ticketToken"]]
                                worksheet.append_row(row)

                                replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                        else:
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                else:
                    if (userData["status"] == "0" and userData["degree"] == "1"):
                        if functions.intersects.intersects("ประกวดวาดภาพระบายสี ม.ต้น", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            with open("data/events.json", "w", encoding="utf-8") as eventD:
                                new_data = {userData["school"]: 1}
                                eventData["ประกวดวาดภาพระบายสี ม.ต้น"]["school"].update(new_data)
                                eventD.write(str(eventData).replace("'", '"'))
                            token = secrets.token_hex(16)
                            while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                token = secrets.token_hex(16)
                            img = qrcode.make(token)
                            img.save("staticFiles/images/qrCode/{}.png".format(token))
                            with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                new_data = {"ประกวดวาดภาพระบายสี ม.ต้น": eventData["ประกวดวาดภาพระบายสี ม.ต้น"]}
                                userData["events"].update(new_data)
                                new_data = {"ticketToken": token}
                                userData["events"]["ประกวดวาดภาพระบายสี ม.ต้น"].update(new_data)
                                user.write(str(userData).replace("'", '"'))
                            eventName = "ประกวดวาดภาพระบายสี ม.ต้น"
                            firstName = userData["firstName"]
                            lastName = userData["lastName"]
                            school = userData["school"]
                            when = time.strftime("%d/%m/%Y, %H:%M",
                                                 time.localtime(
                                                     eventData["ประกวดวาดภาพระบายสี ม.ต้น"]["startTime"] + 25200))
                            place = eventData["ประกวดวาดภาพระบายสี ม.ต้น"]["place"]
                            qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                            flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                            events = "ประกวดวาดภาพระบายสี ม.ต้น"
                            worksheet = spreadsheet.worksheet(events)
                            data = userData
                            if data["status"] == "0":
                                status = "นักเรียน"
                            elif data["status"] == "1":
                                status = "ครู"
                            elif data["status"] == "2":
                                status = "ผู้ปกครอง"

                            if data["degree"] == "0":
                                degree = "ประถม"
                            elif data["degree"] == "1":
                                degree = "ม.ต้น"
                            elif data["degree"] == "2":
                                degree = "ม.ปลาย"
                            row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                   data["school"],
                                   status, degree, data["events"][events]["ticketToken"]]
                            worksheet.append_row(row)

                            replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # ลงสมัครประกวดวาดภาพระบายสี ม.ปลาย
    elif (event.message.text == "ลงสมัครประกวดวาดภาพระบายสี ม.ปลาย"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            with open("data/events.json", "r", encoding="utf-8") as eventD:
                eventData = json.load(eventD)
                if (userData["school"] in eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]["school"]):
                    if (eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]["school"][userData["school"]] >= 2):
                        flex = functions.fmsg.warningFlex("จำนวนผู้สมัครของ{}เต็มแล้ว".format(userData["school"]))
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        if (userData["status"] == "0" and userData["degree"] == "2"):
                            if functions.intersects.intersects("ประกวดวาดภาพระบายสี ม.ปลาย", event.source.user_id):
                                flex = functions.fmsg.warningFlex(
                                    "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                with open("data/events.json", "w", encoding="utf-8") as eventD:
                                    eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]["school"][userData["school"]] += 1
                                    eventD.write(str(eventData).replace("'", '"'))
                                token = secrets.token_hex(16)
                                while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                    token = secrets.token_hex(16)
                                img = qrcode.make(token)
                                img.save("staticFiles/images/qrCode/{}.png".format(token))
                                with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                    new_data = {"ประกวดวาดภาพระบายสี ม.ปลาย": eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]}
                                    userData["events"].update(new_data)
                                    new_data = {"ticketToken": token}
                                    userData["events"]["ประกวดวาดภาพระบายสี ม.ปลาย"].update(new_data)
                                    user.write(str(userData).replace("'", '"'))
                                eventName = "ประกวดวาดภาพระบายสี ม.ปลาย"
                                firstName = userData["firstName"]
                                lastName = userData["lastName"]
                                school = userData["school"]
                                when = time.strftime("%d/%m/%Y %H:%M", time.localtime(
                                    eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]["startTime"] + 25200))
                                place = eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]["place"]
                                qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place,
                                                                 qr)

                                events = "ประกวดวาดภาพระบายสี ม.ปลาย"
                                worksheet = spreadsheet.worksheet(events)
                                data = userData
                                if data["status"] == "0":
                                    status = "นักเรียน"
                                elif data["status"] == "1":
                                    status = "ครู"
                                elif data["status"] == "2":
                                    status = "ผู้ปกครอง"

                                if data["degree"] == "0":
                                    degree = "ประถม"
                                elif data["degree"] == "1":
                                    degree = "ม.ต้น"
                                elif data["degree"] == "2":
                                    degree = "ม.ปลาย"
                                row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                       data["school"],
                                       status, degree, data["events"][events]["ticketToken"]]
                                worksheet.append_row(row)

                                replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                        else:
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                else:
                    if (userData["status"] == "0" and userData["degree"] == "2"):
                        if functions.intersects.intersects("ประกวดวาดภาพระบายสี ม.ปลาย", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            with open("data/events.json", "w", encoding="utf-8") as eventD:
                                new_data = {userData["school"]: 1}
                                eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]["school"].update(new_data)
                                eventD.write(str(eventData).replace("'", '"'))
                            token = secrets.token_hex(16)
                            while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                token = secrets.token_hex(16)
                            img = qrcode.make(token)
                            img.save("staticFiles/images/qrCode/{}.png".format(token))
                            with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                new_data = {"ประกวดวาดภาพระบายสี ม.ปลาย": eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]}
                                userData["events"].update(new_data)
                                new_data = {"ticketToken": token}
                                userData["events"]["ประกวดวาดภาพระบายสี ม.ปลาย"].update(new_data)
                                user.write(str(userData).replace("'", '"'))
                            eventName = "ประกวดวาดภาพระบายสี ม.ปลาย"
                            firstName = userData["firstName"]
                            lastName = userData["lastName"]
                            school = userData["school"]
                            when = time.strftime("%d/%m/%Y, %H:%M",
                                                 time.localtime(
                                                     eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]["startTime"] + 25200))
                            place = eventData["ประกวดวาดภาพระบายสี ม.ปลาย"]["place"]
                            qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                            flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                            events = "ประกวดวาดภาพระบายสี ม.ปลาย"
                            worksheet = spreadsheet.worksheet(events)
                            data = userData
                            if data["status"] == "0":
                                status = "นักเรียน"
                            elif data["status"] == "1":
                                status = "ครู"
                            elif data["status"] == "2":
                                status = "ผู้ปกครอง"

                            if data["degree"] == "0":
                                degree = "ประถม"
                            elif data["degree"] == "1":
                                degree = "ม.ต้น"
                            elif data["degree"] == "2":
                                degree = "ม.ปลาย"
                            row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                   data["school"],
                                   status, degree, data["events"][events]["ticketToken"]]
                            worksheet.append_row(row)

                            replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)


    # ภาษาไทยในฐานะภาษาต่างประเทศ
    elif (event.message.text == "ภาษาไทยในฐานะภาษาต่างประเทศ"):
        flex = functions.fmsg.thaiFlex()
        replyObj = FlexSendMessage(alt_text='ภาษาไทยในฐานะภาษาต่างประเทศ', contents=flex)

    # ลงสมัครภาษาไทยในฐานะภาษาต่างประเทศ
    elif (event.message.text == "ลงสมัครภาษาไทยในฐานะภาษาต่างประเทศ"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["ภาษาไทยในฐานะภาษาต่างประเทศ"]["count"] >= 30:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if userData["status"] == "1":
                        if functions.intersects.intersects("ภาษาไทยในฐานะภาษาต่างประเทศ", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            with open("data/events.json", "w", encoding="utf-8") as eventD:
                                eventData["ภาษาไทยในฐานะภาษาต่างประเทศ"]["count"] += 1
                                eventD.write(str(eventData).replace("'", '"'))
                            token = secrets.token_hex(16)
                            while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                token = secrets.token_hex(16)
                            img = qrcode.make(token)
                            img.save("staticFiles/images/qrCode/{}.png".format(token))
                            with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                new_data = {"ภาษาไทยในฐานะภาษาต่างประเทศ": eventData["ภาษาไทยในฐานะภาษาต่างประเทศ"]}
                                userData["events"].update(new_data)
                                new_data = {"ticketToken": token}
                                userData["events"]["ภาษาไทยในฐานะภาษาต่างประเทศ"].update(new_data)
                                user.write(str(userData).replace("'", '"'))
                            eventName = "ภาษาไทยในฐานะภาษาต่างประเทศ"
                            firstName = userData["firstName"]
                            lastName = userData["lastName"]
                            school = userData["school"]
                            when = time.strftime("%d/%m/%Y %H:%M",
                                                 time.localtime(
                                                     eventData["ภาษาไทยในฐานะภาษาต่างประเทศ"]["startTime"] + 25200))
                            place = eventData["ภาษาไทยในฐานะภาษาต่างประเทศ"]["place"]
                            qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                            flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                            events = "ภาษาไทยในฐานะภาษาต่างประเทศ"
                            worksheet = spreadsheet.worksheet(events)
                            data = userData
                            if data["status"] == "0":
                                status = "นักเรียน"
                            elif data["status"] == "1":
                                status = "ครู"
                            elif data["status"] == "2":
                                status = "ผู้ปกครอง"

                            if data["degree"] == "0":
                                degree = "ประถม"
                            elif data["degree"] == "1":
                                degree = "ม.ต้น"
                            elif data["degree"] == "2":
                                degree = "ม.ปลาย"
                            row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                   data["school"],
                                   status, degree, data["events"][events]["ticketToken"]]
                            worksheet.append_row(row)

                            replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)



    # HomeCourt
    elif (event.message.text == "HomeCourt"):
        flex = functions.fmsg.peFlex()
        replyObj = FlexSendMessage(alt_text='HomeCourt', contents=flex)

    elif (event.message.text == "ลงสมัครโฮมคอร์ทแอปพลิเคชันกับการประยุกต์ใช้"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["HomeCourt"]["count"] >= 40:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if userData["status"] == "1" or userData["status"] == "0":
                        if functions.intersects.intersects("HomeCourt", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            with open("data/events.json", "w", encoding="utf-8") as eventD:
                                eventData["HomeCourt"]["count"] += 1
                                eventD.write(str(eventData).replace("'", '"'))
                            token = secrets.token_hex(16)
                            while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                token = secrets.token_hex(16)
                            img = qrcode.make(token)
                            img.save("staticFiles/images/qrCode/{}.png".format(token))
                            with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                new_data = {"HomeCourt": eventData["HomeCourt"]}
                                userData["events"].update(new_data)
                                new_data = {"ticketToken": token}
                                userData["events"]["HomeCourt"].update(new_data)
                                user.write(str(userData).replace("'", '"'))
                            eventName = "HomeCourt"
                            firstName = userData["firstName"]
                            lastName = userData["lastName"]
                            school = userData["school"]
                            when = time.strftime("%d/%m/%Y %H:%M",
                                                 time.localtime(eventData["HomeCourt"]["startTime"] + 25200))
                            place = eventData["HomeCourt"]["place"]
                            qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                            flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                            events = "HomeCourt"
                            worksheet = spreadsheet.worksheet(events)
                            data = userData
                            if data["status"] == "0":
                                status = "นักเรียน"
                            elif data["status"] == "1":
                                status = "ครู"
                            elif data["status"] == "2":
                                status = "ผู้ปกครอง"

                            if data["degree"] == "0":
                                degree = "ประถม"
                            elif data["degree"] == "1":
                                degree = "ม.ต้น"
                            elif data["degree"] == "2":
                                degree = "ม.ปลาย"
                            row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                   data["school"],
                                   status, degree, data["events"][events]["ticketToken"]]
                            worksheet.append_row(row)

                            replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)


    # CANSAT
    elif (event.message.text == "CANSAT"):
        flex = functions.fmsg.sciFlex()
        replyObj = FlexSendMessage(alt_text='CANSAT', contents=flex)

    # ลงสมัครการอบรมสร้างดาวเทียมขนาดจิ๋ว
    elif (event.message.text == "ลงสมัครการอบรมสร้างดาวเทียมขนาดจิ๋ว"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            if (userData["status"] == "0" and userData["degree"] == "2"):
                if functions.intersects.intersects("CANSAT", event.source.user_id):
                    flex = functions.fmsg.warningFlex(
                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                else:
                    flex = functions.fmsg.teamOptionFlex("CANSAT")
                    replyObj = FlexSendMessage(alt_text='ทีม', contents=flex)

            else:
                flex = functions.fmsg.warningFlex(
                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # สร้างทีมใหม่การอบรมสร้างดาวเทียมขนาดจิ๋ว
    elif (event.message.text == "สร้างทีมใหม่ CANSAT"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["CANSAT"]["countBCC"] >= 5:
                flex = functions.fmsg.warningFlex(
                    "ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว (กรุงเทพคริสเตียนวิทยาลัย)")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                line_bot_api.reply_message(event.reply_token, replyObj)
                return
            if eventData["CANSAT"]["count"] >= 10:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if (userData["status"] == "0" and userData["degree"] == "2"):
                        if functions.intersects.intersects("CANSAT", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            teamToken = secrets.token_hex(2)
                            while (os.path.exists("teams/{}.json".format(teamToken))):
                                teamToken = secrets.token_hex(2)
                            with open("teams/template.json", "r", encoding="utf-8") as teamT:
                                teamData = json.load(teamT)
                                teamData["eventName"] = "CANSAT"
                                teamData["teamId"] = teamToken
                                teamData["school"] = userData["school"]
                                x = {event.source.user_id: userData["status"]}
                                teamData["members"].update(x)
                                with open("teams/{}.json".format(teamToken), "w", encoding="utf-8") as team:
                                    team.write(str(teamData).replace("'", '"'))
                                if (userData["school"] == "กรุงเทพคริสเตียนวิทยาลัย"):
                                    with open("data/events.json", "w", encoding="utf-8") as eventD:
                                        eventData["CANSAT"]["countBCC"] += 1
                                        eventD.write(str(eventData).replace("'", '"'))
                                else:
                                    with open("data/events.json", "w", encoding="utf-8") as eventD:
                                        eventData["CANSAT"]["count"] += 1
                                        eventD.write(str(eventData).replace("'", '"'))
                                token = secrets.token_hex(16)
                                while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                    token = secrets.token_hex(16)
                                img = qrcode.make(token)
                                img.save("staticFiles/images/qrCode/{}.png".format(token))
                                with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                    new_data = {"CANSAT": eventData["CANSAT"]}
                                    userData["events"].update(new_data)
                                    new_data = {"ticketToken": token}
                                    userData["events"]["CANSAT"].update(new_data)
                                    new_data = {"teamToken": teamToken}
                                    userData["events"]["CANSAT"].update(new_data)
                                    user.write(str(userData).replace("'", '"'))
                                eventName = "CANSAT"
                                firstName = userData["firstName"]
                                lastName = userData["lastName"]
                                school = userData["school"]
                                when = time.strftime("%d/%m/%Y %H:%M",
                                                     time.localtime(eventData["CANSAT"]["startTime"] + 25200))
                                place = eventData["CANSAT"]["place"]
                                qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place,
                                                                 qr)

                                events = "CANSAT"
                                worksheet = spreadsheet.worksheet(events)
                                data = userData
                                if data["status"] == "0":
                                    status = "นักเรียน"
                                elif data["status"] == "1":
                                    status = "ครู"
                                elif data["status"] == "2":
                                    status = "ผู้ปกครอง"

                                if data["degree"] == "0":
                                    degree = "ประถม"
                                elif data["degree"] == "1":
                                    degree = "ม.ต้น"
                                elif data["degree"] == "2":
                                    degree = "ม.ปลาย"
                                row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                       data["school"],
                                       status, degree, data["events"][events]["ticketToken"],
                                       data["events"][events]["teamToken"]]
                                worksheet.append_row(row)

                                replyObj = []
                                replyObj.append(FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
                                creator = userData["firstName"]
                                flex = functions.fmsg.team(teamToken, eventName, creator)
                                replyObj.append(FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))

                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # เข้าร่วมทีมที่มีอยู่แล้ว CANSAT
    elif (event.message.text == "เข้าร่วมทีมที่มีอยู่แล้ว CANSAT"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            if (userData["status"] == "0" and userData["degree"] == "2"):
                if functions.intersects.intersects("CANSAT", event.source.user_id):
                    flex = functions.fmsg.warningFlex(
                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                else:
                    replyObj = TextSendMessage(text='กรุณาพิมพ์รหัสทีมของคุณลงแชทนี้')

            else:
                flex = functions.fmsg.warningFlex(
                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # Soft Cookie
    elif (event.message.text == "Soft Cookie"):
        flex = functions.fmsg.workFlex()
        replyObj = FlexSendMessage(alt_text='Soft Cookie', contents=flex)

    # ลงสมัครการทำขนมอบ Soft Cookie
    elif (event.message.text == "ลงสมัครการทำขนมอบ Soft Cookie"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Soft Cookie"]["count"] >= 24:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if (userData["status"] == "0" and userData["degree"] == "1") or (
                            userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1":
                        if functions.intersects.intersects("Soft Cookie", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            with open("data/events.json", "w", encoding="utf-8") as eventD:
                                eventData["Soft Cookie"]["count"] += 1
                                eventD.write(str(eventData).replace("'", '"'))
                            token = secrets.token_hex(16)
                            while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                token = secrets.token_hex(16)
                            img = qrcode.make(token)
                            img.save("staticFiles/images/qrCode/{}.png".format(token))
                            with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                new_data = {"Soft Cookie": eventData["Soft Cookie"]}
                                userData["events"].update(new_data)
                                new_data = {"ticketToken": token}
                                userData["events"]["Soft Cookie"].update(new_data)
                                user.write(str(userData).replace("'", '"'))
                            eventName = "Soft Cookie"
                            firstName = userData["firstName"]
                            lastName = userData["lastName"]
                            school = userData["school"]
                            when = time.strftime("%d/%m/%Y %H:%M",
                                                 time.localtime(eventData["Soft Cookie"]["startTime"] + 25200))
                            place = eventData["Soft Cookie"]["place"]
                            qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                            flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                            events = "Soft Cookie"
                            worksheet = spreadsheet.worksheet(events)
                            data = userData
                            if data["status"] == "0":
                                status = "นักเรียน"
                            elif data["status"] == "1":
                                status = "ครู"
                            elif data["status"] == "2":
                                status = "ผู้ปกครอง"

                            if data["degree"] == "0":
                                degree = "ประถม"
                            elif data["degree"] == "1":
                                degree = "ม.ต้น"
                            elif data["degree"] == "2":
                                degree = "ม.ปลาย"
                            row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                   data["school"],
                                   status, degree, data["events"][events]["ticketToken"]]
                            worksheet.append_row(row)

                            replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)


    # เปลี่ยนรบเป็นรัก
    elif (event.message.text == "เปลี่ยนรบเป็นรัก"):
        flex = functions.fmsg.socialFlex()
        replyObj = FlexSendMessage(alt_text='เปลี่ยนรบเป็นรัก', contents=flex)

    # ลงสมัครไกล่เกลี่ย !!! เคลียร์ให้จบ (เปลี่ยนรบเป็นรัก)
    elif (event.message.text == "ลงสมัครไกล่เกลี่ย !!! เคลียร์ให้จบ (เปลี่ยนรบเป็นรัก)"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            if ((userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1"):
                if functions.intersects.intersects("เปลี่ยนรบเป็นรัก", event.source.user_id):
                    flex = functions.fmsg.warningFlex(
                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                else:
                    flex = functions.fmsg.teamOptionFlex("เปลี่ยนรบเป็นรัก")
                    replyObj = FlexSendMessage(alt_text='ทีม', contents=flex)

            else:
                flex = functions.fmsg.warningFlex(
                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # สร้างทีมใหม่ เปลี่ยนรบเป็นรัก
    elif (event.message.text == "สร้างทีมใหม่ เปลี่ยนรบเป็นรัก"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["เปลี่ยนรบเป็นรัก"]["count"] >= 20:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if ((userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1"):
                        if functions.intersects.intersects("เปลี่ยนรบเป็นรัก", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            teamToken = secrets.token_hex(2)
                            while (os.path.exists("teams/{}.json".format(teamToken))):
                                teamToken = secrets.token_hex(2)
                            with open("teams/template.json", "r", encoding="utf-8") as teamT:
                                teamData = json.load(teamT)
                                teamData["eventName"] = "เปลี่ยนรบเป็นรัก"
                                teamData["teamId"] = teamToken
                                teamData["school"] = userData["school"]
                                x = {event.source.user_id: userData["status"]}
                                teamData["members"].update(x)
                                with open("teams/{}.json".format(teamToken), "w", encoding="utf-8") as team:
                                    team.write(str(teamData).replace("'", '"'))
                                with open("data/events.json", "w", encoding="utf-8") as eventD:
                                    eventData["เปลี่ยนรบเป็นรัก"]["count"] += 1
                                    eventD.write(str(eventData).replace("'", '"'))
                                token = secrets.token_hex(16)
                                while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                    token = secrets.token_hex(16)
                                img = qrcode.make(token)
                                img.save("staticFiles/images/qrCode/{}.png".format(token))
                                with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                    new_data = {"เปลี่ยนรบเป็นรัก": eventData["เปลี่ยนรบเป็นรัก"]}
                                    userData["events"].update(new_data)
                                    new_data = {"ticketToken": token}
                                    userData["events"]["เปลี่ยนรบเป็นรัก"].update(new_data)
                                    new_data = {"teamToken": teamToken}
                                    userData["events"]["เปลี่ยนรบเป็นรัก"].update(new_data)
                                    user.write(str(userData).replace("'", '"'))
                                eventName = "เปลี่ยนรบเป็นรัก"
                                firstName = userData["firstName"]
                                lastName = userData["lastName"]
                                school = userData["school"]
                                when = time.strftime("%d/%m/%Y %H:%M",
                                                     time.localtime(
                                                         eventData["เปลี่ยนรบเป็นรัก"]["startTime"] + 25200))
                                place = eventData["เปลี่ยนรบเป็นรัก"]["place"]
                                qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place,
                                                                 qr)

                                events = "เปลี่ยนรบเป็นรัก"
                                worksheet = spreadsheet.worksheet(events)
                                data = userData
                                if data["status"] == "0":
                                    status = "นักเรียน"
                                elif data["status"] == "1":
                                    status = "ครู"
                                elif data["status"] == "2":
                                    status = "ผู้ปกครอง"

                                if data["degree"] == "0":
                                    degree = "ประถม"
                                elif data["degree"] == "1":
                                    degree = "ม.ต้น"
                                elif data["degree"] == "2":
                                    degree = "ม.ปลาย"
                                row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                       data["school"],
                                       status, degree, data["events"][events]["ticketToken"],
                                       data["events"][events]["teamToken"]]
                                worksheet.append_row(row)

                                replyObj = []
                                replyObj.append(FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
                                creator = userData["firstName"]
                                flex = functions.fmsg.team(teamToken, eventName, creator)
                                replyObj.append(FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))

                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # เข้าร่วมทีมที่มีอยู่แล้ว เปลี่ยนรบเป็นรัก
    elif (event.message.text == "เข้าร่วมทีมที่มีอยู่แล้ว เปลี่ยนรบเป็นรัก"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            if ((userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1"):
                if functions.intersects.intersects("เปลี่ยนรบเป็นรัก", event.source.user_id):
                    flex = functions.fmsg.warningFlex(
                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                else:
                    replyObj = TextSendMessage(text='กรุณาพิมพ์รหัสทีมของคุณลงแชทนี้')

            else:
                flex = functions.fmsg.warningFlex(
                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # English Singing Contest
    elif (event.message.text == "English Singing Contest"):
        flex = functions.fmsg.engFlex()
        replyObj = FlexSendMessage(alt_text='English Singing Contest', contents=flex)

    # ลงสมัครการแข่งขันประกวดร้องเพลงภาษาอังกฤษ(ประเภทขับร้องเดี่ยว)
    elif (event.message.text == "ลงสมัครการแข่งขันประกวดร้องเพลงภาษาอังกฤษ(ประเภทขับร้องเดี่ยว)"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            if ((userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1"):
                if functions.intersects.intersects("English Singing Contest", event.source.user_id):
                    flex = functions.fmsg.warningFlex(
                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                else:
                    flex = functions.fmsg.teamOptionFlex("English Singing Contest")
                    replyObj = FlexSendMessage(alt_text='ทีม', contents=flex)

            else:
                flex = functions.fmsg.warningFlex(
                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # สร้างทีมใหม่ English Singing Contest
    elif (event.message.text == "สร้างทีมใหม่ English Singing Contest"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                userData = json.load(user)
                if ((userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1"):
                    if functions.intersects.intersects("English Singing Contest", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        if userData["school"] in eventData["English Singing Contest"]["school"]:
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากโรงเรียนของคุณได้สมัครกิจกรรมนี้ไปแล้ว")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            teamToken = secrets.token_hex(2)
                            while (os.path.exists("teams/{}.json".format(teamToken))):
                                teamToken = secrets.token_hex(2)
                            with open("teams/template.json", "r", encoding="utf-8") as teamT:
                                teamData = json.load(teamT)
                                teamData["eventName"] = "English Singing Contest"
                                teamData["teamId"] = teamToken
                                teamData["school"] = userData["school"]
                                x = {event.source.user_id: userData["status"]}
                                teamData["members"].update(x)
                                with open("teams/{}.json".format(teamToken), "w", encoding="utf-8") as team:
                                    team.write(str(teamData).replace("'", '"'))
                                with open("data/events.json", "w", encoding="utf-8") as eventD:
                                    eventData["English Singing Contest"]["count"] += 1
                                    new_data = {userData["school"]: 1}
                                    eventData["English Singing Contest"]["school"].update(new_data)
                                    eventD.write(str(eventData).replace("'", '"'))
                                token = secrets.token_hex(16)
                                while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                    token = secrets.token_hex(16)
                                img = qrcode.make(token)
                                img.save("staticFiles/images/qrCode/{}.png".format(token))
                                with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                    new_data = {"English Singing Contest": eventData["English Singing Contest"]}
                                    userData["events"].update(new_data)
                                    new_data = {"ticketToken": token}
                                    userData["events"]["English Singing Contest"].update(new_data)
                                    new_data = {"teamToken": teamToken}
                                    userData["events"]["English Singing Contest"].update(new_data)
                                    user.write(str(userData).replace("'", '"'))
                                eventName = "English Singing Contest"
                                firstName = userData["firstName"]
                                lastName = userData["lastName"]
                                school = userData["school"]
                                when = time.strftime("%d/%m/%Y %H:%M",
                                                     time.localtime(
                                                         eventData["English Singing Contest"]["startTime"] + 25200))
                                place = eventData["English Singing Contest"]["place"]
                                qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place,
                                                                 qr)

                                events = "English Singing Contest"
                                worksheet = spreadsheet.worksheet(events)
                                data = userData
                                if data["status"] == "0":
                                    status = "นักเรียน"
                                elif data["status"] == "1":
                                    status = "ครู"
                                elif data["status"] == "2":
                                    status = "ผู้ปกครอง"

                                if data["degree"] == "0":
                                    degree = "ประถม"
                                elif data["degree"] == "1":
                                    degree = "ม.ต้น"
                                elif data["degree"] == "2":
                                    degree = "ม.ปลาย"
                                row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                       data["school"],
                                       status, degree, data["events"][events]["ticketToken"],
                                       data["events"][events]["teamToken"]]
                                worksheet.append_row(row)

                                replyObj = []
                                replyObj.append(FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
                                creator = userData["firstName"]
                                flex = functions.fmsg.team(teamToken, eventName, creator)
                                replyObj.append(FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))

                else:
                    flex = functions.fmsg.warningFlex(
                        "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # เข้าร่วมทีมที่มีอยู่แล้ว English Singing Contest
    elif (event.message.text == "เข้าร่วมทีมที่มีอยู่แล้ว English Singing Contest"):
        with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
            userData = json.load(user)
            if ((userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1"):
                if functions.intersects.intersects("English Singing Contest", event.source.user_id):
                    flex = functions.fmsg.warningFlex(
                        "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                    replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                else:
                    replyObj = TextSendMessage(text='กรุณาพิมพ์รหัสทีมของคุณลงแชทนี้')

            else:
                flex = functions.fmsg.warningFlex(
                    "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)


    # เกมการเรียนรู้ธุรกิจ
    elif (event.message.text == "เกมการเรียนรู้ธุรกิจ"):
        flex = functions.fmsg.mathFlex()
        replyObj = FlexSendMessage(alt_text='เกมการเรียนรู้ธุรกิจ', contents=flex)

    # ลงสมัครเกมการเรียนรู้ธุรกิจ
    elif (event.message.text == "ลงสมัครเกมการเรียนรู้ธุรกิจ"):
        flex = functions.fmsg.warningFlex("ขณะนี้เกมการเรียนรู้ธุรกิจปิดการรับสมัครแล้ว ขออภัยในความไม่สะดวก")
        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
        # with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
        #     userData = json.load(user)
        #     if ((userData["status"] == "0" and userData["degree"] == "1") or (
        #             userData["status"] == "1" and userData["degree"] == "1")):
        #         if functions.intersects.intersects("เกมการเรียนรู้ธุรกิจ", event.source.user_id):
        #             flex = functions.fmsg.warningFlex(
        #                 "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
        #             replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
        #         else:
        #             flex = functions.fmsg.teamOptionFlex("เกมการเรียนรู้ธุรกิจ")
        #             replyObj = FlexSendMessage(alt_text='ทีม', contents=flex)
        #
        #     else:
        #         flex = functions.fmsg.warningFlex(
        #             "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
        #         replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # # สร้างทีมใหม่ เกมการเรียนรู้ธุรกิจ
    # elif (event.message.text == "สร้างทีมใหม่ เกมการเรียนรู้ธุรกิจ"):
    #     with open("data/events.json", "r", encoding="utf-8") as eventD:
    #         eventData = json.load(eventD)
    #         if eventData["เกมการเรียนรู้ธุรกิจ"]["count"] >= 10:
    #             flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
    #             replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
    #         else:
    #             with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
    #                 userData = json.load(user)
    #                 if ((userData["status"] == "0" and userData["degree"] == "1") or (
    #                         userData["status"] == "1" and userData["degree"] == "1")):
    #                     if functions.intersects.intersects("เกมการเรียนรู้ธุรกิจ", event.source.user_id):
    #                         flex = functions.fmsg.warningFlex(
    #                             "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
    #                         replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
    #                     else:
    #                         if userData["school"] in eventData["เกมการเรียนรู้ธุรกิจ"]["school"]:
    #                             flex = functions.fmsg.warningFlex(
    #                                 "ไม่สามารถสมัครได้ เนื่องจากโรงเรียนของคุณได้สมัครกิจกรรมนี้ไปแล้ว")
    #                             replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
    #                         else:
    #                             teamToken = secrets.token_hex(2)
    #                             while (os.path.exists("teams/{}.json".format(teamToken))):
    #                                 teamToken = secrets.token_hex(2)
    #                             with open("teams/template.json", "r", encoding="utf-8") as teamT:
    #                                 teamData = json.load(teamT)
    #                                 teamData["eventName"] = "เกมการเรียนรู้ธุรกิจ"
    #                                 teamData["teamId"] = teamToken
    #                                 teamData["school"] = userData["school"]
    #                                 x = {event.source.user_id: userData["status"]}
    #                                 teamData["members"].update(x)
    #                                 with open("teams/{}.json".format(teamToken), "w", encoding="utf-8") as team:
    #                                     team.write(str(teamData).replace("'", '"'))
    #                                 with open("data/events.json", "w", encoding="utf-8") as eventD:
    #                                     eventData["เกมการเรียนรู้ธุรกิจ"]["count"] += 1
    #                                     new_data = {userData["school"]: 1}
    #                                     eventData["เกมการเรียนรู้ธุรกิจ"]["school"].update(new_data)
    #                                     eventD.write(str(eventData).replace("'", '"'))
    #                                 token = secrets.token_hex(16)
    #                                 while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
    #                                     token = secrets.token_hex(16)
    #                                 img = qrcode.make(token)
    #                                 img.save("staticFiles/images/qrCode/{}.png".format(token))
    #                                 with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
    #                                     new_data = {"เกมการเรียนรู้ธุรกิจ": eventData["เกมการเรียนรู้ธุรกิจ"]}
    #                                     userData["events"].update(new_data)
    #                                     new_data = {"ticketToken": token}
    #                                     userData["events"]["เกมการเรียนรู้ธุรกิจ"].update(new_data)
    #                                     new_data = {"teamToken": teamToken}
    #                                     userData["events"]["เกมการเรียนรู้ธุรกิจ"].update(new_data)
    #                                     user.write(str(userData).replace("'", '"'))
    #                                 eventName = "เกมการเรียนรู้ธุรกิจ"
    #                                 firstName = userData["firstName"]
    #                                 lastName = userData["lastName"]
    #                                 school = userData["school"]
    #                                 when = time.strftime("%d/%m/%Y %H:%M",
    #                                                      time.localtime(
    #                                                          eventData["เกมการเรียนรู้ธุรกิจ"]["startTime"] + 25200))
    #                                 place = eventData["เกมการเรียนรู้ธุรกิจ"]["place"]
    #                                 qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
    #                                 flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
    #                                                                  place,
    #                                                                  qr)
    #
    #                                 events = "เกมการเรียนรู้ธุรกิจ"
    #                                 worksheet = spreadsheet.worksheet(events)
    #                                 data = userData
    #                                 if data["status"] == "0":
    #                                     status = "นักเรียน"
    #                                 elif data["status"] == "1":
    #                                     status = "ครู"
    #                                 elif data["status"] == "2":
    #                                     status = "ผู้ปกครอง"
    #
    #                                 if data["degree"] == "0":
    #                                     degree = "ประถม"
    #                                 elif data["degree"] == "1":
    #                                     degree = "ม.ต้น"
    #                                 elif data["degree"] == "2":
    #                                     degree = "ม.ปลาย"
    #                                 row = [data["firstName"], data["lastName"], data["phone"], data["email"],
    #                                        data["school"],
    #                                        status, degree, data["events"][events]["ticketToken"],
    #                                        data["events"][events]["teamToken"]]
    #                                 worksheet.append_row(row)
    #
    #                                 replyObj = []
    #                                 replyObj.append(FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex))
    #                                 creator = userData["firstName"]
    #                                 flex = functions.fmsg.team(teamToken, eventName, creator)
    #                                 replyObj.append(FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))
    #
    #                 else:
    #                     flex = functions.fmsg.warningFlex(
    #                         "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
    #                     replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
    #
    # # เข้าร่วมทีมที่มีอยู่แล้ว เกมการเรียนรู้ธุรกิจ
    # elif (event.message.text == "เข้าร่วมทีมที่มีอยู่แล้ว เกมการเรียนรู้ธุรกิจ"):
    #     with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
    #         userData = json.load(user)
    #         if ((userData["status"] == "0" and userData["degree"] == "1") or (
    #                 userData["status"] == "1" and userData["degree"] == "1")):
    #             if functions.intersects.intersects("เกมการเรียนรู้ธุรกิจ", event.source.user_id):
    #                 flex = functions.fmsg.warningFlex(
    #                     "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
    #                 replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
    #             else:
    #                 replyObj = TextSendMessage(text='กรุณาพิมพ์รหัสทีมของคุณลงแชทนี้')
    #
    #         else:
    #             flex = functions.fmsg.warningFlex(
    #                 "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
    #             replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # Secondary Demonstration
    elif (event.message.text == "BCC Market ช็อปเพลิน เดิน “ตลาดเติมใจ (J.A.I.)”"):
        flex = functions.fmsg.secondaryDemonstration()
        replyObj = FlexSendMessage(alt_text='BCC Market ช็อปเพลิน เดิน “ตลาดเติมใจ (J.A.I.)”', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมอักษรศาสตร์(จีน)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง": eventData["กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(
                                                 eventData["กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง"]["startTime"] + 25200))
                        place = eventData["กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "กินหรู กินเหลาตั้งแต่ราชวงศ์ชิง"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมอักษรศาสตร์(ญี่ปุ่น)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["มุดท่อตะลุยตลาด"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("มุดท่อตะลุยตลาด", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["มุดท่อตะลุยตลาด"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"มุดท่อตะลุยตลาด": eventData["มุดท่อตะลุยตลาด"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["มุดท่อตะลุยตลาด"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "มุดท่อตะลุยตลาด"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["มุดท่อตะลุยตลาด"]["startTime"] + 25200))
                        place = eventData["มุดท่อตะลุยตลาด"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "มุดท่อตะลุยตลาด"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมนิเทศศาสตร์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["สดใหม่ สายตัด!!!"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("สดใหม่ สายตัด!!!", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["สดใหม่ สายตัด!!!"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"สดใหม่ สายตัด!!!": eventData["สดใหม่ สายตัด!!!"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["สดใหม่ สายตัด!!!"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "สดใหม่ สายตัด!!!"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["สดใหม่ สายตัด!!!"]["startTime"] + 25200))
                        place = eventData["สดใหม่ สายตัด!!!"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "สดใหม่ สายตัด!!!"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมบริหารธุรกิจ"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["การตัดสินใจธุรกิจแบบผู้ประกอบการ"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("การตัดสินใจธุรกิจแบบผู้ประกอบการ", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["การตัดสินใจธุรกิจแบบผู้ประกอบการ"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {
                                "การตัดสินใจธุรกิจแบบผู้ประกอบการ": eventData["การตัดสินใจธุรกิจแบบผู้ประกอบการ"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["การตัดสินใจธุรกิจแบบผู้ประกอบการ"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "การตัดสินใจธุรกิจแบบผู้ประกอบการ"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(
                                                 eventData["การตัดสินใจธุรกิจแบบผู้ประกอบการ"]["startTime"] + 25200))
                        place = eventData["การตัดสินใจธุรกิจแบบผู้ประกอบการ"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "การตัดสินใจธุรกิจแบบผู้ประกอบการ"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมสังคมศาสตร์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["เสวนาภาษาสังคม"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("เสวนาภาษาสังคม", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["เสวนาภาษาสังคม"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"เสวนาภาษาสังคม": eventData["เสวนาภาษาสังคม"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["เสวนาภาษาสังคม"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "เสวนาภาษาสังคม"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["เสวนาภาษาสังคม"]["startTime"] + 25200))
                        place = eventData["เสวนาภาษาสังคม"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "เสวนาภาษาสังคม"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมศิลปกรรมศาสตร์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["สืบสานลายศิลป์ไทย"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("สืบสานลายศิลป์ไทย", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["สืบสานลายศิลป์ไทย"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"สืบสานลายศิลป์ไทย": eventData["สืบสานลายศิลป์ไทย"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["สืบสานลายศิลป์ไทย"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "สืบสานลายศิลป์ไทย"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["สืบสานลายศิลป์ไทย"]["startTime"] + 25200))
                        place = eventData["สืบสานลายศิลป์ไทย"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "สืบสานลายศิลป์ไทย"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมอักษรศาสตร์(ไทย)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["ร้านปันสุข"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("ร้านปันสุข", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["ร้านปันสุข"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"ร้านปันสุข": eventData["ร้านปันสุข"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["ร้านปันสุข"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "ร้านปันสุข"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["ร้านปันสุข"]["startTime"] + 25200))
                        place = eventData["ร้านปันสุข"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "ร้านปันสุข"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมศิลปะการประกอบอาหาร"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["อร่อยเต็มคำ คุกกี้แฟนซี"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("อร่อยเต็มคำ คุกกี้แฟนซี", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["อร่อยเต็มคำ คุกกี้แฟนซี"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"อร่อยเต็มคำ คุกกี้แฟนซี": eventData["อร่อยเต็มคำ คุกกี้แฟนซี"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["อร่อยเต็มคำ คุกกี้แฟนซี"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "อร่อยเต็มคำ คุกกี้แฟนซี"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["อร่อยเต็มคำ คุกกี้แฟนซี"]["startTime"] + 25200))
                        place = eventData["อร่อยเต็มคำ คุกกี้แฟนซี"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "อร่อยเต็มคำ คุกกี้แฟนซี"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมสถาปัตยกรรมศาสตร์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Architecture project"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Architecture project", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Architecture project"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Architecture project": eventData["Architecture project"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Architecture project"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Architecture project"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Architecture project"]["startTime"] + 25200))
                        place = eventData["Architecture project"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Architecture project"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมสถาปัตยกรรมศาสตร์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Architecture project"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Architecture project", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Architecture project"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Architecture project": eventData["Architecture project"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Architecture project"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Architecture project"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Architecture project"]["startTime"] + 25200))
                        place = eventData["Architecture project"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Architecture project"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมแพทยศาสตร์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Our Body"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Our Body", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Our Body"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Our Body": eventData["Our Body"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Our Body"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Our Body"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Our Body"]["startTime"] + 25200))
                        place = eventData["Our Body"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Our Body"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)


    elif (event.message.text == "ลงสมัครกิจกรรมวิศวกรรมศาสตร์การบิน"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["BCC Space project"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("BCC Space project", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["BCC Space project"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"BCC Space project": eventData["BCC Space project"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["BCC Space project"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "BCC Space project"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["BCC Space project"]["startTime"] + 25200))
                        place = eventData["BCC Space project"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "BCC Space project"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมวิศวกรรมชีวการแพทย์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Biomedical engineering International Innovation for a brighter change"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects(
                            "Biomedical engineering International Innovation for a brighter change",
                            event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Biomedical engineering International Innovation for a brighter change"][
                                "count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {
                                "Biomedical engineering International Innovation for a brighter change": eventData[
                                    "Biomedical engineering International Innovation for a brighter change"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"][
                                "Biomedical engineering International Innovation for a brighter change"].update(
                                new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Biomedical engineering International Innovation for a brighter change"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData[
                                                                "Biomedical engineering International Innovation for a brighter change"][
                                                                "startTime"] + 25200))
                        place = eventData["Biomedical engineering International Innovation for a brighter change"][
                            "place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Biomedical engineering International Innovation for a brighter change"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมวิศวกรรมศาสตร์ 1"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["สนุกกับวงจรอิเล็กทรอนิกส์"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("สนุกกับวงจรอิเล็กทรอนิกส์", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["สนุกกับวงจรอิเล็กทรอนิกส์"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"สนุกกับวงจรอิเล็กทรอนิกส์": eventData["สนุกกับวงจรอิเล็กทรอนิกส์"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["สนุกกับวงจรอิเล็กทรอนิกส์"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "สนุกกับวงจรอิเล็กทรอนิกส์"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(
                                                 eventData["สนุกกับวงจรอิเล็กทรอนิกส์"]["startTime"] + 25200))
                        place = eventData["สนุกกับวงจรอิเล็กทรอนิกส์"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "สนุกกับวงจรอิเล็กทรอนิกส์"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมวิศวกรรมศาสตร์ 2"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Engineering project"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Engineering project", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Engineering project"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Engineering project": eventData["Engineering project"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Engineering project"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Engineering project"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Engineering project"]["startTime"] + 25200))
                        place = eventData["Engineering project"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Engineering project"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    elif (event.message.text == "ลงสมัครกิจกรรมวิศวกรรมหุ่นยนต์และคอมพิวเตอร์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Robotics and Innovations"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Robotics and Innovations", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Robotics and Innovations"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Robotics and Innovations": eventData["Robotics and Innovations"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Robotics and Innovations"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Robotics and Innovations"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Robotics and Innovations"]["startTime"] + 25200))
                        place = eventData["Robotics and Innovations"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Robotics and Innovations"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)



    # Secondary Open House
    elif (event.message.text == "Open House ผจญภัยในรั้วม่วงทอง"):
        flex = functions.fmsg.secondaryOpenHouse()
        replyObj = FlexSendMessage(alt_text='Open House ผจญภัยในรั้วม่วงทอง', contents=flex)

    # Secondary Sci Open House
    elif (event.message.text == "ขุมทรัพย์นักวิทย์ของเลือดม่วงทอง"):
        flex = functions.fmsg.sciOpenHouse()
        replyObj = FlexSendMessage(alt_text='ขุมทรัพย์นักวิทย์ของเลือดม่วงทอง', contents=flex)

    # Secondary Open House
    elif (event.message.text == "ลงสมัคร Open House สายวิทย์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง"]["count"] >= 30:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {
                                "ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง": eventData["ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(
                                                 eventData["ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง"]["startTime"] + 25200))
                        place = eventData["ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "ขุมทรัพย์สายวิทย์ของเลือดม่วงทอง"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)


    # Secondary Art Open House
    elif (event.message.text == "ท่องโลกการเรียนรู้แห่งศิลปศาสตร์"):
        flex = functions.fmsg.artOpenHouse()
        replyObj = FlexSendMessage(alt_text='ท่องโลกการเรียนรู้แห่งศิลปศาสตร์', contents=flex)

    # ลงสมัคร Open House สายศิลป์
    elif (event.message.text == "ลงสมัคร Open House สายศิลป์"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["ท่องโลกการเรียนรู้แห่งสายศิลป์"]["count"] >= 30:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("ท่องโลกการเรียนรู้แห่งสายศิลป์", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["ท่องโลกการเรียนรู้แห่งสายศิลป์"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"ท่องโลกการเรียนรู้แห่งสายศิลป์": eventData["ท่องโลกการเรียนรู้แห่งสายศิลป์"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["ท่องโลกการเรียนรู้แห่งสายศิลป์"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "ท่องโลกการเรียนรู้แห่งสายศิลป์"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(
                                                 eventData["ท่องโลกการเรียนรู้แห่งสายศิลป์"]["startTime"] + 25200))
                        place = eventData["ท่องโลกการเรียนรู้แห่งสายศิลป์"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "ท่องโลกการเรียนรู้แห่งสายศิลป์"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    # Scholar Talks
    elif (event.message.text == "Scholar Talks"):
        flex = functions.fmsg.scholarTalks()
        replyObj = FlexSendMessage(alt_text='Scholar Talks', contents=flex)

    # Scholar Talks
    elif (event.message.text == "Scholar Talks 11 ม.ค."):
        flex = functions.fmsg.scholarTalks1()
        replyObj = FlexSendMessage(alt_text='Scholar Talks 11 ม.ค.', contents=flex)

    # ลงสมัคร Scholar Talk (1st Day-ช่วงเช้า-Dream)
    elif (event.message.text == "ลงสมัคร Scholar Talk (1st Day-ช่วงเช้า-Dream)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Scholar Talks 1"]["count"] >= 250:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Scholar Talks 1", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Scholar Talks 1"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Scholar Talks 1": eventData["Scholar Talks 1"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Scholar Talks 1"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Scholar Talks 1"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Scholar Talks 1"]["startTime"] + 25200))
                        place = eventData["Scholar Talks 1"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Scholar Talks 1"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)


    # ลงสมัคร Scholar Talk (1st Day-ช่วงเช้า-Go)
    elif (event.message.text == "ลงสมัคร Scholar Talk (1st Day-ช่วงเช้า-Go)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Scholar Talks 2"]["count"] >= 250:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Scholar Talks 2", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Scholar Talks 2"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Scholar Talks 2": eventData["Scholar Talks 2"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Scholar Talks 2"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Scholar Talks 2"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Scholar Talks 2"]["startTime"] + 25200))
                        place = eventData["Scholar Talks 2"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Scholar Talks 2"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    # ลงสมัคร Scholar Talk (1st Day-Building-our-dream)
    elif (event.message.text == "ลงสมัคร Scholar Talk (1st Day-Building-our-dream)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Scholar Talks 3"]["count"] >= 150:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Scholar Talks 3", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Scholar Talks 3"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Scholar Talks 3": eventData["Scholar Talks 3"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Scholar Talks 3"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Scholar Talks 3"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Scholar Talks 3"]["startTime"] + 25200))
                        place = eventData["Scholar Talks 3"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Scholar Talks 3"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    # ลงสมัคร Scholar Talk (2nd Day - คุณ Krit Tone)
    elif (event.message.text == "ลงสมัคร Scholar Talk (2nd Day - คุณ Krit Tone)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Scholar Talks 4"]["count"] >= 300:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Scholar Talks 4", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Scholar Talks 4"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Scholar Talks 4": eventData["Scholar Talks 4"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Scholar Talks 4"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Scholar Talks 4"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Scholar Talks 4"]["startTime"] + 25200))
                        place = eventData["Scholar Talks 4"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Scholar Talks 4"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)

    # ลงสมัคร Scholar Talk (2nd Day - คุณวิทย์)
    elif (event.message.text == "ลงสมัคร Scholar Talk (2nd Day - คุณวิทย์)"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Scholar Talks 5"]["count"] >= 150:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Scholar Talks 5", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Scholar Talks 5"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Scholar Talks 5": eventData["Scholar Talks 5"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Scholar Talks 5"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Scholar Talks 5"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Scholar Talks 5"]["startTime"] + 25200))
                        place = eventData["Scholar Talks 5"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Scholar Talks 5"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)


    # Scholar Talks
    elif (event.message.text == "Scholar Talks 12 ม.ค."):
        flex = functions.fmsg.scholarTalks2()
        replyObj = FlexSendMessage(alt_text='Scholar Talks 12 ม.ค.', contents=flex)


    # Student Council
    elif (event.message.text == "สภานักเรียน"):
        flex = functions.fmsg.studentCouncil()
        replyObj = FlexSendMessage(alt_text='สภานักเรียน', contents=flex)

    # Student Council
    elif (event.message.text == "เสวนาสภากาแฟร์"):
        flex = functions.fmsg.sc()
        replyObj = FlexSendMessage(alt_text='เสวนาสภากาแฟร์', contents=flex)

    # ลงสมัครเสวนาสภากาแฟร์
    elif (event.message.text == "ลงสมัครเสวนาสภากาแฟร์"):
        flex = functions.fmsg.warningFlex("ขณะนี้สภากาแฟร์ปิดการรับสมัครแล้ว ขออภัยในความไม่สะดวก")
        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

    # Student Council
    elif (event.message.text == "Common Goal"):
        flex = functions.fmsg.commonGoal()
        replyObj = FlexSendMessage(alt_text='Common Goal', contents=flex)

    # ลงสมัคร Common Goal
    elif (event.message.text == "ลงสมัคร Common Goal"):
        with open("data/events.json", "r", encoding="utf-8") as eventD:
            eventData = json.load(eventD)
            if eventData["Common Goal"]["count"] >= 25:
                flex = functions.fmsg.warningFlex("ไม่สามารถสมัครได้ เนื่องจากกิจกรรมนี้มีผู้สมัครเต็มแล้ว")
                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
            else:
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                    if functions.intersects.intersects("Common Goal", event.source.user_id):
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                    else:
                        with open("data/events.json", "w", encoding="utf-8") as eventD:
                            eventData["Common Goal"]["count"] += 1
                            eventD.write(str(eventData).replace("'", '"'))
                        token = secrets.token_hex(16)
                        while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                            token = secrets.token_hex(16)
                        img = qrcode.make(token)
                        img.save("staticFiles/images/qrCode/{}.png".format(token))
                        with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                            new_data = {"Common Goal": eventData["Common Goal"]}
                            userData["events"].update(new_data)
                            new_data = {"ticketToken": token}
                            userData["events"]["Common Goal"].update(new_data)
                            user.write(str(userData).replace("'", '"'))
                        eventName = "Common Goal"
                        firstName = userData["firstName"]
                        lastName = userData["lastName"]
                        school = userData["school"]
                        when = time.strftime("%d/%m/%Y %H:%M",
                                             time.localtime(eventData["Common Goal"]["startTime"] + 25200))
                        place = eventData["Common Goal"]["place"]
                        qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                        flex = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when, place, qr)

                        events = "Common Goal"
                        worksheet = spreadsheet.worksheet(events)
                        data = userData
                        if data["status"] == "0":
                            status = "นักเรียน"
                        elif data["status"] == "1":
                            status = "ครู"
                        elif data["status"] == "2":
                            status = "ผู้ปกครอง"

                        if data["degree"] == "0":
                            degree = "ประถม"
                        elif data["degree"] == "1":
                            degree = "ม.ต้น"
                        elif data["degree"] == "2":
                            degree = "ม.ปลาย"
                        row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                               data["school"],
                               status, degree, data["events"][events]["ticketToken"]]
                        worksheet.append_row(row)

                        replyObj = FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex)
    # Debug
    elif (event.message.text == "Debug"):
        replyObj = TextSendMessage(text=str(event))

    else:
        if (os.path.exists("teams/{}.json".format(event.message.text))):
            with open("teams/{}.json".format(event.message.text), 'r', encoding="utf8") as f:
                data = json.load(f)
                eventName = data["eventName"]
                with open("data/" + event.source.user_id + ".json", "r", encoding="utf-8") as user:
                    userData = json.load(user)
                if eventName == "Scholar Quiz วิชาการ":
                    if (userData["status"] == "0" and userData["degree"] == "0"):
                        if functions.intersects.intersects("Scholar Quiz วิชาการ", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            memberCount = len(data["members"])
                            if memberCount >= 2:
                                flex = functions.fmsg.warningFlex(
                                    "ทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                with open("teams/{}.json".format(event.message.text), "w", encoding="utf-8") as team:
                                    new_data = {event.source.user_id: userData["status"]}
                                    data["members"].update(new_data)
                                    team.write(str(data).replace("'", '"'))
                                with open("data/events.json", "r", encoding="utf-8") as ev:
                                    eventData = json.load(ev)
                                    token = secrets.token_hex(16)
                                    while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                        token = secrets.token_hex(16)
                                    img = qrcode.make(token)
                                    img.save("staticFiles/images/qrCode/{}.png".format(token))
                                    with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                        new_data = {"Scholar Quiz วิชาการ": eventData["Scholar Quiz วิชาการ"]}
                                        userData["events"].update(new_data)
                                        new_data = {"ticketToken": token}
                                        userData["events"]["Scholar Quiz วิชาการ"].update(new_data)
                                        new_data = {"teamToken": event.message.text}
                                        userData["events"]["Scholar Quiz วิชาการ"].update(new_data)
                                        user.write(str(userData).replace("'", '"'))
                                    flex1 = functions.fmsg.yourTeam(event.message.text)

                                    eventName = "Scholar Quiz วิชาการ"
                                    firstName = userData["firstName"]
                                    lastName = userData["lastName"]
                                    school = userData["school"]
                                    when = time.strftime("%d/%m/%Y %H:%M",
                                                         time.localtime(
                                                             eventData["Scholar Quiz วิชาการ"]["startTime"] + 25200))
                                    place = eventData["Scholar Quiz วิชาการ"]["place"]
                                    qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                    flex2 = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                      place,
                                                                      qr)

                                    events = "Scholar Quiz วิชาการ"
                                    worksheet = spreadsheet.worksheet(events)
                                    data = userData
                                    if data["status"] == "0":
                                        status = "นักเรียน"
                                    elif data["status"] == "1":
                                        status = "ครู"
                                    elif data["status"] == "2":
                                        status = "ผู้ปกครอง"

                                    if data["degree"] == "0":
                                        degree = "ประถม"
                                    elif data["degree"] == "1":
                                        degree = "ม.ต้น"
                                    elif data["degree"] == "2":
                                        degree = "ม.ปลาย"
                                    row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                           data["school"],
                                           status, degree, data["events"][events]["ticketToken"],
                                           data["events"][events]["teamToken"]]
                                    worksheet.append_row(row)

                                    replyObj = [FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex1),
                                                FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex2)]

                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                elif eventName == "แข่งหมากล้อม":
                    if ((userData["status"] == "0" and userData["degree"] == "0") or userData["status"] == "1"):
                        if functions.intersects.intersects("แข่งหมากล้อม", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            memberCount = len(data["members"])
                            if memberCount >= 6:
                                flex = functions.fmsg.warningFlex(
                                    "ทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                if userData["status"] == "0":
                                    studentCount = 0
                                    for users in data["members"]:
                                        if data["members"][users] == "0":
                                            studentCount += 1
                                        if studentCount >= 5:
                                            flex = functions.fmsg.warningFlex(
                                                "จำนวนนักเรียนในทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                            line_bot_api.reply_message(event.reply_token, replyObj)
                                            return
                                else:
                                    teacherCount = 0
                                    for users in data["members"]:
                                        if data["members"][users] == "1":
                                            teacherCount += 1
                                        if teacherCount >= 1:
                                            flex = functions.fmsg.warningFlex(
                                                "จำนวนคุณครูในทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                            line_bot_api.reply_message(event.reply_token, replyObj)
                                            return
                                with open("teams/{}.json".format(event.message.text), "w", encoding="utf-8") as team:
                                    new_data = {event.source.user_id: userData["status"]}
                                    data["members"].update(new_data)
                                    team.write(str(data).replace("'", '"'))
                                with open("data/events.json", "r", encoding="utf-8") as ev:
                                    eventData = json.load(ev)
                                    token = secrets.token_hex(16)
                                    while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                        token = secrets.token_hex(16)
                                    img = qrcode.make(token)
                                    img.save("staticFiles/images/qrCode/{}.png".format(token))
                                    with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                        new_data = {"แข่งหมากล้อม": eventData["แข่งหมากล้อม"]}
                                        userData["events"].update(new_data)
                                        new_data = {"ticketToken": token}
                                        userData["events"]["แข่งหมากล้อม"].update(new_data)
                                        new_data = {"teamToken": event.message.text}
                                        userData["events"]["แข่งหมากล้อม"].update(new_data)
                                        user.write(str(userData).replace("'", '"'))
                                    flex1 = functions.fmsg.yourTeam(event.message.text)

                                    eventName = "แข่งหมากล้อม"
                                    firstName = userData["firstName"]
                                    lastName = userData["lastName"]
                                    school = userData["school"]
                                    when = time.strftime("%d/%m/%Y %H:%M",
                                                         time.localtime(
                                                             eventData["แข่งหมากล้อม"]["startTime"] + 25200))
                                    place = eventData["แข่งหมากล้อม"]["place"]
                                    qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                    flex2 = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                      place,
                                                                      qr)

                                    events = "แข่งหมากล้อม"
                                    worksheet = spreadsheet.worksheet(events)
                                    data = userData
                                    if data["status"] == "0":
                                        status = "นักเรียน"
                                    elif data["status"] == "1":
                                        status = "ครู"
                                    elif data["status"] == "2":
                                        status = "ผู้ปกครอง"

                                    if data["degree"] == "0":
                                        degree = "ประถม"
                                    elif data["degree"] == "1":
                                        degree = "ม.ต้น"
                                    elif data["degree"] == "2":
                                        degree = "ม.ปลาย"
                                    row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                           data["school"],
                                           status, degree, data["events"][events]["ticketToken"],
                                           data["events"][events]["teamToken"]]
                                    worksheet.append_row(row)

                                    replyObj = [FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex1),
                                                FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex2)]
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                elif eventName == "CANSAT":
                    if (userData["status"] == "0" and userData["degree"] == "2"):
                        if functions.intersects.intersects("CANSAT", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            memberCount = len(data["members"])
                            if memberCount >= 3:
                                flex = functions.fmsg.warningFlex(
                                    "ทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                with open("teams/{}.json".format(event.message.text), "w", encoding="utf-8") as team:
                                    new_data = {event.source.user_id: userData["status"]}
                                    data["members"].update(new_data)
                                    team.write(str(data).replace("'", '"'))
                                with open("data/events.json", "r", encoding="utf-8") as ev:
                                    eventData = json.load(ev)
                                    token = secrets.token_hex(16)
                                    while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                        token = secrets.token_hex(16)
                                    img = qrcode.make(token)
                                    img.save("staticFiles/images/qrCode/{}.png".format(token))
                                    with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                        new_data = {"CANSAT": eventData["CANSAT"]}
                                        userData["events"].update(new_data)
                                        new_data = {"ticketToken": token}
                                        userData["events"]["CANSAT"].update(new_data)
                                        new_data = {"teamToken": event.message.text}
                                        userData["events"]["CANSAT"].update(new_data)
                                        user.write(str(userData).replace("'", '"'))
                                    flex1 = functions.fmsg.yourTeam(event.message.text)

                                    eventName = "CANSAT"
                                    firstName = userData["firstName"]
                                    lastName = userData["lastName"]
                                    school = userData["school"]
                                    when = time.strftime("%d/%m/%Y %H:%M",
                                                         time.localtime(
                                                             eventData["CANSAT"]["startTime"] + 25200))
                                    place = eventData["CANSAT"]["place"]
                                    qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                    flex2 = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                      place,
                                                                      qr)

                                    events = "CANSAT"
                                    worksheet = spreadsheet.worksheet(events)
                                    data = userData
                                    if data["status"] == "0":
                                        status = "นักเรียน"
                                    elif data["status"] == "1":
                                        status = "ครู"
                                    elif data["status"] == "2":
                                        status = "ผู้ปกครอง"

                                    if data["degree"] == "0":
                                        degree = "ประถม"
                                    elif data["degree"] == "1":
                                        degree = "ม.ต้น"
                                    elif data["degree"] == "2":
                                        degree = "ม.ปลาย"
                                    row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                           data["school"],
                                           status, degree, data["events"][events]["ticketToken"],
                                           data["events"][events]["teamToken"]]
                                    worksheet.append_row(row)

                                    replyObj = [FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex1),
                                                FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex2)]

                elif eventName == "เกมการเรียนรู้ธุรกิจ":
                    if ((userData["status"] == "0" and userData["degree"] == "1") or (
                            userData["status"] == "1" and userData["degree"] == "1")):
                        if functions.intersects.intersects("เกมการเรียนรู้ธุรกิจ", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            memberCount = len(data["members"])
                            if memberCount >= 6:
                                flex = functions.fmsg.warningFlex(
                                    "ทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                if userData["status"] == "0":
                                    studentCount = 0
                                    for users in data["members"]:
                                        if data["members"][users] == "0":
                                            studentCount += 1
                                        if studentCount >= 3:
                                            flex = functions.fmsg.warningFlex(
                                                "จำนวนนักเรียนในทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                            line_bot_api.reply_message(event.reply_token, replyObj)
                                            return
                                else:
                                    teacherCount = 0
                                    for users in data["members"]:
                                        if data["members"][users] == "1":
                                            teacherCount += 1
                                        if teacherCount >= 1:
                                            flex = functions.fmsg.warningFlex(
                                                "จำนวนคุณครูในทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                            line_bot_api.reply_message(event.reply_token, replyObj)
                                            return
                                with open("teams/{}.json".format(event.message.text), "w", encoding="utf-8") as team:
                                    new_data = {event.source.user_id: userData["status"]}
                                    data["members"].update(new_data)
                                    team.write(str(data).replace("'", '"'))
                                with open("data/events.json", "r", encoding="utf-8") as ev:
                                    eventData = json.load(ev)
                                    token = secrets.token_hex(16)
                                    while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                        token = secrets.token_hex(16)
                                    img = qrcode.make(token)
                                    img.save("staticFiles/images/qrCode/{}.png".format(token))
                                    with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                        new_data = {"เกมการเรียนรู้ธุรกิจ": eventData["เกมการเรียนรู้ธุรกิจ"]}
                                        userData["events"].update(new_data)
                                        new_data = {"ticketToken": token}
                                        userData["events"]["เกมการเรียนรู้ธุรกิจ"].update(new_data)
                                        new_data = {"teamToken": event.message.text}
                                        userData["events"]["เกมการเรียนรู้ธุรกิจ"].update(new_data)
                                        user.write(str(userData).replace("'", '"'))
                                    flex1 = functions.fmsg.yourTeam(event.message.text)

                                    eventName = "เกมการเรียนรู้ธุรกิจ"
                                    firstName = userData["firstName"]
                                    lastName = userData["lastName"]
                                    school = userData["school"]
                                    when = time.strftime("%d/%m/%Y %H:%M",
                                                         time.localtime(
                                                             eventData["เกมการเรียนรู้ธุรกิจ"]["startTime"] + 25200))
                                    place = eventData["เกมการเรียนรู้ธุรกิจ"]["place"]
                                    qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                    flex2 = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                      place,
                                                                      qr)

                                    events = "เกมการเรียนรู้ธุรกิจ"
                                    worksheet = spreadsheet.worksheet(events)
                                    data = userData
                                    if data["status"] == "0":
                                        status = "นักเรียน"
                                    elif data["status"] == "1":
                                        status = "ครู"
                                    elif data["status"] == "2":
                                        status = "ผู้ปกครอง"

                                    if data["degree"] == "0":
                                        degree = "ประถม"
                                    elif data["degree"] == "1":
                                        degree = "ม.ต้น"
                                    elif data["degree"] == "2":
                                        degree = "ม.ปลาย"
                                    row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                           data["school"],
                                           status, degree, data["events"][events]["ticketToken"],
                                           data["events"][events]["teamToken"]]
                                    worksheet.append_row(row)

                                    replyObj = [FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex1),
                                                FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex2)]
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                elif eventName == "English Singing Contest":
                    if ((userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1"):
                        if functions.intersects.intersects("English Singing Contest", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            memberCount = len(data["members"])
                            if memberCount >= 2:
                                flex = functions.fmsg.warningFlex(
                                    "ทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                if userData["status"] == "0":
                                    studentCount = 0
                                    for users in data["members"]:
                                        if data["members"][users] == "0":
                                            studentCount += 1
                                        if studentCount >= 1:
                                            flex = functions.fmsg.warningFlex(
                                                "จำนวนนักเรียนในทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                            line_bot_api.reply_message(event.reply_token, replyObj)
                                            return
                                else:
                                    teacherCount = 0
                                    for users in data["members"]:
                                        if data["members"][users] == "1":
                                            teacherCount += 1
                                        if teacherCount >= 1:
                                            flex = functions.fmsg.warningFlex(
                                                "จำนวนคุณครูในทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                            line_bot_api.reply_message(event.reply_token, replyObj)
                                            return
                                with open("teams/{}.json".format(event.message.text), "w", encoding="utf-8") as team:
                                    new_data = {event.source.user_id: userData["status"]}
                                    data["members"].update(new_data)
                                    team.write(str(data).replace("'", '"'))
                                with open("data/events.json", "r", encoding="utf-8") as ev:
                                    eventData = json.load(ev)
                                    token = secrets.token_hex(16)
                                    while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                        token = secrets.token_hex(16)
                                    img = qrcode.make(token)
                                    img.save("staticFiles/images/qrCode/{}.png".format(token))
                                    with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                        new_data = {"English Singing Contest": eventData["English Singing Contest"]}
                                        userData["events"].update(new_data)
                                        new_data = {"ticketToken": token}
                                        userData["events"]["English Singing Contest"].update(new_data)
                                        new_data = {"teamToken": event.message.text}
                                        userData["events"]["English Singing Contest"].update(new_data)
                                        user.write(str(userData).replace("'", '"'))
                                    flex1 = functions.fmsg.yourTeam(event.message.text)

                                    eventName = "English Singing Contest"
                                    firstName = userData["firstName"]
                                    lastName = userData["lastName"]
                                    school = userData["school"]
                                    when = time.strftime("%d/%m/%Y %H:%M",
                                                         time.localtime(
                                                             eventData["English Singing Contest"]["startTime"] + 25200))
                                    place = eventData["English Singing Contest"]["place"]
                                    qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                    flex2 = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                      place,
                                                                      qr)

                                    events = "English Singing Contest"
                                    worksheet = spreadsheet.worksheet(events)
                                    data = userData
                                    if data["status"] == "0":
                                        status = "นักเรียน"
                                    elif data["status"] == "1":
                                        status = "ครู"
                                    elif data["status"] == "2":
                                        status = "ผู้ปกครอง"

                                    if data["degree"] == "0":
                                        degree = "ประถม"
                                    elif data["degree"] == "1":
                                        degree = "ม.ต้น"
                                    elif data["degree"] == "2":
                                        degree = "ม.ปลาย"
                                    row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                           data["school"],
                                           status, degree, data["events"][events]["ticketToken"],
                                           data["events"][events]["teamToken"]]
                                    worksheet.append_row(row)

                                    replyObj = [FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex1),
                                                FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex2)]
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

                elif eventName == "เปลี่ยนรบเป็นรัก":
                    if ((userData["status"] == "0" and userData["degree"] == "2") or userData["status"] == "1"):
                        if functions.intersects.intersects("เปลี่ยนรบเป็นรัก", event.source.user_id):
                            flex = functions.fmsg.warningFlex(
                                "ไม่สามารถสมัครได้ เนื่องจากคุณได้ลงกิจกรรมที่มีเวลาใกล้เคียง หรือ ซ้อนทับกับกิจกรรมนี้")
                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                        else:
                            memberCount = len(data["members"])
                            if memberCount >= 5:
                                flex = functions.fmsg.warningFlex(
                                    "ทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                            else:
                                if userData["status"] == "0":
                                    studentCount = 0
                                    for users in data["members"]:
                                        if data["members"][users] == "0":
                                            studentCount += 1
                                        if studentCount >= 4:
                                            flex = functions.fmsg.warningFlex(
                                                "จำนวนนักเรียนในทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                            line_bot_api.reply_message(event.reply_token, replyObj)
                                            return
                                else:
                                    teacherCount = 0
                                    for users in data["members"]:
                                        if data["members"][users] == "1":
                                            teacherCount += 1
                                        if teacherCount >= 1:
                                            flex = functions.fmsg.warningFlex(
                                                "จำนวนคุณครูในทีมของคุณเต็มแล้ว ถ้าหากคิดว่าเป็นข้อผิดพลาดของระบบ กรุณาติดต่อเจ้าหน้าที่ผ่านทางแชทนี้")
                                            replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)
                                            line_bot_api.reply_message(event.reply_token, replyObj)
                                            return
                                with open("teams/{}.json".format(event.message.text), "w", encoding="utf-8") as team:
                                    new_data = {event.source.user_id: userData["status"]}
                                    data["members"].update(new_data)
                                    team.write(str(data).replace("'", '"'))
                                with open("data/events.json", "r", encoding="utf-8") as ev:
                                    eventData = json.load(ev)
                                    token = secrets.token_hex(16)
                                    while (os.path.exists("staticFiles/images/qrCode/{}.png".format(token))):
                                        token = secrets.token_hex(16)
                                    img = qrcode.make(token)
                                    img.save("staticFiles/images/qrCode/{}.png".format(token))
                                    with open("data/" + event.source.user_id + ".json", "w", encoding="utf-8") as user:
                                        new_data = {"เปลี่ยนรบเป็นรัก": eventData["เปลี่ยนรบเป็นรัก"]}
                                        userData["events"].update(new_data)
                                        new_data = {"ticketToken": token}
                                        userData["events"]["เปลี่ยนรบเป็นรัก"].update(new_data)
                                        new_data = {"teamToken": event.message.text}
                                        userData["events"]["เปลี่ยนรบเป็นรัก"].update(new_data)
                                        user.write(str(userData).replace("'", '"'))
                                    flex1 = functions.fmsg.yourTeam(event.message.text)

                                    eventName = "เปลี่ยนรบเป็นรัก"
                                    firstName = userData["firstName"]
                                    lastName = userData["lastName"]
                                    school = userData["school"]
                                    when = time.strftime("%d/%m/%Y %H:%M",
                                                         time.localtime(
                                                             eventData["เปลี่ยนรบเป็นรัก"]["startTime"] + 25200))
                                    place = eventData["เปลี่ยนรบเป็นรัก"]["place"]
                                    qr = "https://bccscholar.com/staticFiles/images/qrCode/{}.png".format(token)
                                    flex2 = functions.fmsg.ticketFlex(eventName, firstName, lastName, school, when,
                                                                      place,
                                                                      qr)

                                    events = "เปลี่ยนรบเป็นรัก"
                                    worksheet = spreadsheet.worksheet(events)
                                    data = userData
                                    if data["status"] == "0":
                                        status = "นักเรียน"
                                    elif data["status"] == "1":
                                        status = "ครู"
                                    elif data["status"] == "2":
                                        status = "ผู้ปกครอง"

                                    if data["degree"] == "0":
                                        degree = "ประถม"
                                    elif data["degree"] == "1":
                                        degree = "ม.ต้น"
                                    elif data["degree"] == "2":
                                        degree = "ม.ปลาย"
                                    row = [data["firstName"], data["lastName"], data["phone"], data["email"],
                                           data["school"],
                                           status, degree, data["events"][events]["ticketToken"],
                                           data["events"][events]["teamToken"]]
                                    worksheet.append_row(row)

                                    replyObj = [FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex1),
                                                FlexSendMessage(alt_text='ตั๋วของคุณ', contents=flex2)]
                    else:
                        flex = functions.fmsg.warningFlex(
                            "ไม่สามารถสมัครได้ เนื่องจากคุณสมบัติไม่ตรงกับเงื่อนไขของกิจกรรมนี้")
                        replyObj = FlexSendMessage(alt_text='ไม่สามารถสมัครได้', contents=flex)

        # ทีมของฉัน
        elif (event.message.text == "ทีมของฉัน"):
            c = 0
            replyObj = []
            with open('data/{}.json'.format(event.source.user_id), 'r', encoding="utf8") as user:
                userData = json.load(user)
                for events in userData["events"]:
                    with open('msgJson/yourTeam.json', 'r', encoding="utf8") as f:
                        flex = json.load(f)
                    if "teamToken" in userData["events"][events]:
                        c += 1
                        with open('teams/{}.json'.format(userData["events"][events]["teamToken"]), 'r',
                                  encoding="utf8") as data:
                            data = json.load(data)
                            flex["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = \
                                userData["events"][events]["teamToken"]
                            flex["body"]["contents"][1]["contents"][1]["contents"][1]["text"] = data["eventName"]
                            for members in data["members"]:
                                with open('data/{}.json'.format(members), 'r', encoding="utf8") as user:
                                    userData = json.load(user)
                                    new_data = f"""{{"type": "box", "layout": "baseline", "spacing": "sm", "contents": [{{"type": "text", "text": "สมาชิก", "color": "#aaaaaa", "size": "sm", "flex": 1}}, {{"type": "text", "text": "{userData["firstName"]} {userData["lastName"]}", "wrap": true, "color": "#666666", "size": "sm", "flex": 4}}]}}"""
                                    new_data = json.loads(new_data)
                                    flex["body"]["contents"][1]["contents"].append(new_data)
                        line_bot_api.push_message(event.source.user_id,
                                                  FlexSendMessage(alt_text='ทีมของคุณ', contents=flex))
                if c == 0:
                    flex = functions.fmsg.warningFlex(
                        "คุณยังไม่มีทีม")
                    replyObj = FlexSendMessage(alt_text='คุณยังไม่มีทีม', contents=flex)


        # ตั๋วของคุณ
        elif (event.message.text == "ตั๋วของฉัน"):
            replyObj = []
            with open('data/{}.json'.format(event.source.user_id), 'r', encoding="utf8") as user:
                userData = json.load(user)
                if len(userData["events"]) == 0:
                    flex = functions.fmsg.warningFlex(
                        "คุณยังไม่ได้ลงสมัครกิจกรรม")
                    replyObj = FlexSendMessage(alt_text='คุณยังไม่ได้ลงสมัครกิจกรรม', contents=flex)
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

    # send the reply message
    line_bot_api.reply_message(event.reply_token, replyObj)


# start the website
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=443, ssl_context=("keys/ssl/cert.pem", "keys/ssl/key.key"))
