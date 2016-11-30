set_up:
	pip install flask --user
	pip install psycopg2 --user
	pip install twilio --user

query_drug:
	curl -i -H "Content-Type: application/json" -X GET -d '{"name": "codeine"}' http://localhost:5000/query_drug/

add_drug:
	curl -i -H "Content-Type: application/json" -X POST -d '{"name": "test_drug", "quantity": 800000, "price": 95}' http://localhost:5000/add_drug/

increase_drug_quantity:
	curl -i -H "Content-Type: application/json" -X PUT -d '{"name": "test_drug", "quantity": 800}' http://localhost:5000/change_drug_quantity/