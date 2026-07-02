import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.academic_calendar import router as academic_calendar_router
from app.api.attendance import router as attendance_router
from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.departments import router as departments_router
from app.api.designations import router as designations_router
from app.api.employees import router as employee_router
from app.api.leave import router as leave_router
from app.api.overtime import router as overtime_router
from app.api.payroll import router as payroll_router
from app.api.users import router as users_router
from app.api.academic_calendar import router as academic_calendar_router
from app.core.config import settings
from app.db.session import SessionLocal, engine

logger = logging.getLogger(__name__)


def _get_alembic_heads() -> list[str]:
    """Return the list of head revision IDs from the migration scripts."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    return [rev.revision for rev in script.get_revisions("heads")]


def _get_db_current_heads() -> list[str]:
    """Return the revision(s) currently stamped in the database."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT version_num FROM alembic_version")
        ).fetchall()
    return [row[0] for row in rows]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 1. Database connectivity check ──────────────────────────────────────
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connectivity check passed.")
    except Exception as exc:
        url = settings.DATABASE_URL
        # Extract host and port safely for the log message
        try:
            from sqlalchemy.engine.url import make_url
            parsed = make_url(url)
            host = parsed.host or "unknown"
            port = parsed.port or "unknown"
        except Exception:
            host = "unknown"
            port = "unknown"
        logger.error(
            "DATABASE_URL connection failed — host=%s port=%s error=%s",
            host,
            port,
            exc,
        )
        sys.exit(1)

    # ── 2. Alembic migration state check ────────────────────────────────────
    try:
        script_heads = _get_alembic_heads()
        db_heads = _get_db_current_heads()

        script_head = script_heads[0] if script_heads else None
        db_head = db_heads[0] if db_heads else None

        if set(db_heads) != set(script_heads):
            logger.warning(
                "Migration state mismatch — db_head=%s expected_head=%s. "
                "Run: alembic upgrade head",
                db_head,
                script_head,
            )
            sys.exit(1)

        logger.info("Migration state OK — head=%s", db_head)
    except Exception as exc:
        logger.error("Migration state check failed: %s", exc)
        sys.exit(1)

    yield  # application runs here

    # Shutdown: nothing to clean up at this stage


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router)
app.include_router(departments_router)
app.include_router(designations_router)
app.include_router(academic_calendar_router)
app.include_router(employee_router, prefix="/employees", tags=["Employees"])
app.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
app.include_router(payroll_router, prefix="/payroll", tags=["Payroll"])
app.include_router(overtime_router, prefix="/overtime", tags=["Overtime"])
app.include_router(dashboard_router)
app.include_router(leave_router)
app.include_router(audit_logs_router)
app.include_router(academic_calendar_router, prefix="/academic-calendar", tags=["Academic Calendar"])


@app.get("/")
def root():
    return {"message": "School Payroll API is running"}


@app.get("/health")
def health_check():
    db_status = "ok"
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    finally:
        db.close()

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
    }
