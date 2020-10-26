bash:
	docker exec -it djangoplicity-newsletters bash

test:
	docker exec -it djangoplicity-newsletters env DJANGO_SETTINGS_MODULE="test_project.test_settings" coverage run --source='.' manage.py test

coverage-html:
	docker exec -it djangoplicity-newsletters coverage html
	open ./htmlcov/index.html

test-python27:
	docker exec -it djangoplicity-newsletters tox -e py27-django111

migrate:
	docker exec -it djangoplicity-newsletters python manage.py migrate

makemigrations:
	docker exec -it djangoplicity-newsletters python manage.py makemigrations

test_newsletter:
	docker exec -it djangoplicity-newsletters env DJANGO_SETTINGS_MODULE="test_project.test_settings" coverage run --source='.' manage.py test tests.test_newsletter

up:
	docker-compose --env-file ./test_project/.env up --build