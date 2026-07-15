"""Business logic for the Caso/Projeto domain and its lifecycle."""

from __future__ import annotations

from geoavia_backend.core.roles import ADMIN_ROLES
from geoavia_backend.repositories.projeto import ProjetoRepository

# Ordered lifecycle. A transition is allowed only between adjacent states
# (forward or back one step): iniciado ⇄ em_analise ⇄ campo ⇄ concluido.
STATUS_ORDER = ["iniciado", "em_analise", "campo", "concluido"]


def is_valid_transition(current: str, target: str) -> bool:
    """True if `target` is adjacent to `current` in the lifecycle."""
    if current not in STATUS_ORDER or target not in STATUS_ORDER:
        return False
    return abs(STATUS_ORDER.index(target) - STATUS_ORDER.index(current)) == 1


def _serialize(row: dict) -> dict:
    """Maps a DB row to the camelCase shape the frontend expects."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row.get("descricao"),
        "coordenadorId": row.get("coordenador_id"),
        "createdBy": row.get("created_by"),
        "estadoUf": row.get("estado_uf"),
        "municipioIbgeCode": row.get("municipio_ibge_code"),
        "status": row["status"],
        "siteCount": row.get("site_count", 0),
        "createdAt": row.get("created_at").isoformat() if row.get("created_at") else None,
        "updatedAt": row.get("updated_at").isoformat() if row.get("updated_at") else None,
    }


class ProjetoService:
    def __init__(self, repo: ProjetoRepository | None = None) -> None:
        self.repo = repo or ProjetoRepository()

    def create(self, data: dict, actor: dict) -> dict:
        nome = (data.get("nome") or "").strip()
        if not nome:
            raise ValueError("O nome do caso é obrigatório")
        row = self.repo.insert(
            nome=nome,
            descricao=(data.get("descricao") or "").strip() or None,
            coordenador_id=data.get("coordenador_id"),
            created_by=self._actor_id(actor),
            estado_uf=(data.get("estado_uf") or "").strip().upper()[:2] or None,
            municipio_ibge_code=(data.get("municipio_ibge_code") or "").strip() or None,
        )
        return _serialize(row)

    def list(self, status: str | None = None) -> list[dict]:
        return [_serialize(r) for r in self.repo.list(status=status)]

    def get(self, projeto_id: int) -> dict | None:
        row = self.repo.get_by_id(projeto_id)
        if not row:
            return None
        result = _serialize(row)
        sites = self.repo.list_sites(projeto_id)
        result["sites"] = sites
        result["siteCount"] = len(sites)
        return result

    def update(self, projeto_id: int, data: dict) -> dict:
        row = self.repo.get_by_id(projeto_id)
        if not row:
            raise ValueError("Caso não encontrado")
        nome = (data.get("nome") or row["nome"]).strip()
        descricao = data.get("descricao")
        descricao = descricao.strip() if isinstance(descricao, str) else row.get("descricao")
        self.repo.update(projeto_id, nome, descricao or None)
        return _serialize(self.repo.get_by_id(projeto_id))

    def change_status(self, projeto_id: int, new_status: str, actor: dict) -> dict:
        row = self.repo.get_by_id(projeto_id)
        if not row:
            raise ValueError("Caso não encontrado")
        self._require_ownership(row, actor)
        if not is_valid_transition(row["status"], new_status):
            raise ValueError(
                f"Transição inválida: {row['status']} → {new_status}. "
                "Só é permitido avançar/retroceder um estado por vez."
            )
        self.repo.update_status(projeto_id, new_status)
        updated = _serialize(self.repo.get_by_id(projeto_id))
        updated["previousStatus"] = row["status"]
        return updated

    def link_site(self, projeto_id: int, assessment_id: int) -> dict:
        if self.repo.get_by_id(projeto_id) is None:
            raise ValueError("Caso não encontrado")
        if not self.repo.assessment_exists(assessment_id):
            raise ValueError("Sítio (assessment) não encontrado")
        self.repo.link_site(projeto_id, assessment_id)
        return {"projetoId": projeto_id, "assessmentId": assessment_id}

    def list_sites(self, projeto_id: int) -> list[dict]:
        return self.repo.list_sites(projeto_id)

    @staticmethod
    def _actor_id(actor: dict) -> int | None:
        sub = str(actor.get("sub", ""))
        return int(sub) if sub.isdigit() else None

    def _require_ownership(self, projeto_row: dict, actor: dict) -> None:
        """Only the case coordinator or an admin/dev may transition status."""
        if actor.get("role") in ADMIN_ROLES:
            return
        if projeto_row.get("coordenador_id") == self._actor_id(actor):
            return
        raise ValueError("Apenas o coordenador do caso ou um administrador pode alterar o status")
