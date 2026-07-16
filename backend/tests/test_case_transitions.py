"""Pure tests for the Caso/Projeto lifecycle transition rules (no DB)."""

from geoavia_backend.services.projeto import STATUS_ORDER, is_valid_transition


def test_forward_adjacent_transitions_allowed():
    assert is_valid_transition("iniciado", "em_analise")
    assert is_valid_transition("em_analise", "campo")
    assert is_valid_transition("campo", "concluido")


def test_backward_adjacent_transitions_allowed():
    assert is_valid_transition("em_analise", "iniciado")
    assert is_valid_transition("concluido", "campo")


def test_skipping_states_rejected():
    assert not is_valid_transition("iniciado", "campo")
    assert not is_valid_transition("iniciado", "concluido")
    assert not is_valid_transition("em_analise", "concluido")


def test_same_state_and_unknown_rejected():
    assert not is_valid_transition("campo", "campo")
    assert not is_valid_transition("iniciado", "bogus")
    assert not is_valid_transition("bogus", "campo")


def test_status_order_is_the_documented_lifecycle():
    assert STATUS_ORDER == ["iniciado", "em_analise", "campo", "concluido"]
