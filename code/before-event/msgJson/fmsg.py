import json


# Warning
def warningFlex(reason):
    with open('msgJson/warningFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
        flex["body"]["contents"][2]["contents"][0]["contents"][0]["contents"][0]["text"] = reason
    return flex


# Confirmation
def confirmationFlex(name):
    with open('msgJson/confirmationFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
        flex["body"]["contents"][2]["contents"][0]["contents"][0]["contents"][0][
            "text"] = "คุณยืนยันที่จะเข้าร่วมกิจกรรม " + name + " หรือไม่"
        flex["footer"]["contents"][0]["action"]["text"] = "ยืนยันเข้าร่วม " + name
    return flex


# Team Option
def teamOptionFlex(name):
    with open('msgJson/teamOption.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
        flex["body"]["contents"][0]["text"] = name
        flex["footer"]["contents"][1]["action"]["text"] = "สร้างทีมใหม่ {}".format(name)
        flex["footer"]["contents"][2]["action"]["text"] = "เข้าร่วมทีมที่มีอยู่แล้ว {}".format(name)
    return flex

# Maintenance
def maintenance():
    with open('msgJson/maintenance.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex



# Ticket
def ticketFlex(eventName, firstName, lastName, school, when, place, qr):
    with open('msgJson/ticket.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
        flex["body"]["contents"][0]["text"] = eventName
        flex["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = firstName
        flex["body"]["contents"][1]["contents"][1]["contents"][1]["text"] = lastName
        flex["body"]["contents"][1]["contents"][2]["contents"][1]["text"] = school
        flex["body"]["contents"][1]["contents"][3]["contents"][1]["text"] = when
        flex["body"]["contents"][1]["contents"][4]["contents"][1]["text"] = place
        flex["body"]["contents"][2]["contents"][0]["url"] = qr
    return flex


# My Ticket
def myTicketFlex():
    with open('msgJson/ticket.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Cancel
def cancelFlex():
    with open('msgJson/cancelFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Primary

# Primary Section List
def primarySectionListFlex():
    with open('msgJson/primary/sectionListFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Primary Open House
def primaryOpenHouse():
    with open('msgJson/primary/openHouse.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Primary Open House 8:00
def primaryOpenHouse8():
    with open('msgJson/primary/openHouse8.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Primary Open House 12:00
def primaryOpenHouse12():
    with open('msgJson/primary/openHouse12.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Scholar Quiz
def scholarQuiz():
    with open('msgJson/primary/scholarQuiz.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Go
def primaryGo():
    with open('msgJson/primary/go.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Secondary

# Secondary Section List
def sectionListFlex():
    with open('msgJson/secondary/sectionListFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Secondary Scholar Competitions
def scholarCompetition():
    with open('msgJson/secondary/scholarCompetition/scholarCompetition.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# ประกวดวาดภาพระบายสี
def artFlex():
    with open('msgJson/secondary/scholarCompetition/artFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# ภาษาไทยในฐานะภาษาต่างประเทศ
def thaiFlex():
    with open('msgJson/secondary/scholarCompetition/thaiFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# HomeCourt
def peFlex():
    with open('msgJson/secondary/scholarCompetition/peFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# CANSAT
def sciFlex():
    with open('msgJson/secondary/scholarCompetition/sciFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Soft Cookie
def workFlex():
    with open('msgJson/secondary/scholarCompetition/workFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# เปลี่ยนรบเป็นรัก
def socialFlex():
    with open('msgJson/secondary/scholarCompetition/socialFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# English Singing Contest
def engFlex():
    with open('msgJson/secondary/scholarCompetition/engFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# เกมการเรียนรู้ธุรกิจ
def mathFlex():
    with open('msgJson/secondary/scholarCompetition/mathFlex.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Secondary Demonstration
def secondaryDemonstration():
    with open('msgJson/secondary/demonstration/demonstration.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Secondary Open House
def secondaryOpenHouse():
    with open('msgJson/secondary/openHouse/openHouse.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Secondary Science Open House
def sciOpenHouse():
    with open('msgJson/secondary/openHouse/sciOpenHouse.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Secondary Art Open House
def artOpenHouse():
    with open('msgJson/secondary/openHouse/artOpenHouse.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Scholar Talks
def scholarTalks():
    with open('msgJson/secondary/scholarTalks/scholarTalks.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Scholar Talks
def scholarTalks1():
    with open('msgJson/secondary/scholarTalks/scholarTalks1.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Scholar Talks
def scholarTalks2():
    with open('msgJson/secondary/scholarTalks/scholarTalks2.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Student Council
def studentCouncil():
    with open('msgJson/secondary/studentCouncil/scSection.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# เสวนาสภากาแฟร์
def sc():
    with open('msgJson/secondary/studentCouncil/studentCouncil.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Common Goal
def commonGoal():
    with open('msgJson/secondary/studentCouncil/commonGoal.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
    return flex


# Team
def team(teamToken, eventName, creator):
    with open('msgJson/team.json', 'r', encoding="utf8") as f:
        flex = json.loads(f.read())
        flex["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = teamToken
        flex["body"]["contents"][1]["contents"][1]["contents"][1]["text"] = eventName
        flex["body"]["contents"][1]["contents"][2]["contents"][1]["text"] = creator

    return flex


def yourTeam(teamToken):
    with open('msgJson/yourTeam.json', 'r', encoding="utf8") as f:
        with open('teams/{}.json'.format(teamToken), 'r', encoding="utf8") as data:
            data = json.load(data)
            flex = json.loads(f.read())
            flex["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = teamToken
            flex["body"]["contents"][1]["contents"][1]["contents"][1]["text"] = data["eventName"]
            for members in data["members"]:
                with open('data/{}.json'.format(members), 'r', encoding="utf8") as user:
                    userData = json.load(user)
                    new_data = f"""{{"type": "box", "layout": "baseline", "spacing": "sm", "contents": [{{"type": "text", "text": "สมาชิก", "color": "#aaaaaa", "size": "sm", "flex": 1}}, {{"type": "text", "text": "{userData["firstName"]} {userData["lastName"]}", "wrap": true, "color": "#666666", "size": "sm", "flex": 4}}]}}"""
                    new_data = json.loads(new_data)
                    flex["body"]["contents"][1]["contents"].append(new_data)
    return flex
