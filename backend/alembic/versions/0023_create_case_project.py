"""create Caso/Projeto domain (UML: Projeto → SearchRegion → CandidateSites)

Models the MESA case as a first-class domain on top of the existing
`assessments` rows (which already hold the candidate-site layout: geometry,
width/height/angle). A nullable FK on `assessments` links a site to a case, so
standalone assessments keep working (projeto_id NULL) and a case can adopt them.

Revision ID: 0023
Revises: 0022
Create Date: 2026-07-15
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.projeto (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(120) NOT NULL,
            descricao TEXT,
            coordenador_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            estado_uf VARCHAR(2),
            municipio_ibge_code VARCHAR(7),
            status VARCHAR(20) NOT NULL DEFAULT 'iniciado'
                CHECK (status IN ('iniciado', 'em_analise', 'campo', 'concluido')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    )
    op.execute(
        text("CREATE INDEX IF NOT EXISTS idx_projeto_status ON mesa_a.projeto (status);")
    )
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_projeto_municipio "
            "ON mesa_a.projeto (municipio_ibge_code);"
        )
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.search_region (
            id SERIAL PRIMARY KEY,
            projeto_id INTEGER NOT NULL REFERENCES mesa_a.projeto(id) ON DELETE CASCADE,
            crs VARCHAR(20) NOT NULL DEFAULT 'EPSG:4674',
            center_lat NUMERIC(9, 6),
            center_lon NUMERIC(9, 6),
            radius_m NUMERIC(12, 2),
            geom GEOMETRY(POLYGON, 4674),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    )
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_search_region_geom "
            "ON mesa_a.search_region USING GIST (geom);"
        )
    )

    # Extend assessments: link a candidate site to a case (nullable, backward
    # compatible) plus per-site status/violation/observation.
    op.execute(
        text("""
        ALTER TABLE assessments
            ADD COLUMN IF NOT EXISTS projeto_id INTEGER
                REFERENCES mesa_a.projeto(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS site_status VARCHAR(20) NOT NULL DEFAULT 'candidato'
                CHECK (site_status IN ('candidato', 'descartado', 'selecionado', 'campo')),
            ADD COLUMN IF NOT EXISTS avoidance_violation BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS observacao TEXT;
    """)
    )
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_assessments_projeto_id "
            "ON assessments (projeto_id);"
        )
    )


def downgrade() -> None:
    op.execute(
        text("""
        ALTER TABLE assessments
            DROP COLUMN IF EXISTS projeto_id,
            DROP COLUMN IF EXISTS site_status,
            DROP COLUMN IF EXISTS avoidance_violation,
            DROP COLUMN IF EXISTS observacao;
    """)
    )
    op.execute(text("DROP TABLE IF EXISTS mesa_a.search_region;"))
    op.execute(text("DROP TABLE IF EXISTS mesa_a.projeto;"))
