import time
from datetime import datetime

quiz = [('print(2*4)'),('print(19+1)'),('print(2-1)')]
right_ans = [8,20,1]

options = [(1,3,4,5),(1,5,7,20),(4,5,3,1)]

## calcualte score...
def calculatScore(time_taken, ans: bool):
   pass







while True:
   
   print('game starts')
   for index,ques in enumerate(quiz):
      start_time = time.time()
      print(ques)
      print(options[index])
      # ans
      ans = int(input())
      end_time = time.time()
      # calculate the ans time... 
      time_took = end_time - start_time
      print(f'TIme taken: {time_took}')
      if ans == right_ans[index]:
         # calculate score according to time
   # break


      

