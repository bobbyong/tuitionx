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

import webapp2
import jinja2
import logging

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


##### Main Page #####

class MainHandler(PageHandler):
    def get(self):
        self.render('main.html')


##### Video Playlist Page #####

class PlaylistHandler(PageHandler):
    def get(self, id):
        playlist = [(1, 'Video #1', 'bzE--l_Lj0A'), 
                    (2, 'Video #2', 'BURnfFozfO4'), 
                    (3, 'Video #3', 'luUD5CXMj3w'),
                    (4, 'Video #4', 'fNuk6j3nfmM'),
                    (5, 'Video #5', 'QGSt9Z4_WA8'),
                    (6, 'Video #6', '8OQnI8MJ6x0'),
                    (7, 'Video #7', 'KXsY2r1_9C0'),
                    (8, 'Video #8', '27NX_MMIkLY')]

        self.render('playlist.html', playlist = playlist, id=int(id)-1)


##### Quizzes Page #####

quiz = [(1, 'What is the product of 5 and 10?', '10', '5', '50', '20', 3), 
        (2, 'What is the sum of 35 and 25?', '60', '40', '55', '20', 1), 
        (3, 'Who is the current Prime Minister of UK?', 'Margaret Thatcher', 'Tony Blair', 'Gordon Brown', 'David Cameron', 4)]
        

class QuizHandler(PageHandler):
    def get(self, id):
        
        self.render('quiz.html', quiz = quiz, id=int(id)-1)       


    def post(self, id):
        answer = self.request.get("quiz%s" %id) 
        id = int(id)
        tuple_id = int(id) - 1
        if int(answer) == quiz[tuple_id][-1]:
            
            self.write("You got it right!")
            if id+1 <= len(quiz):
                self.write('<br><a href="/quiz/%s">Next</a>' % str(id+1))
            else:
                self.write('<br>No more question')
        else:
            self.write("You got it wrong")    

##### URL Mapping #####

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/playlist/([0-9]+)', PlaylistHandler),
                               ('/quiz/([0-9]+)', QuizHandler)],
                              debug=True)

