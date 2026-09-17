



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
   formula = -3.4285714 * (time_taken - max_time) + min_score

   score = 0
   if correct:
      if time_taken < 1:
         time_taken = 1
      if time_taken <= max_time:
         score = formula
         return round(score)
      else:
         return 0
   else:
      return 0
   
   

