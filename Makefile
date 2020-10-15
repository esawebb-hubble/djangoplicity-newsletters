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

futurize-stage1:
	docker exec -it djangoplicity-newsletters futurize --stage1 -w -n .

futurize-stage2:
	docker exec -it djangoplicity-newsletters futurize --stage2 --nofix=newstyle -w -n .
