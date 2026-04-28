.PHONY: setup run stop logs test clean

setup:
	cp .env.example .env
	docker compose build

run:
	docker compose up -d
	@echo "\n✅ Pipeline rodando!"
	@echo "   Dashboard:  http://localhost:8501"
	@echo "   Adminer DB: http://localhost:8080"

stop:
	docker compose down

logs:
	docker compose logs -f app

test:
	pytest tests/ -v --tb=short

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete
