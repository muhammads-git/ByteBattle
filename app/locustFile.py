# import os
# import random
# import jwt
# from datetime import datetime, timezone, timedelta
# from locust import HttpUser, task, between
# from dotenv import load_dotenv

# # Project configurations read sync parameters setup
# load_dotenv()

# class LeaderboardStressUser(HttpUser):
#     # Short pacing wait interval to simulate high continuous read stress
#     wait_time = between(0.5, 1.5)

#     def on_start(self):
#         """
#         Runs exactly once per simulated user instantiation lifecycle checkpoint.
#         Generates a valid JWT targeting our clean pool of 5,000 pre-seeded accounts.
#         """
#         # Target only the IDs safely populated by our seed script execution context
#         # Assumes the seeded range fits well within your overall players pool allocation boundary
#         self.player_id = random.randint(1005, 5999) 
#         self.player_name = f"Player_Simulated_{self.player_id}"

#         # Secure system key variables extraction matching application settings
#         SECRET_KEY = os.getenv("SECRET_KEY") or "secret"
#         ALGORITHM = os.getenv("ALGORITHM") or "HS256"

#         token_payload = {
#             "sub": str(self.player_id),
#             "player_name": self.player_name,
#             "exp": datetime.now(timezone.utc) + timedelta(hours=2)
#         }
        
#         try:
#             encoded_jwt = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
            
#             # Persist secure authentication cookies directly to cookie container context
#             self.client.cookies.set("access_token", encoded_jwt)
            
#             # Optional: Fallback Authorization Header binding for double inspection layer verification
#             self.client.headers.update({
#                 "Authorization": f"Bearer {encoded_jwt}"
#             })
            
#         except Exception as e:
#             print(f"❌ [Locust Context Authentication Initialization Failure]: {e}")

#     @task
#     def view_leaderboard(self):
#         """
#         Pure Read Operation Benchmark:
#         Isolates your Redis data extraction tier logic from slow relational DB block actions.
#         """
#         with self.client.get("/leaderboard", catch_response=True) as response:
#             if response.status_code == 200:
#                 response.success()
#             elif response.status_code == 401:
#                 response.failure("401 Unauthorized - Confirm your JWT environment token constants or signatures match.")
#             elif response.status_code == 500:
#                 response.failure("500 Server Error - Redis engine lookup bottleneck or sync validation failure.")
#             else:
#                 response.failure(f"Request failed unexpectedly with status: {response.status_code}")



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

        # Hardcoded backup strings to bypass any loose .env parsing bottlenecks under sudden stress
        SECRET_KEY = os.getenv("SECRET_KEY") or "secret"
        ALGORITHM = os.getenv("ALGORITHM") or "HS256"

        token_payload = {
            "sub": str(self.player_id),
            "player_name": self.player_name,
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
