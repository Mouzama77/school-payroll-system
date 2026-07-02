from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
db.execute(text("DELETE FROM payrolls WHERE employee_id='5d916a85-7a87-4049-9b18-dd0eb6684398' AND month IN ('2026-02','2026-06')"))
db.commit()
db.close()
print("cleaned")
