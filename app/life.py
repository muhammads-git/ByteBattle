import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from redis.asyncio import Redis, ConnectionPool  # Added ConnectionPool explicitly

from app.jobs.schedular import start_schedular, stop_schedular

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(" Initializing and warming up Redis connection pool...")
    
    # 1. Explicit Connection Pool config setup karein
    # Is se max_connections enforce hoti hain limits ke mutabiq
    pool = ConnectionPool(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        max_connections=1000,  # 500 parallel connections capacity
        decode_responses=True
    )
    
    # 2. Redis client instance create karein using the pool
    redis_client = Redis(connection_pool=pool)
    
    try:
        # THE CRITICAL STEP: Pre-warm the connections!
        # PING call karne se actual TCP handshakes startup par hi complete ho jate hain
        await redis_client.ping()
        print(" Redis connection pool successfully warmed up with 500 max_connections!")
    except Exception as e:
        print(f"Failed to pre-warm Redis connection pool: {e}")
        # Agar startup pe connection fail ho to server run na kare taake faulty test na ho
        raise e

    # 3. App state mein store karein taake routing endpoints directly attach ho sakein
    app.state.redis = redis_client
    
    # 4. Scheduler start
    start_schedular()
    
    yield  #vYahan aapki application requests handle karegi (Locust Stress Test runs here)
    
    # --- SHUTDOWN LOGIC ---
    # 5. Scheduler stop
    stop_schedular()

    # 6. Stop and disconnect the pool properly
    print("vClosing Redis connection pool...")
    await redis_client.close()
    await pool.disconnect()  # Ensure all connections are fully released back to OS
    print("Redis connection pool clean shutdown complete.")
