#!/usr/bin/python
from flask import Flask, jsonify, abort, make_response, request, render_template, redirect
import psycopg2
import datetime
from twilio.rest import TwilioRestClient
import smtplib

app = Flask(__name__)

# XXX out secure things after demo!!

conn_string = "host='impharm.c8sfa07wbzip.us-west-2.rds.amazonaws.com' dbname='pharm' user='pharmacist' password='pharmacist'"
conn = psycopg2.connect(conn_string)
cursor = conn.cursor()

account_sid = "ACc6ff8b8c0b4becff5903dc12815677c8"
auth_token = "8ff5dfef459fa32a58a8934e4a19b7c7"
client = TwilioRestClient(account_sid, auth_token)


def format_msg(orders):
    email_msg = "Order ID	Date					Drug ID		Quantity	Fulfiled\n"
    for i in orders:
        for j in i:
            email_msg += str(j)
            email_msg += "		"
        email_msg += str("\n")
    send_email(email_msg)

def grab_orders():
    cursor.execute('SELECT * FROM "order"')
    orders = cursor.fetchall()
    format_msg(orders)

def send_email(msg):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("throw586plus1@gmail.com", "password123!")
    i = 0
    s.sendmail("throw586plus1@gmail.com", "z.smith32@gmail.com", msg)
    s.quit()


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
    if not request.form or not 'drug_name' in request.form or not 'quantity' in request.form or not 'patient_name' in request.form:
        abort(400)
    cursor.execute("SELECT * FROM drug WHERE name = '%s'" % (request.form['drug_name']))
    drug = cursor.fetchall()[0]
    if (drug is None):
        abort(404)
    cursor.execute("SELECT * FROM patient WHERE name = '%s'" % (request.form['patient_name']))
    patients = cursor.fetchall()
    if (len(patients) == 0):
        cursor.execute("INSERT INTO patient (name) VALUES ('%s')" % (request.form['patient_name']))
        cursor.execute("SELECT * FROM patient WHERE name = '%s'" % (request.form['patient_name']))
        patient = cursor.fetchall()[0]
    else:
        patient  = patients[0]
    new_quantity = drug[2] - int(request.form['quantity'])
    cursor.execute("UPDATE drug SET quantity = %s WHERE id = %s" % (new_quantity, drug[0]))
    cursor.execute("INSERT INTO transaction (patient_id, date, drug_id, quantity) VALUES (%s, current_timestamp, %s, %s)" % (patient[0], drug[0], int(request.form['quantity'])))
    if drug[2] - int(request.form['quantity']) < drug[4]:
        order_amount = ((drug[4] / 7) * 3) - (drug[2] / 3)
        cursor.execute('INSERT INTO "order" (date, drug_id, quantity, fufiled) VALUES (current_timestamp, %s, %s, %s)' % (drug[0], order_amount, False))
    	message = client.messages.create(to="+14129533098", from_="+15102579863", body="Hey, it's IMPharm. We have ordered %s on your behalf becuase you were running low. Have a good day!" % (drug[1]))
        conn.commit()
        grab_orders()
        return redirect("http://127.0.0.1:5000/ordersview/")
    else:
        conn.commit()
        return redirect("http://127.0.0.1:5000/dbview/")

@app.route('/ordersview/', methods=['GET'])
def view_orders():
    cursor.execute('SELECT * FROM "order"')
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
