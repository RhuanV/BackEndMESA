-- Sprint 2 — Example data for the PO demo.
-- Real coordinates in Brazilian territory, plausible but fictitious values.
-- Consistent with the old MOCK_RESULTS from ResultsPanel so the frontend looks
-- familiar while the integration is validated.

INSERT INTO assessments (
    site_name, average_slope, urban_center_distance,
    has_obstacles, obstacle_description, estimated_cost,
    latitude, longitude, geom
) VALUES
    ('Sítio Aeroportuário Norte — Campinas', 2.5, 35.0,
     FALSE, NULL, 180000000.00,
     -22.9, -47.06, ST_SetSRID(ST_MakePoint(-47.06, -22.9), 4674)),

    ('Sítio Vale do Ribeira', 6.8, 80.0,
     FALSE, NULL, 240000000.00,
     -24.5, -47.8, ST_SetSRID(ST_MakePoint(-47.8, -24.5), 4674)),

    ('Sítio Planalto Central — Goiás', 4.2, 55.0,
     TRUE, 'Linha de transmissão a 4km', 210000000.00,
     -15.8, -49.3, ST_SetSRID(ST_MakePoint(-49.3, -15.8), 4674)),

    ('Sítio Litoral Sul — Florianópolis', 9.1, 22.0,
     TRUE, 'Relevo acidentado e área urbana próxima', 320000000.00,
     -27.6, -48.5, ST_SetSRID(ST_MakePoint(-48.5, -27.6), 4674)),

    ('Sítio Serra da Mantiqueira', 18.4, 65.0,
     TRUE, 'Cadeia montanhosa adjacente', 410000000.00,
     -22.4, -45.0, ST_SetSRID(ST_MakePoint(-45.0, -22.4), 4674))
ON CONFLICT DO NOTHING;
