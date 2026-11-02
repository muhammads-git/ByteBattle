import os
import random
import jwt
from datetime import datetime, timezone, timedelta
from locust import HttpUser, task, between
from dotenv import load_dotenv

load_dotenv()

class LeaderboardStressUser(HttpUser):
    # Safe pacing interval to prevent instant packet drops on Windows
    wait_time = between(1.0, 2.5)

    def on_start(self):
        """
        Runs exactly once per virtual user spawn. Safe, bulletproof session initialization.
        """
        # Select randomly from the pool populated by your seeding script
        self.player_id = random.randint(1005, 5999) 
        self.player_name = f"Player_Simulated_{self.player_id}"

        SECRET_KEY = os.getenv("SECRET_KEY") or "secret"
        ALGORITHM = os.getenv("ALGORITHM") or "HS256"

        # 🔥 FIXED PAYLOAD: Aligned precisely with the dictionary key expectations in get_current_user
        token_payload = {
            "sub": self.player_name,       # "sub" must contain the string username
            "user_id": self.player_id,     # "user_id" must contain the integer user ID
            "exp": datetime.now(timezone.utc) + timedelta(hours=2)
        }
        
        try:
            encoded_jwt = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
            
            # Direct cookie allocation sync
            self.client.cookies.set("access_token", encoded_jwt)
            self.client.headers.update({
                "Authorization": f"Bearer {encoded_jwt}"
            })
        except Exception as e:
            # Fallback mock setup so the request runner NEVER crashes out during cold starts
            mock_token = "faked-fallback-stress-token-string"
            self.client.cookies.set("access_token", mock_token)
            self.client.headers.update({
                "Authorization": f"Bearer {mock_token}"
            })

    @task
    def view_leaderboard(self):
        """Pure cache lookup isolation endpoint"""
        with self.client.get("/leaderboard", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Drop Encountered: Status Code {response.status_code}")
