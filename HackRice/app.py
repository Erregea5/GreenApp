import flask
import pandas as pd
import data
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from io import StringIO
import time

app=flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///try.db'
db=SQLAlchemy(app)

CHAT_LIMIT=100

class Transportation(db.Model):
    id: Mapped[int] = mapped_column(unique=True, nullable=False, primary_key=True)
    user: Mapped[str]
    date: Mapped[datetime] =mapped_column(default=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0))
    miles_walked: Mapped[int]
    miles_driven: Mapped[int]
    miles_on_publict: Mapped[int]

class Person(db.Model):
    username: Mapped[str] = mapped_column(unique=True, nullable=False, primary_key=True)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str]
    city: Mapped[str]

class Chat(db.Model):
    id: Mapped[int] = mapped_column(unique=True,primary_key=True)
    conversation_name: Mapped[str] = mapped_column(nullable=False)
    speaker_name: Mapped[str] = mapped_column(nullable=False)
    text:Mapped[str] = mapped_column(db.String(CHAT_LIMIT), nullable=False)
    date_sent: Mapped[datetime]=mapped_column(default=datetime.utcnow())

class Conversation(db.Model):
    name: Mapped[str] = mapped_column(nullable=False, primary_key=True,unique=False)
    city: Mapped[str] = mapped_column(nullable=False,unique=False)
    last_chat_id: Mapped[int] = mapped_column(unique=False)
    date_started: Mapped[datetime]=mapped_column(default=datetime.utcnow())



def isValidUser(username:str|None,password:str|None)->bool:
    if username is None or password is None:
        return False
    user=db.session.get(Person,username)
    if user is None:
        return False
    return user.password==password

@app.route('/signup',methods=['GET','POST'])
def signup():
    if flask.request.method=='POST':
        username=flask.request.form['username']
        password=flask.request.form['password']

        if username is None or password is None:
            return 'Fill in username and password'

        if db.session.get(Person,username) is not None:
            return 'username is already taken'

        new_person=Person(
            username=username,
            password=password,
            email=flask.request.form['email'],
            city=flask.request.form['city']
        )
        try:
            db.session.add(new_person)
            db.session.commit()
            return flask.redirect(flask.url_for('home',username=username,password=password))
        except:
            return 'Error signing up user'
    else:
        return flask.render_template('signup.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if flask.request.method=='POST':
        username=flask.request.form['username']
        password=flask.request.form['password']
        new_person=Person(
            username=username,
            password=password
            )
        try:
            if isValidUser(username,password):
                print(flask.url_for('home',username=username,password=password))
                return flask.redirect(flask.url_for('home',username=username,password=password))
            else:
                return 'incorrect username or password'
        except:
            return 'Error logging in user'
    else:
        return flask.render_template('login.html')

@app.route('/')
def start():
    return flask.redirect('/login')

@app.route('/home',methods=['GET','POST'])
def home():
    if flask.request.method=='POST':
        username=flask.request.form['username']
        password=flask.request.form['password']

        if flask.request.form['type']=='posts':
            conversation_name=flask.request.form['conversation']
            first_message=flask.request.form['message']

            def tryToAddConversation():
                # try:
                new_chat=Chat(
                    conversation_name=conversation_name,
                    speaker_name=username,
                    text=first_message
                )
                db.session.add(new_chat)
                new_conversation=Conversation(
                    name=conversation_name,
                    city=db.session.get(Person,username).city,
                    last_chat_id=new_chat.id
                )
            
                
                db.session.add(new_conversation)
                db.session.commit()
                return flask.redirect(flask.url_for('thread',username=username,password=password,conversation=conversation_name))
                # except:
                    # return 'Error creating a new conversation'

            try:
                if db.session.query(Conversation).first() is None:
                    return tryToAddConversation()
                if db.session.get(Conversation,conversation_name) is not None:
                    return "Conversation already exists"
                else:
                    return tryToAddConversation()
            except:
                return tryToAddConversation()
        else:
            #public driven walk
            public_transport_miles=flask.request.form['public']
            driven_miles=flask.request.form['driven']
            walked_miles=flask.request.form['walk']

            def tryToAddToStats():
                new_transport=Transportation(
                    miles_walked=walked_miles,
                    miles_driven=driven_miles,
                    miles_on_publict=public_transport_miles,
                    user=username
                )

                db.session.add(new_transport)
                db.session.commit()
                return flask.redirect(flask.url_for('stats',username=username,password=password))
            
            try:    
                if db.session.query(Transportation).first() is None:
                    return tryToAddToStats()
                my_existing=existing=db.session.query(Transportation).filter_by(user=username)
                if my_existing.first() is None:
                    return tryToAddToStats()
                my_existing.filter_by(date=datetime.today().replace(hour=0, minute=0, second=0, microsecond=0))
                
                if existing is not None:
                    existing.update({
                        'miles_walked':walked_miles,
                        'miles_driven':driven_miles,
                        'miles_on_publict':public_transport_miles,
                    })
                    db.session.commit()
                    print('here')
                    return flask.redirect(flask.url_for('stats',username=username,password=password))
                else:
                    return tryToAddToStats()
            except:
                return tryToAddToStats()
    else:
        username = flask.request.values.get('username',None)
        password = flask.request.values.get('password',None)
        
        if not isValidUser(username,password):
            return flask.redirect('/login')
        
        user=db.session.get(Person,username)
        all_conversations=db.session.query(Conversation)
        try:
            if all_conversations.first() is not None:
                community_conversations=all_conversations.filter_by(city=user.city).order_by(Conversation.date_started)
                convos_and_last_message=[]
                for a in community_conversations:
                    convos_and_last_message.append((a,a.last_chat_id))
                return flask.render_template('home.html',community_conversations=convos_and_last_message,username=username,password=password)
            else:
                return flask.render_template('home.html',community_conversations=[],username=username,password=password)
        except:
            return flask.render_template('home.html',community_conversations=[],username=username,password=password)

@app.route('/thread',methods=['GET','POST'])
def thread():
    if flask.request.method=='POST':
        username = flask.request.form['username']
        password = flask.request.form['password']

        if not isValidUser(username,password):
            return flask.redirect('/login')
        
        conversation = flask.request.form['conversation']
        new_chat=Chat(
            text=flask.request.form['message'],
            conversation_name=conversation,
            speaker_name=username
        )
        
        try:
            db.session.add(new_chat)
            db.session.commit()
            print(flask.url_for('thread',username=username,password=password,conversation=conversation))
            return flask.redirect(flask.url_for('thread',username=username,password=password,conversation=conversation))
        except:
            return 'Error posting to conversation'
        
    else:
        username = flask.request.values.get('username')
        password = flask.request.values.get('password')

        if not isValidUser(username,password):
            return flask.redirect('/login')
        
        conversation = flask.request.values.get('conversation')
        chats=db.session.query(Chat).filter_by(conversation_name=conversation).order_by(Chat.date_sent).all()
        return flask.render_template('thread.html',chats=chats, username=username, password=password, conversation=conversation, n=len(chats))
    
@app.route('/stats')
def stats():
    username = flask.request.values.get('username',None)
    password = flask.request.values.get('password',None)
    
    if not isValidUser(username,password):
        return flask.redirect('/login')
    
    my_table=db.session.query(Transportation).filter_by(user=username)
    all_table=db.session.query(Transportation)

    my_csv='user,date,miles_walked,miles_on_car,miles_on_publict\n'
    all_csv=my_csv
    for t in my_table.order_by(Transportation.date):
        my_csv+=username+','+str(t.date.month)+'/'+str(t.date.day)+'/'+str(t.date.year)+','+str(t.miles_driven)+','+str(t.miles_on_publict)+','+str(t.miles_walked)+'\n'
    
    for t in all_table.order_by(Transportation.date):
        all_csv+=t.user+','+str(t.date.month)+'/'+str(t.date.day)+'/'+str(t.date.year)+','+str(t.miles_driven)+','+str(t.miles_on_publict)+','+str(t.miles_walked)+'\n'
    
    print(all_csv)

    df = pd.read_csv(StringIO(all_csv))
    
    image_names=data.render_graphs(df, username)
    recommendations=data.generate_text(my_csv,100)
    return flask.render_template('stats.html',images=['static/images/user_trend.png','static/images/user_pie.png'],recommendations=recommendations)


if __name__=='__main__':
    # with app.app_context():
        # db.create_all()
    app.run(debug=True)