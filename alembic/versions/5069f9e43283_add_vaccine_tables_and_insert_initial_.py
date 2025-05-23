"""Add vaccine tables and insert initial data

Revision ID: 5069f9e43283
Revises: 485d594c147e
Create Date: 2025-05-23 17:14:44.766404

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.sql import column, table

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5069f9e43283"
down_revision: Union[str, None] = "485d594c147e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "vaccine_types",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(10), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("period", sa.Integer, nullable=False),
    )

    op.create_table(
        "vaccination_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("dog_id", sa.Integer, sa.ForeignKey("dogs.id"), nullable=False),
        sa.Column(
            "vaccine_id", sa.String, sa.ForeignKey("vaccine_types.id"), nullable=False
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("hospital", sa.String(100), nullable=True),
        sa.Column("memo", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 초기 데이터 삽입
    vaccine_types_table = table(
        "vaccine_types",
        column("id", sa.String),
        column("name", sa.String),
        column("category", sa.String),
        column("description", sa.String),
        column("period", sa.Integer),
    )

    op.bulk_insert(
        vaccine_types_table,
        [
            {
                "id": "dhppl",
                "name": "DHPPL (종합백신)",
                "category": "필수",
                "description": "디스템퍼, 간염, 파보바이러스, 파라인플루엔자, 렙토스피라증",
                "period": 365,
            },
            {
                "id": "rabies",
                "name": "광견병 (Rabies)",
                "category": "필수",
                "description": "치명적인 바이러스성 질환 예방 (법적 의무)",
                "period": 365,
            },
            {
                "id": "heartworm",
                "name": "심장사상충 예방약",
                "category": "필수",
                "description": "모기를 통해 전염되는 기생충 예방",
                "period": 30,
            },
            {
                "id": "kennel",
                "name": "켄넬코프 (KC, Bordetella)",
                "category": "선택",
                "description": "전염성 기관지염 예방",
                "period": 365,
            },
            {
                "id": "corona",
                "name": "코로나 장염 백신",
                "category": "선택",
                "description": "개 코로나 바이러스 예방",
                "period": 365,
            },
            {
                "id": "influenza",
                "name": "인플루엔자 백신",
                "category": "선택",
                "description": "개 인플루엔자 예방",
                "period": 365,
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("vaccination_records")
    op.drop_table("vaccine_types")
