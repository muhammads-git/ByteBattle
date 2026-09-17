import time
from datetime import datetime

quiz = [('print(2*4)'),('print(19+1)'),('print(2-1)')]
right_ans = [8,20,1]

options = [(1,3,4,5),(1,5,7,20),(4,5,3,1)]

## calcualte score...
def calculateScore(time_taken, correct: bool):
   """   
      calculate score per timetaken...
      Forumula;
      slope = the change in points from point a to b i.e points from 1s to 2s.
      score = slope * (time_taken - max_time) + max_score
   """
   max_time = 15
   min_score = 2
   formula = -3 * (time_taken - max_time) + min_score

   score = 0
   if correct:
      if time_taken <= 15:
         score = formula
         return score
      else:
         return 0
   else:
      return 0
   
   
      


while True:
   totla_score = 0
   print('game starts')
   for index,ques in enumerate(quiz):
      start_time = time.time()
      print(ques)
      print(options[index])
      # ans
      ans = int(input())
      end_time = time.time()
      # calculate the ans time... 
      float_t = end_time - start_time
      time_took = int(float_t)
      # if time taken is less than 1
      if time_took < 1:
         time_took = 1
      
      print(f'Time taken: {time_took}')
      if ans == right_ans[index]:
         score = calculateScore(time_took,True)
         totla_score += score
      else:
         score = calculateScore(time_took,False)
         totla_score += score

   print(totla_score)
   break

