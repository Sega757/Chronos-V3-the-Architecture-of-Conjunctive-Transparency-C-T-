-- Seed data for system calibration

INSERT INTO sites (domain, title, config_json, is_active) VALUES
('sccs-cognition.ai', 'Sovereign Cognitive Systems Hub', '{"theme": "dark", "locale": "ru_RU", "huber_delta": 1.35}', true),
('ace-engine.org', 'Autonomous Content Engine Portal', '{"theme": "light", "locale": "en_US", "huber_delta": 1.50}', true);

INSERT INTO categories (name, slug, frequency_type) VALUES
('Когнитивная Архитектура', 'cognitive-architecture', 'HF'),
('Двухпалатный Разум', 'bicameral-mind', 'MF'),
('Фильтрация Реальности', 'chronos-v3-filter', 'LF');

INSERT INTO articles (title, slug, summary, status, views_count, published_at, category_id, site_id) VALUES
('Архитектурный Манифест Суверенной Когнитивной Системы', 'sovereign-cognitive-architecture-manifesto', 'Детальный разбор двухпалатной архитектуры SCCS, механизмов C-T и детерминированной фильтрации Chronos V3.', 'published', 1420, '2026-08-01 10:00:00', 1, 1),
('Детерминированная Стерилизация Шума в Chronos V3', 'chronos-v3-noise-sterilization', 'Применение функции потерь Хубера и метода ALS-IRLS для подавления тяжелых хвостов в данных.', 'published', 890, '2026-08-02 12:30:00', 3, 1);

INSERT INTO article_blocks (article_id, block_type, content, position) VALUES
(1, 'text', 'Современные фундаментальные исследования в области ИИ обращаются к двухпроцессной теории, разделяющей быструю Систему 1 и рефлексивную Систему 2.', 1),
(1, 'quote', 'Conjunctive Transparency (C-T) требует одновременного выполнения условий внутренней логической целостности и внешней фактологической подлинности.', 2),
(2, 'code', 'def compute_huber_loss(residuals, delta=1.35):\n    abs_res = np.abs(residuals)\n    mask = abs_res <= delta\n    return np.where(mask, 0.5 * (residuals ** 2), delta * (abs_res - 0.5 * delta))', 1);

INSERT INTO generation_logs (model_used, prompt_hash, prompt_text, response_text, execution_time_ms, status, created_at) VALUES
('Neocortex-Chronos-V3-Hybrid', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'Сгенерировать архитектурный манифест SCCS с учетом C-T и Huber Loss', 'Успешно сгенерирован лонгрид ID 1. Все логические швы изолированы.', 245, 'success', '2026-08-21 07:00:00'),
('Chronos-Logos-Sterilizer', 'f2d81a26030d94f24381e27a00160a37269e60e306a728ddd718d9f109c31327', 'Провести очистку телеметрии и сформировать Knowledge Object', 'Сформирован Knowledge Object KO-7890-XY. Residual delta = 0.042.', 112, 'success', '2026-08-21 07:15:00');

INSERT INTO metrics (article_id, views, clicks, avg_time_seconds, bounce_rate) VALUES
(1, 1420, 310, 245.5, 0.12),
(2, 890, 185, 190.2, 0.18);
