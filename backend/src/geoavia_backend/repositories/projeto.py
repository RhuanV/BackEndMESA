"""Persistence for the Caso/Projeto domain (mesa_a.projeto + search_region).

All queries are parameterized. Candidate sites are the existing `assessments`
rows linked by a nullable projeto_id.
"""

from __future__ import annotations

from geoavia_backend.core.db import cursor

_PROJETO_COLUMNS = (
    "id, nome, descricao, coordenador_id, created_by, estado_uf, "
    "municipio_ibge_code, status, created_at, updated_at"
)


class ProjetoRepository:
    def insert(
        self,
        nome: str,
        descricao: str | None,
        coordenador_id: int | None,
        created_by: int | None,
        estado_uf: str | None,
        municipio_ibge_code: str | None,
    ) -> dict:
        with cursor(dict_rows=True) as cur:
            cur.execute(
                f"""
                INSERT INTO mesa_a.projeto
                    (nome, descricao, coordenador_id, created_by, estado_uf, municipio_ibge_code)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING {_PROJETO_COLUMNS};
                """,
                (nome, descricao, coordenador_id, created_by, estado_uf, municipio_ibge_code),
            )
            return dict(cur.fetchone())

    def list(self, status: str | None = None) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if status:
            clauses.append("status = %s")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with cursor(dict_rows=True) as cur:
            cur.execute(
                f"""
                SELECT {_PROJETO_COLUMNS},
                    (SELECT COUNT(*) FROM assessments a
                      WHERE a.projeto_id = projeto.id) AS site_count
                FROM mesa_a.projeto
                {where}
                ORDER BY created_at DESC;
                """,
                tuple(params),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_by_id(self, projeto_id: int) -> dict | None:
        with cursor(dict_rows=True) as cur:
            cur.execute(
                f"SELECT {_PROJETO_COLUMNS} FROM mesa_a.projeto WHERE id = %s;", (projeto_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def update(self, projeto_id: int, nome: str, descricao: str | None) -> bool:
        with cursor() as cur:
            cur.execute(
                """
                UPDATE mesa_a.projeto
                   SET nome = %s, descricao = %s, updated_at = NOW()
                 WHERE id = %s;
                """,
                (nome, descricao, projeto_id),
            )
            return cur.rowcount > 0

    def update_status(self, projeto_id: int, status: str) -> bool:
        with cursor() as cur:
            cur.execute(
                "UPDATE mesa_a.projeto SET status = %s, updated_at = NOW() WHERE id = %s;",
                (status, projeto_id),
            )
            return cur.rowcount > 0

    # --- Candidate sites (assessments linked to the case) ---
    def list_sites(self, projeto_id: int) -> list[dict]:
        with cursor(dict_rows=True) as cur:
            cur.execute(
                """
                SELECT id, site_name, site_status, avoidance_violation, observacao,
                       latitude, longitude, ST_AsGeoJSON(geom) AS geometry_geojson,
                       created_at
                  FROM assessments
                 WHERE projeto_id = %s
                 ORDER BY created_at DESC;
                """,
                (projeto_id,),
            )
            rows = []
            for r in cur.fetchall():
                d = dict(r)
                d["geometry"] = d.pop("geometry_geojson", None)
                rows.append(d)
            return rows

    def link_site(self, projeto_id: int, assessment_id: int) -> bool:
        with cursor() as cur:
            cur.execute(
                "UPDATE assessments SET projeto_id = %s WHERE id = %s;",
                (projeto_id, assessment_id),
            )
            return cur.rowcount > 0

    def assessment_exists(self, assessment_id: int) -> bool:
        with cursor(dict_rows=True) as cur:
            cur.execute("SELECT 1 FROM assessments WHERE id = %s;", (assessment_id,))
            return cur.fetchone() is not None
