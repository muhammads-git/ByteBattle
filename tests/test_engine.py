from app.engine import calculateScore

def test_ali1s():
   result1 = calculateScore(1,True)
   assert result1 == 50
def test_usman2s():
   result2 = calculateScore(2,True)
   assert result2 == 47

def test_dani3s():
   result3 = calculateScore(3,True)
   assert result3 == 43
def test_hammad16s():
   result = calculateScore(16,True)
   assert result == 0

def test_hina12s():
   result = calculateScore(12,True)
   assert result == 12

def test_boundary_15s():
   result= calculateScore(15,True)
   assert result == 2
# correct = False
def test_dani1s():
   result = calculateScore(1,False)
   assert result == 0


   # test < 1
def test_lessthan_1():
   result = calculateScore(0.2,True)
   assert result == 50

def test_negative_time():
   result = calculateScore(-1,True)
   assert result == 50