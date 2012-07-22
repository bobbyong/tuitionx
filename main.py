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

import webapp2
import jinja2
import logging

from google.appengine.ext import db

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

class Signup(db.Model):
    email = db.StringProperty(required = True)
    joined = db.DateTimeProperty(auto_now_add = True)    

class Submit(db.Model):
    name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    joined = db.DateTimeProperty(auto_now_add = True)    



##### Playlist and Quiz List #####

addmaths_f4= { 'ch2': [(1, 'Quadratic Equations', 'Jg0nvDjdqsI',''),
                        (2, '2.1 Quadratic Equations and its Roots', 'bp6_gAesCTk',''), 
                        (3, '2.2 Quadratic Equations - Part 1', '2pW7MF6kL74',''), 
                        (4, '2.2 Quadratic Equations - Part 2', 'Pl6eaqIcqdg',''),
                        (5, '2.2 Quadratic Equations - Part 3', 'ooD8CvFPhig',''),
                        (6, '2.2 Quadratic Equations - Part 4', 'SKDw3EtBabs',''),
                        (7, '2.3 Types of Roots of Quadratic Equations - Part 1', 'Sd15kSxzM0w',''),
                        (8, '2.3 Types of Roots of Quadratic Equations - Part 2', 'KANVMqizc4Y','')],
                'public': [(1, 'Quadratic Function - Quadratic Inequality', 'TFxnznhE51Y','&start=6&end=399'),
                        (2, 'Quadratic Function - Linear Inequality', 'u85dFT_5H-c','&start=6&end=266'),
                        (3, 'Function - Type of Relation and Function Notation', '2WaCcWftvr8','&start=6&end=115'),
                        (4, 'Function - Finding Domain, Codomain and Range from Arrow Diagram', 'KhoRxK9XEKs','&start=6&end=104'),
                        (5, 'Function - Finding Object and Image for Ordered Pair', 'usNfqLgy7mM','&start=6&end=100'),
                        (6, 'Logarithm', 'n8eIOs4ARGE',''),
                        (7, 'Understanding Rates of Change', 'GKugLlsSsp8',''),
                        (8, 'Understanding Rates of Change Part 2', 'gZC2JHM-WxE','')],  
                'ch1': [] }
     

### PLAYLIST FORMAT --> DICTIONARY {chapter: [playlist]}
### [playlist] format --> [id, title, youtube link, time_delay]    

quiz = [(1, 'Solve the quadratic equation x(2x-3) = 2x+1. Give your answer correct to three decimal places.', 'x = 2.686 OR x = -0.186', 'x = 3.576 OR x = 2.102', 'x = -1.335 OR x = 1.353', 'x = 1.282 OR x = -3.521', 'CdmLRkDRm0o', 1), 
        (2, 'Find the range of values of <i>p</i> given that the quadratic equation x<sup>2</sup> = 5x+2-<i>p</i> has no roots.', 'p > 23/5', 'p < 33/4', 'p > 33/4', 'p < 23/5', 'ABrVHu7I2z8', 3)]

        #quiz format follows the following format (id, question, option1, option2, option3, option4, answer explanation, right answer)        





##### Main Page #####

class MainHandler(PageHandler):
    def get(self):
        self.render('main.html')

    def post(self):
        have_error = False
        email = self.request.get('email')
        
        params = dict(email = email)

        que = db.Query(Signup).filter("email =", email).fetch(limit=1)

        if que:
            params['error_email_register'] = "That email address is already registered."
            have_error = True
        
        if not valid_email(email):
            params['error_email'] = "That is not a valid email address."
            have_error = True

        if have_error:
            self.render('home.html', **params)

        else:      
            u = Signup(email=email)
            u.put()     
            
            self.render('home.html', message="Thank you for signing up with TuitionX. You may now begin your learning journey.<br><br>") 
        


##### Video Playlist Page #####

class PlaylistHandler(PageHandler):
    def get(self):
        
        subject = self.request.get("subject")
        year = self.request.get("year")
        chapter = self.request.get("chapter")
        lesson = self.request.get("lesson")
        lesson_id = int(lesson)-1
        
        list_to_use = addmaths_f4[chapter]

        while int(lesson_id+1)<len(list_to_use):
            self.render('playlist.html', playlist = list_to_use, lesson=lesson_id, \
                url = '/playlist?subject=%s&year=%s&chapter=%s&lesson=%s' %(subject,year,chapter,str(lesson_id + 2)), \
                button = "Next Video", time_delay=str(list_to_use[lesson_id][-1]), temp = addmaths_f4["public"])
            return

        self.render('playlist.html', playlist = list_to_use, lesson=lesson_id, url = '/quiz/1', \
            button = 'Continue Learning', time_delay=str(list_to_use[lesson_id][-1]), temp = addmaths_f4["public"])

        
                

##### Quizzes Page #####

class QuizHandler(PageHandler):
    def get(self, id):
        tuple_id = int(id)-1
        self.render('quiz.html', quiz = quiz, id=tuple_id, playlist=addmaths_f4)       


    def post(self, id):
        
        answer = self.request.get("quiz%s" %id)                     #get answer from form in 1,2,3,4 type

        if answer == '':                                            #form validation if no answer is selected
            self.write("Please click the Back button and select an answer.")
            return

        id = int(id)                                                #makes the id given in url an integer
        tuple_id = int(id) - 1                                      #refer to the id on the quiz tuple
        right_answer = "You got it right."
        wrong_answer = "You got it wrong."
        correct_answer = quiz[tuple_id][1 + quiz[tuple_id][-1]]     #print the correct answer in value type eg David Cameron
        given_answer = quiz[tuple_id][1 + int(answer)]              #print the answer given in value type eg Margaret Thatcher 
        explanation = quiz[tuple_id][-2]


        signup_button = """
                        <br><b><em>Congratulations on reaching this far in your learning. 
                        <br>We are working hard to build TuitionX. Kindly sign-up to our mailing list to keep updated.</em></b><br><br>
                        <a href = "/home" class="btn btn-primary btn-large">Sign Up Now &raquo;</a>
                        """  

        next_button = '<div class="playlist-button"><a href="/quiz/%s" class="btn btn-primary btn-large">Next Question &raquo;</a></div>' % str(id+1)                                    

        #signup_button and next_button SHOULD NOT be in this python/controller file --> it should be in the TEMPLATE/view/quiz.html file
        #signup_button and next_button is here for temporary convenience sake                  



        if int(answer) == quiz[tuple_id][-1]:                       #checks submitted answer with correct answer in tuple list
            if id+1 <= len(quiz):                                   #checks to see if this is the last question
                self.render("answer.html", quiz = quiz, correct_answer = correct_answer, given_answer = given_answer, tuple_id = tuple_id, solution = right_answer, explanation = explanation, nextquestion = next_button, playlist = addmaths_f4)
            else:
                self.render("answer.html", quiz = quiz, correct_answer = correct_answer, given_answer = given_answer, tuple_id = tuple_id, solution = right_answer, explanation = explanation, nextquestion = signup_button, playlist = addmaths_f4)
        else:                                                       #if wrong answer
            if id+1 <= len(quiz):                                   #if wrong answer and last question                
                self.render("answer.html", quiz = quiz, correct_answer = correct_answer, given_answer = given_answer, tuple_id = tuple_id, solution = wrong_answer, explanation = explanation, nextquestion = next_button, playlist = addmaths_f4)
            else:
                self.render("answer.html", quiz = quiz, correct_answer = correct_answer, given_answer = given_answer, tuple_id = tuple_id, solution = wrong_answer, explanation = explanation, nextquestion = signup_button, playlist = addmaths_f4)





##### SignUp Page #####


PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

def hash_str(s):
    return hashlib.md5(s).hexdigest()


class SignUpHandler(PageHandler):
    def get(self):
        self.render('signup.html')

    def post(self):
        have_error = False
        email = self.request.get('email')
        verify = self.request.get('verify')
        password = self.request.get('password')
        
        params = dict(email = email)

        que = db.Query(User).filter("email =", email).fetch(limit=1)

        if que:
            params['error_email_register'] = "That email address is already registered."
            have_error = True
        
        if not valid_password(password):
            params['error_password'] = "That is not a valid password."
            have_error = True
        
        elif email != verify:
            params['error_verify'] = "Your email addresses do not match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That is not a valid email address."
            have_error = True

        if have_error:
            self.render('signup.html', **params)

        else:      
            u = User(email=email, password=hash_str(password))
            u.put()     
            
            self.render('welcome.html') 





##### Home Handler #####

class HomeHandler(PageHandler):
    def get(self):
        self.render('home.html')

    def post(self):
        have_error = False
        email = self.request.get('email')
        
        params = dict(email = email)

        que = db.Query(Signup).filter("email =", email).fetch(limit=1)

        if que:
            params['error_email_register'] = "That email address is already registered."
            have_error = True
        
        if not valid_email(email):
            params['error_email'] = "That is not a valid email address."
            have_error = True

        if have_error:
            self.render('home.html', **params)

        else:      
            u = Signup(email=email)
            u.put()     
            
            self.render('welcome.html') 
    



##### Submit Handler #####

class SubmitHandler(PageHandler):
    def get(self):
        self.render('submit.html')

    def post(self):
        name = self.request.get('name')
        email = self.request.get('email')
        content = self.request.get('content')

        if name and valid_email(email) and content:
            p = Submit(name = name, email = email, content = content)
            p.put()
            self.render('home.html', message="Thank you for submitting your useful links. <br><br>") 
        
        else:
            error = "Name, valid email and content, please!"
            self.render("submit.html", name=name, email=email, content=content, error=error)    
    




##### About Handler #####

class AboutHandler(PageHandler):
    def get(self):
        self.render('about.html')

    

##### URL Mapping #####

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/home', HomeHandler),
                               ('/about', AboutHandler),
                               ('/playlist', PlaylistHandler),
                               ('/quiz/([0-9]+)', QuizHandler),
                               ('/submit', SubmitHandler),
                               ('/signup', SignUpHandler)],
                              debug=True)

