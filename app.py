#!flask/bin/python
from flask import Flask, jsonify, abort, make_response, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'impharm.c8sfa07wbzip.us-west-2.rds.amazonaws.com:5432'
db = SQLAlchemy(app)

class Drug(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    quantity = db.Column(db.Integer)
    transactions = db.relationship('Transaction', backref='drug_id')

    def __init__(self, name, quantity):
        self.name = name
        self.quantity = quantity

    def __repr__(self):
        return '<Drug Name %r, Quantity %r>' % (self.name, self.quantity)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer)
    drug_id = db.Column(db.Integer, db.ForeignKey('drug.id'))
    quantity = db.Column(db.Integer)
    date = db.Column(db.DateTime)

    def __init__(self, patient_id, drug_id, quantity):
        self.patient_id = patient_id
        self.drug_id = drug_id
        self.quantity = quantity
        self.date = datetime.datetime.now()

    def __repr__(self):
        return '<Patient ID %r, Drug ID %r, Quantity %r, Date %r>' % (self.patient_id, self.drug_id, self.quantity, self.date)

"""
do we need to intialize the db, or will it all be sitting fancily in aws?
@app.route('/initialize')
def initialize_db():
    db.create_all()
"""

@app.route('/list_drugs', methods=['GET'])
def list_drugs():
    drugs_list = Drug.query.all()
    if len(drugs_list) == 0:
        abort(404)
    #just works for 3 for initial testing, gotta figure out how to set up return statement better
    return jsonify({'1': drugs_list[0], '2': drugs_list[1], '3': drugs_list[2]})

@app.route('/query_drug/', methods=['GET'])
def query_drug():
    if not request.json or not 'name' in request.json:
        abort(400)
    drug = Drug.query.filter_by(name=request.json['name']).first()
    if drug is None:
        abort(404)
    return jsonify({'drug_id': drug.id, 'name': drug.name, 'quantity': drug.quantity})

@app.route('/add_drug/<int:quantity>', methods=['POST'])
def add_drug():
    if not request.json or not 'name' in request.json:
        abort(400)
    new_drug = Drug(request.json['name'], quantity)
    db.session.add(new_drug)
    db.session.commit()
    return jsonify({'drug_id': new_drug.id, 'name': new_drug.name, 'quantity': new_drug.quantity}), 201

@app.route('/increase_drug_quantity/<int:quantity>', methods=['PUT'])
def increase_drug_quantity():
    if not request.json or not 'name' in request.json:
        abort(400)
    drug = Drug.query.filter_by(name=request.json['name']).first()
    if drug is None:
        abort(404)
    updated_drug = Drug(request.json['name'], drug.quantity + quantity)
    db.session.delete(drug)
    db.session.add(updated_drug)
    db.session.commit()
    return jsonify({'drug_id': updated_drug.id, 'name': updated_drug.name, 'quantity': updated_drug.quantity})

@app.route('/delete_drug', methods=['DELETE'])
def delete_drug():
    if not request.json or not 'name' in request.json:
        abort(400)
    drug = Drug.query.filter_by(drug_name=request.json['name'])
    if drug is None:
        abort(404)
    db.session.delete(drug)
    db.session.commit()
    return jsonify({'result': True})

@app.route('/list_transactions', methods=['GET'])
def list_transactions():
    trans_list = Transaction.query.all()
    if len(trans_list) == 0:
        abort(404)
    #just works for 3 for initial testing, gotta figure out how to set up return statement better
    return jsonify({'1': trans_list[0], '2': trans_list[1], '3': trans_list[2]})

@app.route('/query_patient/<int:patient_id>', methods=['GET'])
def query_patient():
    patient_list = Transaction.query.filter_by(patient_id=patient_id).all()
    if len(patient_list) == 0:
        abort(404)
    #just works for 3 for initial testing, gotta figure out how to set up return statement better
    return jsonify({'1': patient_list[0], '2': patient_list[1], '3': patient_list[2]})

@app.route('/query_transaction/<int:transaction_id>', methods['GET'])
def query_transaction():
    trans = Transaction.query.get(transaction_id)
    if trans is None:
        abort(404)
    drug = Drug.query.get(trans.drug_id)
    return jsonify({'transaction_id': trans.id, 'patient_id': trans.patient_id, 'drug_name': drug.name, 'quantity': trans.quantity}), 201

@app.route('/make_transaction/<int:patient_id>/<int:quantity>', methods=['POST'])
def add_transaction():
    if not request.json or not 'drug_name' in request.json:
        abort(400)
    drug = Drug.query.filter_by(name=request.json['drug_name']).first()
    if drug is None:
        abort(404)
    if drug.quantity - quantity < 0:
        abort(409)
    new_trans = Transaction(patient_id, drug.id, quantity)
    updated_drug = Drug(drug.name, drug.quantity - quantity)
    db.session.add(new_trans)
    db.session.delete(drug)
    db.session.add(updated_drug)
    db.session.commit()
    return jsonify({'transaction_id': new_trans.id, 'patient_id': new_trans.patient_id, 'drug_name': drug.name, 'quantity': new_trans.quantity}), 201

@app.route('/update_transaction_quantity/<int:transaction_id>/<int:quantity>', methods=['PUT'])
def update_transaction_quantity():
    trans = Transaction.query.get(transaction_id)
    if trans is None:
        abort(404)
    drug = Drug.query.get(trans.id)
    new_drug = Drug(drug.name, drug.quantity + trans.quantity - quantity)
    new_trans = Transaction(trans.patient_id, new_drug.id, quantity)
    db.session.delete(trans)
    db.session.add(new_trans)
    db.session.delete(drug)
    db.session.add(new_drug)
    db.session.commit()
    return jsonify({'transaction_id': new_trans.id, 'patient_id': new_trans.patient_id, 'drug_name': new_drug.name, 'quantity': new_trans.quantity})

@app.route('/delete_transaction/<int:transaction_id>', methods=['DELETE'])
def delete_transaction():
    trans = Transaction.query.get(transaction_id)
    if trans is None:
        abort(404)
    drug = Drug.query.get(trans.drug_id)
    new_drug = Drug(drug.name, drug.quantity + trans.quantity)
    db.session.delete(trans)
    db.session.delete(drug)
    db.session.add(new_drug)
    db.session.commit()
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
