from flask import Flask, request, redirect, Response
from pymongo import MongoClient
from twilio.twiml.messaging_response import Message, MessagingResponse
import re
import datetime
import ssl

import os



app = Flask(__name__)

team_names = {}

# Enter the answer to the puzzle. No whitespace allowed
answers = {
    "1": "WANE",
    "2": "HUNGRY",
    "3": "RUNNING",
    "4": "ZOO",
    "5": "GRASS",
    "6": "JUPITER",
    "7": "SUFFOCATE",
    "8": "PITCHFORK",
    "META": "UNDERWATERBASKETWEAVING"
}

# Enter the flavor text given for a correct answer
storyline = {
    "1": "",
    "2": "",
    "3": "",
    "4": "",
    "5": "",
    "6": "",
    "7": "",
    "8": "",
}

client = MongoClient("mongodb+srv://aquaadmin:aqua@cluster0.9lq84.mongodb.net/aqua?retryWrites=true&w=majority", ssl_cert_reqs=ssl.CERT_NONE)
print("Available dbs (need aqua): ", client.list_database_names())

db = client.aqua #make sure to set up a db called aqua beforehand
teams = db.teams
subans = db.subans

stock_messages = {
    "Welcome": "Welcome to MIT, {team_name}. Go find some puzzles in yellow envelopes! Start texting us with answers [PUZZLE NO.] [SOLUTION], for example,'1 balloon' if the answer for puzzle 1 was balloon.",
    "Help": "Text [PUZZLE NO.] [SOLUTION], like '1 balloon', and we'll let you know if you are correct. Read the puzzle solving tips in the intro doc! If you need more help, find a staff member wearing a hat.",
    "Name Already Taken": "Sorry, the name '{team_name_new}' is already taken. Text 'yes' to accept the name '{team_name_temp}' or text to create a new one",
    "Name Already Taken First": "Sorry, the name '{team_name_new}' is already taken. Text to create a new one",
    "Name Too Long": "Sorry, please keep your name under 30 characters. Text 'yes' to accept the name '{team_name_temp}' or text to create a new one",
    "Name Too Long First": "Sorry, please keep your name under 30 characters. Text to create a new one",
    "Confirm Name": "Welcome to the Aquarium Puzzlehunt! Text 'yes' to accept the name '{team_name_temp}' or text to create a new one",
    "Parse Error": "I'm sorry, we didn't understand '{text}'. Please text answers in the format [PUZZLE NO.] [SOLUTION], like '1 balloon'",
    "Problem Not Exists": "We don't have a puzzle {puzzle_number}...",
    "Correct": "Your answer of {answer} for puzzle {puzzle_number} is Correct!{storyline}",
    "Incorrect": "Sorry, your answer {answer} for puzzle {puzzle_number} was incorrect. Please try again.",
    "Already Answered": "You've already completed puzzle {puzzle_number}, go find another one!",
    "Final Puzzle": "Your answer of {answer} is Correct!{storyline} You have solved {num_solved}/8 puzzles! Come to the front desk to receive the meta puzzle! To submit the meta, text 'meta' and then the answer",
    "Meta Correct": "Congratulations {team_name}, {answer} was correct! Go see the Diving Supervisors at the front desk!",
    "Meta Answered": "You've completed the puzzle hunt! Congratulations :)",
    "Meta Incorrect": "Sorry, {answer} was wrong. Please try again."
}

special_messages = {
    "1": {
        "NAMEOF": "Keep going! What shapes do those letters make?",
        "NAMEOFAUTHOR": "You're close! Who is the author of the puzzle?",
        "AUTHOR": "Keep going! Who is the author of the puzzle?",
        "WAYNE": "One more step! Try applying the puzzle mechanic again."
    },
    "2": {
        "ONEISANGRY": "Almost! The other is...?"
    }
}

parse_length = len(stock_messages["Parse Error"].format(text=""))
name_length = len(stock_messages["Welcome"].format(team_name=""))
reDigits = re.compile(r"^\d+$")
reEndWhitespace = re.compile(r"\s+$")
reBeginWhitespace = re.compile(r"^\s+")
reWhitespace = re.compile(r"\s+")

def parse_error(command):
    if len(command) + parse_length < 160:
        return stock_messages["Parse Error"].format(text=command)
    else:
        return stock_messages["Parse Error"].format(text=(command[:160-parse_length-4] + " ..."))

def parse_puzzle_answers(team,from_number,root,leaf):
    if root in answers:
        if root in team[u'Correct']:
            return stock_messages["Already Answered"].format(puzzle_number=root)
        elif leaf == answers[root].upper():
            teams.update({"Number":from_number},{"$push":{"Correct":root},"$set":{"SolveTimes."+root:datetime.datetime.utcnow()}})
            subans.update({"_Puzzle":root},{"$inc":{leaf:1},"$addToSet":{"_Answers":leaf}},True)

            if len(team[u'Correct']) >= 6:
                return stock_messages["Final Puzzle"].format(puzzle_number=root, num_solved=len(team[u'Correct'])+1, answer=leaf,  storyline=storyline[root], team_name=team[u'Name'])
            else:
                return stock_messages["Correct"].format(puzzle_number=root, answer=leaf, storyline=storyline[root])
        elif root in special_messages and leaf in special_messages[root]:
            subans.update({"_Puzzle":root},{"$inc":{leaf:1},"$addToSet":{"_Answers":leaf}},True)
            return special_messages[root][leaf]
        else:
            subans.update({"_Puzzle":root},{"$inc":{leaf:1},"$addToSet":{"_Answers":leaf}},True)
            return stock_messages["Incorrect"].format(puzzle_number=root, answer=leaf)
    else:
        return stock_messages["Problem Not Exists"].format(puzzle_number=root)

@app.route("/answers.txt")
def show_answers():
    ret = ""
    for ans in subans.find():
        ret += ans[u'_Puzzle'] + "\r\n"
        ret += "\r\n".join(['"{}",{}'.format(k,ans[k]) for k in ans[u'_Answers']])
        ret += "\r\n"

    return Response(ret, mimetype='text/plain')

@app.route("/solvedpuzzles.txt")
def show_stats():
    total_solved = [0]*10
    puzzles_solved = [0]*9
    for team in teams.find():
        for i in range(10):
            if len(team[u'Correct']) == i:
                total_solved[i] += 1
        for i in range(8):
            if str(i+1) in team[u'Correct']:
                puzzles_solved[i] += 1
        if "META" in team[u'Correct']:
            puzzles_solved[8] += 1

    ret = "# of Teams by total # of problems solved:\r\n"
    for i in range(10):
        ret += str(i) + ": " + str(total_solved[i]) + "\r\n"

    ret += "\r\n# of puzzle solves by puzzle:\r\n"
    for i in range(8):
        ret += str(i) + ": " + str(puzzles_solved[i]) + "\r\n"

    ret += "META: " + str(puzzles_solved[8])

    return Response(ret, mimetype='text/plain')

@app.route("/allteams.txt")
def show_teams():
    ret = ""
    for team in teams.find():
        if "StartTime" in team:
            if "META" in team[u'Correct']:
                ret+= "FINISHED(" + str(team['SolveTimes']['META']-team[u'StartTime']) +") "
            else:
                ret+= "ELAPSED(" + str(datetime.datetime.utcnow()-team[u'StartTime']) +") "
            ret += '"' + team[u'TempName'] + '",' + ",".join(team[u'Correct']) +" "+ team[u'StartTime'].strftime("%H:%M:%S") + "\r\n"
    return Response(ret, mimetype='text/plain')

@app.route("/", methods=['GET', 'POST'])
def hello_monkey():

    from_number = request.values.get('From', None)
    command = reBeginWhitespace.sub('', reEndWhitespace.sub('', request.values.get('Body', None)))

    tokens = command.split(None, 1)

    team = teams.find_one({"Number":from_number})

    message = parse_error(command)

    if team == None:
        if len(command) < 31:
            if teams.find_one({"$or":[{"Name":command}, {"TempName":command}]}) == None:
                message = stock_messages["Confirm Name"].format(team_name_temp=command)
                teams.insert({"Number":from_number,"TempName":command,"Correct":list()})
            else:
                message = stock_messages["Name Already Taken First"].format(team_name_new=command)
        else:
            message = stock_messages["Name Too Long First"]
    elif "Name" not in team:
        if tokens[0].upper() == 'YES':
            teams.update({"Number":from_number},{"$set":{"Name":team[u'TempName']}})
            teams.update({"Number":from_number},{"$set":{"StartTime":datetime.datetime.utcnow()}})
            message = stock_messages["Welcome"].format(team_name=team[u'TempName'])
        elif len(command) < 31:
            if teams.find_one({"$or":[{"Name":command}, {"TempName":command}]}) == None:
                teams.update({"Number":from_number},{"$set":{"TempName":command}})
                message = stock_messages["Confirm Name"].format(team_name_temp=command)
            else:
                message = stock_messages["Name Already Taken"].format(team_name_new=command,team_name_temp=team[u'TempName'])
        else:
            message = stock_messages["Name Too Long"].format(team_name_temp=team[u'TempName'])
    elif len(tokens) == 2:
        root,leaf = tokens
        if reDigits.search(root) != None:
            message = parse_puzzle_answers(team, from_number, root, reWhitespace.sub('',leaf).upper())
        elif root.upper() == "META":
            if "META" in team[u'Correct']:
                message = stock_messages["Meta Answered"]
            else:
                if reWhitespace.sub('',leaf).upper() == answers["META"].upper():
                    message = stock_messages["Meta Correct"].format(answer=reWhitespace.sub('',leaf).upper(), team_name=team[u'Name'])
                    teams.update({"Number":from_number},{"$push":{"Correct":root.upper()},"$set":{"SolveTimes.META":datetime.datetime.utcnow()}})
                    subans.update({"_Puzzle":"META"},{"$inc":{leaf:1},"$addToSet":{"_Answers":leaf}},True)
                else:
                    message = stock_messages["Meta Incorrect"].format(answer=reWhitespace.sub('',leaf).upper())
                    subans.update({"_Puzzle":"META"},{"$inc":{leaf:1},"$addToSet":{"_Answers":leaf}},True)
        elif root.upper() == "PENCIL-REMOVE-TEAM":
            teams.remove({"Name":leaf})
            message = "Removed " + leaf

    elif len(tokens) == 1:
        root = tokens[0]
        if root.upper() == "?":
            message = stock_messages["Help"]

    response = MessagingResponse()
    response.message(message)

    return str(response)

if __name__ == "__main__":
    app.run()





