#!/usr/bin/python
from flask import Flask, jsonify, abort, make_response, request, render_template
import psycopg2
from datetime import date
from twilio.rest import TwilioRestClient

app = Flask(__name__)

# XXX out secure things after demo!!

conn_string = "host='impharm.c8sfa07wbzip.us-west-2.rds.amazonaws.com' dbname='pharm' user='pharmacist' password='pharmacist'"
conn = psycopg2.connect(conn_string)
cursor = conn.cursor()

account_sid = "ACc6ff8b8c0b4becff5903dc12815677c8"
auth_token = "8ff5dfef459fa32a58a8934e4a19b7c7"
client = TwilioRestClient(account_sid, auth_token)

@app.route('/dbview/', methods=['GET'])
def view_db():
    cursor.execute("SELECT * FROM drug")
    drugs_list = cursor.fetchall()
    if len(drugs_list) == 0:
        abort(404)
    drugs_formatted = []
    for i in range(len(drugs_list)):
        drugs_formatted.append({'drug_id': drugs_list[i][0],
                                'name': drugs_list[i][1],
                                'quantity': drugs_list[i][2],
                                'price': drugs_list[i][3],
                                'minimum': drugs_list[i][4]
                                })
    cursor.execute("SELECT * FROM transaction")
    transactions_list = cursor.fetchall()
    if len(transactions_list) == 0:
        abort(404)
    transactions_formatted = []
    for i in range(len(transactions_list)):
        cursor.execute("SELECT * FROM patient WHERE id in ('%s')" % (transactions_list[i][1]))
        patient = cursor.fetchall()[0]
        cursor.execute("SELECT * FROM drug WHERE id in ('%s')" % (transactions_list[i][3]))
        drug = cursor.fetchall()[0]
        transactions_formatted.append({'transaction_id': transactions_list[i][0],
                                       'patient_name': patient[1],
                                       'date': transactions_list[i][2],
                                       'drug_name': drug[1],
                                       'quantity': transactions_list[i][4]
                                       })
    ret = []
    ret.append(drugs_formatted)
    ret.append(transactions_formatted)
    return render_template('demo.html', ret=ret)

@app.route('/addData/', methods=['POST'])
def post_db():
    if not request.form or not 'drug_name' in request.form or not 'quantity' in request.form or not 'patient_id' in request.form:
        abort(400)
    cursor.execute("SELECT * FROM drug")
    drugs_list = cursor.fetchall()
    if (len(drugs_list) == 0):
        abort(404)
    i = 0
    while i in range(len(drugs_list)):
        if drugs_list[i][1] == request.form['drug_name']:
            drug = drugs_list[i]
            break
        i += 1
    #if drug[2] - int(request.form['quantity']) < drug[4]:
    #    abort(409)
    	#who we texting? Make sure to add them as a verified number on twilio
    	#message = client.messages.create(to="+15033200439", from_="+15102579863", body="Test!")
    new_quantity = drug[2] - int(request.form['quantity'])
    cursor.execute("UPDATE drug SET quantity = %s WHERE id = %s", (new_quantity, drug[0]))
    cursor.execute("INSERT INTO transaction (patient_id, date, drug_id, quantity) VALUES (%s, NULL, %s, %s)" % (int(request.form['patient_id']), drug[0], int(request.form['quantity'])))
    conn.commit()
    return jsonify({'result': True}), 201

@app.route('/ordersview/', methods=['GET'])
def view_orders():
    cursor.execute("SELECT * FROM order")
    orders_list = cursor.fetchall()
    if len(orders_list) == 0:
        abort(404)
    ret = []
    for i in range(len(orders_list)):
        ret.append({'id': orders_list[i][0],
                    'date': orders_list[i][1],
                    'drug_id': orders_list[i][2],
                    'quantity': orders_list[i][3],
                    'fulfilled': orders_list[i][4]
                    })
    return jsonify(ret)

@app.route('/list_drugs/', methods=['GET'])
def list_drugs():
    cursor.execute("SELECT * FROM drug")
    drugs_list = cursor.fetchall()
    if len(drugs_list) == 0:
        abort(404)
    ret = []
    for i in range(len(drugs_list)):
        ret.append({'id': drugs_list[i][0],
                    'name': drugs_list[i][1],
                    'quantity': drugs_list[i][2],
                    'price': drugs_list[i][3],
                    'minimum': drugs_list[i][4]
                    })
    return jsonify(ret)

@app.route('/query_drug/', methods=['GET'])
def query_drug():
    cursor.execute("SELECT * FROM drug WHERE name IN ('%s')" % (request.json['name']))
    drug = cursor.fetchall()[0]
    if drug is None:
        abort(404)
    return jsonify({'id': drug[0],
                    'name': drug[1],
                    'quantity': drug[2],
                    'price': drug[3],
                    'minimum':drug[4],
                    })

@app.route('/add_drug/', methods=['POST'])
def add_drug():
    if not request.json or not 'name' in request.json or not 'quantity' in request.json or not 'price' in request.json:
        abort(400)
    cursor.execute("INSERT INTO drug (name, quantity, price, minimum) VALUES ('%s', %s, %s, 0)" % (request.json['name'], request.json['quantity'], request.json['price']))
    conn.commit()
    return jsonify({'result': True}), 201

@app.route('/change_drug_quantity/', methods=['PUT'])
def increase_drug_quantity():
    if not request.json or not 'name' in request.json or not 'quantity' in request.json:
        abort(400)
    cursor.execute("SELECT * FROM drug WHERE name IN ('%s')" % (request.json['name']))
    drug = cursor.fetchall()[0]
    if drug is None:
        abort(404)
    new_quantity = drug[2] + request.json['quantity']
    cursor.execute("UPDATE drug SET quantity = %s WHERE name = %s", (new_quantity, request.json['name']))
    conn.commit()
    return jsonify({'drug_id': drug[0],
                    'name': drug[1],
                    'quantity': new_quantity,
                    'minimum': drug[3]
                    })

@app.route('/delete_drug/', methods=['DELETE'])
def delete_drug():
    if not request.json or not 'name' in request.json:
        abort(400)
    cursor.execute("SELECT * FROM drug WHERE name IN ('%s')" % (request.json['name']))
    drug = cursor.fetchall()[0]
    if drug is None:
        abort(404)
    cursor.execute("DELETE FROM drug WHERE name = '%s'" % (request.json['name']))
    conn.commit()
    return jsonify({'result': True})

@app.route('/list_transactions/', methods=['GET'])
def list_transactions():
    cursor.execute("SELECT * FROM transaction")
    transactions_list = cursor.fetchall()
    if len(transactions_list) == 0:
        abort(404)
    ret = []
    for i in range(len(transactions_list)):
        cursor.execute("SELECT * FROM patient WHERE id IN ('%s')" % (transactions_list[i][1]))
        patient = cursor.fetchall()[0]
        cursor.execute("SELECT * FROM drug WHERE id IN ('%s')" % (transactions_list[i][3]))
        drug = cursor.fetchall()[0]
        ret.append({'transaction_id': transactions_list[i][0],
                    'patient_name': patient[1],
                    'date': transactions_list[i][2],
                    'drug_name': drug[1],
                    'quantity': transactions_list[i][4]
                    })
    return jsonify(ret)

@app.route('/query_transaction/', methods=['GET'])
def query_transaction():
    if not request.json or not 'transaction_id' in request.json:
        abort (400)
    cursor.execute("SELECT * FROM transaction WHERE id IN ('%s')" % (request.json['transaction_id']))
    transaction = cursor.fetchall()[0]
    if transaction is None:
        abort(404)
    cursor.execute("SELECT * FROM patient WHERE id IN ('%s')" % (transaction[1]))
    patient = cursor.fetchall()[0]
    cursor.execute("SELECT * FROM drug WHERE id IN ('%s')" % (transaction[3]))
    drug = cursor.fetchall()[0]
    return jsonify({'transaction_id': transaction[0],
                    'patient_name': patient[1],
                    'date': transaction[2],
                    'drug_name': drug[1],
                    'quantity': transaction[4]
                    })

#need to test
@app.route('/make_transaction/', methods=['POST'])
def add_transaction():
    if not request.json or not 'drug_name' in request.json or not 'quantity' in request.json or not 'patient_id' in request.json:
        abort(400)
    cursor.execute("SELECT * FROM transaction WHERE name IN ('%s')" % (request.json['drug_name']))
    drug = cursor.fetchall()[0]
    if drug is None:
        abort(404)
    if drug[2] - request.json['quantity'] < 0:
        abort(409)
    new_quantity = drug[2] - request.json['quantity']
    cursor.execute("UPDATE drug SET quantity = %s WHERE id = %s" % (new_quantity, drug[0]))
    cursor.execute("INSERT INTO transaction (patient_id, drug_name) VALUES ('%s', %s)" % (request.json['patient_id'], drug[1]))
    conn.commit()
    return jsonify({'result': True}), 201

#need to test
@app.route('/update_transaction_quantity/', methods=['PUT'])
def update_transaction_quantity():
    if not request.json or not 'transaction_id' in request.json or not 'quantity' in request.json:
        abort(400)
    cursor.execute("SELECT * FROM transaction WHERE id IN ('%s')" % (request.json['transaction_id']))
    transaction = cursor.fetchall()[0]
    if transaction is None:
        abort(404)
    cursor.execute("SELECT * FROM drug WHERE id IN ('%s')" % (transaction[3]))
    drug = cursor.fetchall()[0]
    new_quantity = drug[2] + transaction[4] - request.json(['quantity'])
    cursor.execute("UPDATE drug SET quantity = %s WHERE id = %s" % (new_quantity, drug[0]))
    cursor.execute("UPDATE transaction SET quantity = %s WHERE if = %s" % (request.json['quantity'], transaction[0]))
    conn.commit()
    cursor.execute("SELECT * FROM patient WHERE id IN ('%s')" % (transaction[1]))
    patient = cursor.fetchall()[0]
    return jsonify({'transaction_id': transaction[0],
                    'patient_name': patient[1],
                    'date': transaction[2],
                    'drug_name': drug[1],
                    'quantity': transaction[4]
                    })

#need to test
@app.route('/delete_transaction/', methods=['DELETE'])
def delete_transaction():
    if not request.json or not 'transaction_id' in request.json:
        abort(400)
    cursor.execute("SELECT * FROM transaction WHERE id IN ('%s')" % (request.json['transaction_id']))
    transaction = cursor.fetchall()[0]
    if transaction is None:
        abort(404)
    cursor.execute("SELECT * FROM drug WHERE id IN ('%s')" % (transaction[3]))
    drug = cursor.fetchall()[0]
    new_quantity = drug[2] + transaction[4]
    cursor.execute("UPDATE drug SET quantity = %s WHERE id = %s" % (new_quantity, drug[0]))
    cursor.execute("DELETE FROM transaction WHERE id = %s" % (transaction[0]))
    conn.commit()
    return jsonify({'result': True})

@app.errorhandler(400)
def incorrect_request(error):
    return make_response(jsonify({'error': 'Incorrect request, make sure formatting is proper'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Information not found'}), 404)

@app.errorhandler(409)
def out_of_stock(error):
    return make_response(jsonify({'error:': 'Not enough in stock'}), 409)

if __name__ == '__main__':
    app.run(debug=True)
