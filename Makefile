run:
	uvicorn main:app --host 0.0.0.0 --port 8080

dev:
	APP__BROWSER__MODE=disabled APP__LOG__LEVEL=DEBUG uvicorn main:app --reload --port 8080

docker-build:
	docker build -t webclip:latest .

docker-up:
	docker compose up --build

test:
	pytest -q 