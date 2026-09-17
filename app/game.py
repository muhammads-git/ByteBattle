import time
from datetime import datetime
from app.engine import calculateScore

quiz = [('print(2*4)'),('print(19+1)'),('print(2-1)')]
right_ans = [8,20,1]

options = [(1,3,4,8),(1,5,7,20),(4,5,3,1)]


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
      
      print(f'Time taken: {time_took}')
      if ans == right_ans[index]:
         score = calculateScore(time_took,True)
         totla_score += score
      else:
         score = calculateScore(time_took,False)
         totla_score += score

   print(totla_score)
   break

