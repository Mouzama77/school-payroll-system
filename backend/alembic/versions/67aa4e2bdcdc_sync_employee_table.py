from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '67aa4e2bdcdc'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():

    # =========================
    # 1. Late penalty rules
    # =========================
    op.create_table(
        'late_penalty_rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('late_days_min', sa.Integer(), nullable=False),
        sa.Column('deduction_amount', sa.Float(), nullable=False),
        sa.Column('label', sa.String(length=100)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('late_days_min')
    )

    # =========================
    # 2. Attendance changes
    # =========================

    op.add_column('attendance',
        sa.Column('check_in_time', sa.Time(), nullable=True)
    )

    op.add_column('attendance',
        sa.Column('check_out_time', sa.Time(), nullable=True)
    )

    # IMPORTANT: safe enum conversion
    attendance_enum = postgresql.ENUM(
        'PRESENT', 'ABSENT', 'HALF_DAY', 'ON_LEAVE', 'LATE',
        name='attendance_status',
        create_type=False
    )

    op.alter_column(
        'attendance',
        'status',
        type_=attendance_enum,
        postgresql_using="status::text::attendance_status"
    )

    # indexes
    op.create_index(
        'ix_attendance_date',
        'attendance',
        ['date']
    )

    op.create_index(
        'ix_attendance_employee_id',
        'attendance',
        ['employee_id']
    )

    # remove old columns
    op.drop_column('attendance', 'check_in')
    op.drop_column('attendance', 'check_out')

    # =========================
    # 3. Employees reporting_time FIX
    # =========================

    # STEP 1: backfill NULL values FIRST (critical fix)
    op.execute("""
        UPDATE employees
        SET reporting_time = '09:30'
        WHERE reporting_time IS NULL
    """)

    # STEP 2: now safely enforce NOT NULL
    op.alter_column(
        'employees',
        'reporting_time',
        existing_type=postgresql.TIME(),
        type_=sa.Time(),
        nullable=False,
        server_default='09:30:00'
    )


def downgrade():

    op.drop_column('attendance', 'check_in_time')
    op.drop_column('attendance', 'check_out_time')

    op.add_column('attendance', sa.Column('check_in', postgresql.TIME()))
    op.add_column('attendance', sa.Column('check_out', postgresql.TIME()))

    op.drop_index('ix_attendance_date', table_name='attendance')
    op.drop_index('ix_attendance_employee_id', table_name='attendance')

    op.drop_table('late_penalty_rules')

    # rollback enum safely
    op.alter_column(
        'attendance',
        'status',
        type_=sa.String(length=20),
        postgresql_using="status::text"
    )

    op.alter_column(
        'employees',
        'reporting_time',
        type_=postgresql.TIME(),
        nullable=True
    )