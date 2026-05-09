COMPOSE = docker compose

.PHONY: build up down logs ps shell migrate makemigrations superuser test sandbox-image clean

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec django-web python manage.py shell

bash:
	$(COMPOSE) exec django-web bash

migrate:
	$(COMPOSE) exec django-web python manage.py migrate

makemigrations:
	$(COMPOSE) exec django-web python manage.py makemigrations

# First-time setup: create migration files for all first-party apps, then apply.
init-db:
	$(COMPOSE) exec django-web python manage.py makemigrations \
	    authentication classrooms assignments submissions execution gamification
	$(COMPOSE) exec django-web python manage.py migrate

superuser:
	$(COMPOSE) exec django-web python manage.py createsuperuser

# Seed the exercise library (60 exercises across python/web × easy/med/hard)
seed:
	$(COMPOSE) exec django-web python manage.py seed_exercises

# One-shot first-boot: build images, migrate, seed library
bootstrap:
	$(COMPOSE) build
	$(COMPOSE) up -d postgres redis
	docker build -t educoder/sandbox-python:latest ./sandbox-images/python
	$(COMPOSE) up -d
	$(COMPOSE) exec django-web python manage.py makemigrations \
	    authentication classrooms exercises assignments submissions execution realtime gamification || true
	$(COMPOSE) exec django-web python manage.py migrate
	$(COMPOSE) exec django-web python manage.py seed_exercises
	@echo ""
	@echo "✓ educoder ready at http://localhost:8090"
	@echo "  Create a superuser: make superuser"

collectstatic:
	$(COMPOSE) exec django-web python manage.py collectstatic --noinput

test:
	$(COMPOSE) exec django-web pytest

# Build the inner sandbox image used by execution-runner
sandbox-image:
	docker build -t educoder/sandbox-python:latest ./sandbox-images/python

clean:
	$(COMPOSE) down -v
