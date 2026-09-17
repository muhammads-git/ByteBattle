



## calcualte score...
def calculateScore(time_taken, correct: bool):
   """   
      calculate score per timetaken...
      Forumula;
      slope = the change in points from point a to b i.e points from 1s to 2s.
      score = slope * (time_taken - max_time) + min_time
      (x1 - y1) / (x2 - y2) 
   """
   max_time = 15
   min_score = 2
  
   score = 0
   if correct:
      if time_taken > 0 and time_taken < 1:
         time_taken = 1
      if time_taken <= max_time:
         # formulaaa to compute
         formula = -3.4285714 * (time_taken - max_time) + min_score
         score = formula
         # round off
         return round(score)
      else:
         return 0
   else:
      return 0
   
   

