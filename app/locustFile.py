from locust import HttpUser, task, between
import random
import jwt
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Automatically pulls the real environment signature constants directly from your project config!
load_dotenv()

class QuizAppUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """
        Dynamically synchronizes key signatures using your system configuration data context.
        """
        random_id = random.randint(1, 10)
        player_name = f"player_{random_id}"

        # --- DYNAMIC CONFIGURATION ALIGNMENT ---
        # 1. Server configuration secrets trace check:
        # Reads the exact real secret token variable used by your app/auths/jwt package logic!
        SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or "secret"
        ALGORITHM = os.getenv("ALGORITHM") or "HS256"

        print(f"[Engine Config Check] Using SECRET_KEY signature source string: '{SECRET_KEY}' | Algorithm: '{ALGORITHM}'")

        token_payload = {
            "sub": player_name,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
        }
        
        try:
            encoded_jwt = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
            
            # Direct headers parameter cookie framework injection simulation
            self.client.headers.update({
                "Cookie": f"access_token={encoded_jwt}"
            })
            print(f"✅ [JWT Sync Active] Secure mapping context enforced for: {player_name}")
            
        except Exception as e:
            print(f"❌ [JWT Fail]: {e}")

    @task(1)
    def view_leaderboard(self):
        """Simulate profile check dynamic leaderboard tracking"""
        self.client.get("/leaderboard")

    @task(3)
    def submit_answer(self):
        """Simulate real quiz choices updates with row locks check"""
        room_code = "FINAL_STRESS_ROOM" 
        form_payload = {
            "option_index": random.randint(0, 3),
            "question_index": 0  
        }
        
        self.client.post(
            f"/rooms/{room_code}/answer", 
            data=form_payload,
            name="/rooms/[room_code]/answer",
            allow_redirects=False
        )
