##### OLD QUIZHANDLER #####


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







('/quiz/([0-9]+)', QuizHandler),