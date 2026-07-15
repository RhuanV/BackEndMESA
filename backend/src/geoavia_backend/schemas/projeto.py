"""Pydantic request models for the Caso/Projeto endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProjetoCreateRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    descricao: str | None = Field(default=None)
    coordenador_id: int | None = None
    estado_uf: str | None = Field(default=None, max_length=2)
    municipio_ibge_code: str | None = Field(default=None, max_length=7)


class ProjetoUpdateRequest(BaseModel):
    nome: str | None = Field(default=None, max_length=120)
    descricao: str | None = None


class StatusChangeRequest(BaseModel):
    status: Literal["iniciado", "em_analise", "campo", "concluido"]


class LinkSiteRequest(BaseModel):
    assessment_id: int
