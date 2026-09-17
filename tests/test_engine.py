from app.engine import calculateScore

def test_engine():
   result = calculateScore(1,True)
   assert result == 50