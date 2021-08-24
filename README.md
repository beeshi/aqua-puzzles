twiliopuzzles
=============

Texting answer submission system for MIT Aquarium Puzzlehunt.

# Instructions

Go to twilio.com and make an account

Click "Buy a number" and purchase a number with SMS capabilities (I used 234-AQUA-PUZ)

Use https://cloud.mongodb.com/ to set up a free mongo db, make databse called "aqua" with collections "teams" and "subans"

Click "connect", set IP address to all, and create a database user.

Copy the connection string to the run file for the year.
It should look like: "client = MongoClient(connectionstring)"

Follow this tutorial to set up server:
https://aws.amazon.com/blogs/aws/app-runner-from-code-to-scalable-secure-web-apps/

## Build settings
### Runtime
Python 3
### Port
5000
### Build command
pip install -r requirements.txt
### Start command
flask run --host=0.0.0.0

## Service settings
### Environment Variables
FLASK_APP=run20XX.py

No need to add custon domain, although you can if you wish.

Your domain is available in Service overview under Default domain.

Change the Twilio webhook for messaging to be https://<your_domain>.awsapprunner.com/ and set to HTTP GET

To test sending a message, you can either text the number from your phone, or go to 
https://<your_domain>.awsapprunner.com/?From=testnumber&Body=testmessage
to test just the server.

https://<your_domain>.awsapprunner.com/allteams.txt gives you all the teams and when they started

https://<your_domain>.awsapprunner.com/answers.txt gives you all submitted answers for each puzzle

https://<your_domain>.awsapprunner.com/solvedpuzzles.txt gives you stats for puzzle solves
