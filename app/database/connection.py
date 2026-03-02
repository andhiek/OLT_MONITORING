## ========= connection.py ==========


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://noc_user:capung21@localhost/noc_saas"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)



if __name__ == "__main__":
    try:
        conn = engine.connect()
        print("✅ Database connected successfully!")
        conn.close()
    except Exception as e:
        print("❌ Connection failed:", e)