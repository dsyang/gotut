init:
	pip install -r requirements.txt --use-mirrors

test:
	nosetests -v tests

configure:
	python configure.py

deploy:
	pip freeze > requirements.txt
	git commit -am "Automated commit before pushing to heroku"
	git push heroku
