#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import re
import hashlib
import random
import ast
import bcrypt

import webapp2
import jinja2
import logging

from google.appengine.ext import db

from notes import *
from quiz import *


##### Website Page Handlers #####

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class PageHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))




##### User Database Stuff #####

class User(db.Model):
    email = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    joined = db.DateTimeProperty(auto_now_add = True)
    count = db.IntegerProperty()
    points = db.IntegerProperty()

class Signup(db.Model):
    email = db.StringProperty(required=True)     
    joined = db.DateTimeProperty(auto_now_add = True)    

class Submit(db.Model):
    name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    joined = db.DateTimeProperty(auto_now_add = True)    



##### Main Page #####

class MainHandler(PageHandler):
    def get(self):
        user = self.request.cookies.get('user')
        if user:
            user_db = db.GqlQuery("SELECT * FROM User WHERE email = :1", user).get()
            if user_db:
                if user_db.count:
                    count = user_db.count
                else:
                    count = 1
                count += 1
                user_db.count = count
                user_db.put()

                if user_db.points:
                    points = user_db.points
                else:
                    points = 0
                self.response.headers.add_header('Set-Cookie', 'points=%s; Path=/' % str(points))

            self.redirect('/home')
        else:
            self.render('main.html') 





##### Learn Page #####

chapter_dic = {1: ['Alkanes',alkane, alkane_quiz], 2: ['Alkenes',alkene, alkene_quiz], 3: ['Alcohols',alcohol, alcohol_quiz],
               4: ['Carboxylic Acids',carboxylic, carboxylic_quiz], 5: ['Esters', ester, ester_quiz], 6: ['Fats', fats, ''],
               7: ['Natural Rubber', rubber, ''], 10: ['Pendidikan Moral', moral, moral_quiz], 
               99: ['','',alkane_quiz+alkene_quiz+alcohol_quiz+carboxylic_quiz+ester_quiz]}


class LearnHandler(PageHandler):
    def get(self, chapter, id):
        learn_id = int(id)-1
        title = chapter_dic[int(chapter)][0]
        learn = chapter_dic[int(chapter)][1]
        quiz = chapter_dic[int(chapter)][2]

        
        points = self.request.cookies.get('points')
        if points == None:
            points = 0

        if int(id) <= len(learn):
            if isinstance(learn[learn_id], int ): 
                self.render('newquiz.html', quiz=quiz, id=learn[learn_id], title=title, totalpoints=points) 
            else:    
                self.render('learn.html', learn=learn, id=learn_id, chapter=chapter, title=title, totalpoints=points)    
        else:
            self.render('endoflearn.html',totalpoints=points)  
           

    def post(self, chapter, id):
        learn_id = int(id)-1
        title = chapter_dic[int(chapter)][0]
        learn = chapter_dic[int(chapter)][1]
        quiz = chapter_dic[int(chapter)][2]

        quiz_id = learn[learn_id]
        answer = self.request.get("quiz%s" % str(quiz_id))
        correct_answer_id = quiz[quiz_id][-1]

        points = self.request.cookies.get('points')
        if points == None:
            points = 0

        if answer == '':                                            #form validation if no answer is selected
            self.write("Please click the Back button and select an answer.")
            return

        
        if int(answer) == quiz[quiz_id][-1]:
            points = int(points) + 50
            self.response.headers.add_header('Set-Cookie', 'points=%s; Path=/' % str(points))

            user = self.request.cookies.get('user')
            if user:
                user_db = db.GqlQuery("SELECT * FROM User WHERE email = :1", user).get()
                if user_db:
                    if user_db.points:
                        points = user_db.points
                    else:
                        points = 0
                    points += 50
                    user_db.points = points
                    user_db.put()


            self.render('newanswer.html', solution = "right", quiz=quiz, id=quiz_id, next=learn_id+2, \
            given_answer = quiz[quiz_id][int(answer)], correct_answer = quiz[quiz_id][correct_answer_id], points = '+50', \
            title=title, totalpoints=str(points),chapter=chapter)        
        else:
            self.response.headers.add_header('Set-Cookie', 'points=%s; Path=/' % str(points))

            self.render('newanswer.html', solution = "wrong", quiz=quiz, id=quiz_id, next=learn_id+2, \
            given_answer = quiz[quiz_id][int(answer)], correct_answer = quiz[quiz_id][correct_answer_id], points = '+0', \
            title=title, totalpoints=str(points), chapter=chapter)


##### Quizzes Page #####

def rand(exclude, length):
    r = None
    while r in exclude or r is None:
         r = random.randrange(0, length)
    return r

class QuizHandler(PageHandler):
    def get(self, chapter, id):
        quiz = chapter_dic[int(chapter)][2]
        past_id = self.request.cookies.get('quiz_id')
        
        if past_id:
            past_id = past_id.split('|')
            past_id = [int(i) for i in past_id]
        else:
            past_id = []

        points = self.request.cookies.get('points')
        if points == None:
            points = 0

        if len(past_id)+1 <= len(quiz):
            quiz_id = rand(past_id, len(quiz))
            past_id.append(quiz_id)
            past_id = [str(i) for i in past_id]
            past_id = '|'.join(past_id)
            self.response.headers.add_header('Set-Cookie', 'quiz_id=%s; Path=/' % past_id)
            self.render('quiz2.html', quiz=quiz, totalpoints=points, id=quiz_id) 
        else:
            self.response.headers.add_header('Set-Cookie', 'quiz_id=%s; Path=/' % '')
            self.render('endoflearn.html',totalpoints=points)  
        

    def post(self, chapter, id):
        quiz = chapter_dic[int(chapter)][2]
        past_id = self.request.cookies.get('quiz_id')
        past_id = past_id.split('|')
        past_id = [int(i) for i in past_id]
        quiz_id = past_id.pop()
        
        points = self.request.cookies.get('points')
        if points == None:
            points = 0

        
        input1 = self.request.get("input1").lower()
        input2 = self.request.get("input2").lower()
        
        if input1 == quiz[quiz_id][-3] and input2 == quiz[quiz_id][-2]:
            points = int(points) + 50
            self.response.headers.add_header('Set-Cookie', 'points=%s; Path=/' % str(points))

            user = self.request.cookies.get('user')
            if user:
                user_db = db.GqlQuery("SELECT * FROM User WHERE email = :1", user).get()
                if user_db:
                    if user_db.points:
                        points = user_db.points
                    else:
                        points = 0
                    points += 50
                    user_db.points = points
                    user_db.put()


            self.render('answer2.html', solution = "right", quiz=quiz, id=quiz_id, next=quiz_id+2, \
            points = '+50', totalpoints=str(points), chapter=chapter)   

        else:
            self.response.headers.add_header('Set-Cookie', 'points=%s; Path=/' % str(points))

            self.render('answer2.html', solution = "wrong", quiz=quiz, id=quiz_id, next=quiz_id+2, \
            points = '+0', totalpoints=str(points), chapter=chapter)   

        
##### Multiple Choice Quizzes Page (Quiz2Handler) #####

class Quiz2Handler(PageHandler):
    def get(self, chapter, id):
        quiz = chapter_dic[int(chapter)][2]
        past_id = self.request.cookies.get('quiz2_id')
        
        if past_id:
            past_id = past_id.split('|')
            past_id = [int(i) for i in past_id]
        else:
            past_id = []

        points = self.request.cookies.get('points')
        if points == None:
            points = 0

        if len(past_id)+1 <= len(quiz):
            quiz_id = rand(past_id, len(quiz))
            past_id.append(quiz_id)
            past_id = [str(i) for i in past_id]
            past_id = '|'.join(past_id)
            self.response.headers.add_header('Set-Cookie', 'quiz2_id=%s; Path=/' % past_id)
            self.render('newquiz.html', quiz=quiz, id=quiz_id, totalpoints=points) 
        else:
            self.response.headers.add_header('Set-Cookie', 'quiz2_id=%s; Path=/' % '')
            self.render('endoflearn.html',totalpoints=points)  
        

    def post(self, chapter, id):
        quiz = chapter_dic[int(chapter)][2]
        past_id = self.request.cookies.get('quiz2_id')
        past_id = past_id.split('|')
        past_id = [int(i) for i in past_id]
        quiz_id = past_id.pop()


        answer = self.request.get("quiz%s" % str(quiz_id))
        correct_answer_id = quiz[quiz_id][-1]
        
        points = self.request.cookies.get('points')
        if points == None:
            points = 0

        if answer == '':                                            #form validation if no answer is selected
            self.write("Please click the Back button and select an answer.")
            return        
        
        if int(answer) == quiz[quiz_id][-1]:
            points = int(points) + 50
            self.response.headers.add_header('Set-Cookie', 'points=%s; Path=/' % str(points))

            user = self.request.cookies.get('user')
            if user:
                user_db = db.GqlQuery("SELECT * FROM User WHERE email = :1", user).get()
                if user_db:
                    if user_db.points:
                        points = user_db.points
                    else:
                        points = 0
                    points += 50
                    user_db.points = points
                    user_db.put()


            self.render('newanswer2.html', solution = "right", quiz=quiz, id=quiz_id, next=quiz_id, \
            given_answer = quiz[quiz_id][int(answer)], correct_answer = quiz[quiz_id][correct_answer_id], points = '+50', \
            totalpoints=str(points), chapter=chapter)        
        else:
            self.response.headers.add_header('Set-Cookie', 'points=%s; Path=/' % str(points))

            self.render('newanswer2.html', solution = "wrong", quiz=quiz, id=quiz_id, next=quiz_id, \
            given_answer = quiz[quiz_id][int(answer)], correct_answer = quiz[quiz_id][correct_answer_id], points = '+0', \
            totalpoints=str(points), chapter=chapter)


##### SignUp Page #####


PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return email and EMAIL_RE.match(email)

def hash_str(s):
    return bcrypt.hashpw(s, bcrypt.gensalt())
    ### return hashlib.md5(s).hexdigest()


class SignUpHandler(PageHandler):
    def get(self):
        self.render('signup.html', title="Sign Up", message = 'Registered already? <a href="/login">Login now!</a>')

    def post(self):
        have_error = False
        email = self.request.get('email')
        password = self.request.get('password')
        remember = self.request.get('remember')
        
        params = dict(email = email)

        que = db.Query(User).filter("email =", email).fetch(limit=1)

        if que:
            params['error_email_register'] = "That email address is already registered."
            have_error = True
        
        if not valid_email(email):
            params['error_email'] = "That is not a valid email address."
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That is not a valid password."
            have_error = True
        
        if have_error:
            self.render('signup.html',title="Sign Up", message = 'Registered already? <a href="/login">Login now!</a>', **params)

        else:      
            u = User(email=email, password=hash_str(password), count = 1, points = 0)
            u.put()   

            if remember:
                self.response.headers.add_header('Set-Cookie', 'user=%s; expires=Tue, 31-Dec-2013 23:59:59 GMT; Path=/' % str(email))

            
            self.redirect('/home') 



class LoginHandler(PageHandler):
    def get(self):
        self.render('signup.html', title="Login", message = 'First time user? <a href="/signup">Sign up now!</a>')

    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        remember = self.request.get('remember')

        user_db = db.GqlQuery("SELECT * FROM User WHERE email = :1", email)
        user = user_db.get()

        if user:
            pw = user.password
            if bcrypt.hashpw(password, pw) == pw:
                
                if user.count:
                    count = user.count
                else:
                    count = 1
                count += 1
                user.count = count
                user.put()
                
                if user.points:
                    points = user.points
                else:
                    points = 0
                self.response.headers.add_header('Set-Cookie', 'points=%s; Path=/' % str(points))


                if remember:
                    self.response.headers.add_header('Set-Cookie', 'user=%s; expires=Tue, 31-Dec-2013 23:59:59 GMT; Path=/' % str(email))

                self.redirect('/home')   


        self.render('signup.html', title="Login", login_error = "Wrong email/password combination. Please try again.", message = 'First time user? <a href="/signup">Sign up now!</a>')    
            
        
##### Home Handler #####

class HomeHandler(PageHandler):
    def get(self):
        user = self.request.cookies.get('user')
        if not user:
            self.render('main.html')
            return 

        self.render('home.html')




##### Submit Handler #####

class SubmitHandler(PageHandler):
    def get(self):
        self.render('submit.html')

    def post(self):
        name = self.request.get('name')
        email = self.request.get('email')
        content = self.request.get('content')

        if name and email != '' and valid_email(email) and content:
            p = Submit(name = name, email = email, content = content)
            p.put()
            self.render('home.html', message="Thank you for submitting your useful links. <br><br>") 
        
        else:
            error = "Name, valid email and content, please!"
            self.render("submit.html", name=name, email=email, content=content, error=error)    
    


class LogoutHandler(PageHandler):
    def get(self):
        b = 'user=%s; Path=/'  % ""
        self.response.headers.add_header('Set-Cookie', b)
        self.redirect('/')


##### URL Mapping #####

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/home', HomeHandler),
                               ('/quiz/([0-9]+)/([0-9]+)', QuizHandler),
                               ('/quiz2/([0-9]+)/([0-9]+)', Quiz2Handler),
                               ('/learn/([0-9]+)/([0-9]+)', LearnHandler),
                               ('/feedback', SubmitHandler),
                               ('/signup', SignUpHandler),
                               ('/login', LoginHandler),
                               ('/logout', LogoutHandler)],
                              debug=True)

