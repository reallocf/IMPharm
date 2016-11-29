set_up:
	cp ~/Library/Python/2.7/bin/virtualenv .
	./virtualenv flask
	rm virtualenv
	flask/bin/pip install flask
	flask/bin/pip install flask-sqlalchemy