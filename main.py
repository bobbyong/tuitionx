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





##### User Database Stuff

class User(db.Model):
    email = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    joined = db.DateTimeProperty(auto_now_add = True)

    
      
      

##### Main Page #####

class MainHandler(PageHandler):
    def get(self):
        self.render('main.html')


##### Video Playlist Page #####

class PlaylistHandler(PageHandler):
    def get(self, id):
        playlist = [(1, 'Video #1', 'bzE--l_Lj0A'), 
                    (2, 'Video #2', 'BURnfFozfO4'), 
                    (3, 'Video #3', 'luUD5CXMj3w')]

        while int(id)<len(playlist):            
            self.render('playlist.html', playlist = playlist, id=int(id)-1, url = '/playlist/%s' %str(int(id)+1), button = "Next Video")
            return
        
        self.render('playlist.html', playlist = playlist, id=int(id)-1, url = '/quiz/1', button = 'Continue Learning')
                

##### Quizzes Page #####

quiz = [(1, 'What is the product of 5 and 10?', '10', '5', '50', '20', 'This is Explanation for Q1.', 3), 
        (2, 'What is the sum of 35 and 25?', '60', '40', '55', '20', 'This is Explanation for Q2.', 1), 
        (3, 'Who is the current Prime Minister of UK?', 'Margaret Thatcher', 'Tony Blair', 'Gordon Brown', 'David Cameron', 'This is Explanation for Q3.', 4)]

        #quiz format follows the following format (id, question, option1, option2, option3, option4, answer explanation, right answer)        

class QuizHandler(PageHandler):
    def get(self, id):
        tuple_id = int(id)-1
        self.render('quiz.html', quiz = quiz, id=tuple_id)       


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
                        <br>To continue, you will have to register. Otherwise all your great progress will be lost forever.</em></b><br><br>
                        <a href = "/signup" class="btn btn-primary btn-large">Sign Up Now &raquo;</a>
                        """  

        next_button = '<a href="/quiz/%s" class="btn btn-primary btn-large">Next Question &raquo;</a>' % str(id+1)                                    

        #signup_button and next_button SHOULD NOT be in this python/controller file --> it should be in the TEMPLATE/view/quiz.html file
        #signup_button and next_button is here for temporary convenience sake                  



        if int(answer) == quiz[tuple_id][-1]:                       #checks submitted answer with correct answer in tuple list
            if id+1 <= len(quiz):                                   #checks to see if this is the last question
                self.render("answer.html", quiz = quiz, correct_answer = correct_answer, given_answer = given_answer, tuple_id = tuple_id, solution = right_answer, explanation = explanation, nextquestion = next_button)
            else:
                self.render("answer.html", quiz = quiz, correct_answer = correct_answer, given_answer = given_answer, tuple_id = tuple_id, solution = right_answer, explanation = explanation, nextquestion = signup_button)
        else:                                                       #if wrong answer
            if id+1 <= len(quiz):                                   #if wrong answer and last question                
                self.render("answer.html", quiz = quiz, correct_answer = correct_answer, given_answer = given_answer, tuple_id = tuple_id, solution = wrong_answer, explanation = explanation, nextquestion = next_button)
            else:
                self.render("answer.html", quiz = quiz, correct_answer = correct_answer, given_answer = given_answer, tuple_id = tuple_id, solution = wrong_answer, explanation = explanation, nextquestion = signup_button)





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






##### About Handler #####

class AboutHandler(PageHandler):
    def get(self):
        self.render('about.html')




##### URL Mapping #####

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/playlist/([0-9]+)', PlaylistHandler),
                               ('/quiz/([0-9]+)', QuizHandler),
                               ('/signup', SignUpHandler),
                               ('/about', AboutHandler)],
                              debug=True)

