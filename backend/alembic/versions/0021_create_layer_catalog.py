"""create mesa_a.layer_catalog table (metadata catalog — RF01)

Mirrors the metadata spreadsheet (docs/database/modelagem/metadados_vetoriais.csv)
so the layer metadata has a single source of truth in the database, feeding the
GUI metadata viewer instead of a hardcoded frontend/backend registry.

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-15
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.layer_catalog (
            id SERIAL PRIMARY KEY,
            -- Stable operational key derived from plano_informacao + fonte.
            layer_key VARCHAR(120) NOT NULL UNIQUE,
            -- Spreadsheet fields (planilha de controle de metadados).
            tema VARCHAR(120),
            plano_informacao VARCHAR(160),
            fonte VARCHAR(160),
            fonte_principal BOOLEAN NOT NULL DEFAULT TRUE,
            data_atualizacao_fonte VARCHAR(60),
            periodicidade VARCHAR(160),
            segregacao VARCHAR(80),
            datum VARCHAR(60),
            epsg VARCHAR(20),
            formato VARCHAR(80),
            geometria VARCHAR(60),
            observacoes TEXT,
            endereco TEXT,
            -- Operational fields (not in the spreadsheet).
            grupo VARCHAR(20) CHECK (grupo IN ('base', 'analysis', 'exclusion')),
            data_type VARCHAR(10) NOT NULL DEFAULT 'vector'
                CHECK (data_type IN ('vector', 'raster')),
            backend_table VARCHAR(120),
            available BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    )
    op.execute(
        text("CREATE INDEX IF NOT EXISTS idx_layer_catalog_tema ON mesa_a.layer_catalog (tema);")
    )
    op.execute(
        text("CREATE INDEX IF NOT EXISTS idx_layer_catalog_grupo ON mesa_a.layer_catalog (grupo);")
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS mesa_a.layer_catalog;"))
