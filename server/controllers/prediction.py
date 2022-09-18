from decimal import Decimal

from config.app import app
import mysql.connector
from flask import jsonify, request
from datetime import datetime
from keras.utils import pad_sequences
import pickle
import numpy as np
import tensorflow as tf

from keras.models import load_model

connect_to_matrix = mysql.connector.connect(
    host="localhost", user="root", password="", database="production_saer")
matrix_cursor = connect_to_matrix.cursor(buffered=True)

# @desc: Get all the tables and columns from a database
# @app.route('/tables-columns', methods=['POST'])
# def tables_columns():
#     if request.is_json:
#         host = request.json['host']
#         user = request.json['user']
#         password = request.json['password']
#         database = request.json['database']
#
#         try:
#             conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
#             cursor = conn.cursor()
#             cursor.execute("SHOW TABLES")
#             tables = cursor.fetchall()
#             tables_columns = []
#             for table in tables:
#                 cursor.execute("SHOW COLUMNS FROM {}".format(table[0]))
#                 columns = cursor.fetchall()
#                 # table and column name only
#                 tables_columns.append({'table': table[0], 'columns': [column[0] for column in columns]})
#             return jsonify(
#                 {'status': 'success', 'message': 'Tables and columns found', 'tables_columns': tables_columns})
#         except mysql.connector.Error as err:
#             return jsonify({'status': 'error', 'message': 'Connection failed: {}'.format(err)})
#     else:
#         return jsonify({'status': 'error', 'message': 'Invalid request'})


# @desc: Get all the data from a table
# @app.route('/data', methods=['POST'])
# def data():
#     if request.is_json:
#         host = request.json['host']
#         user = request.json['user']
#         password = request.json['password']
#         database = request.json['database']
#         table = request.json['table']
#
#         try:
#             conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
#             cursor = conn.cursor()
#             cursor.execute("SELECT * FROM {}".format(table))
#             data = cursor.fetchall()
#             return jsonify({'status': 'success', 'message': 'Data found', 'data': data})
#         except mysql.connector.Error as err:
#             return jsonify({'status': 'error', 'message': 'Connection failed: {}'.format(err)})
#     else:
#         return jsonify({'status': 'error', 'message': 'Invalid request'})


model = load_model("config/model.h5")
tokenizer = pickle.load(open("config/tokenizer.pickle", "rb"))


# @desc: Predict the sentiment of a text and return the result to the database with a new column containing the
# sentiment, professor name, sentence, and date
@app.route('/analyze_sentiment_from_db', methods=['POST'])
def analyze_sentiment_from_db():
    # Connect to the database
    if request.is_json:
        host = request.json['host']  # Required
        user = request.json['user']  # Required
        password = request.json['password']  # Required
        database = request.json['database']  # Required
        table = request.json['table']  # Required
        input_source = request.json['input_source']  # Required
        evaluatee = request.json['evaluatee']  # Required
        evaluatee_dept = request.json['evaluatee_dept']  # Required
        course_code = request.json['course_code']  # Required
        input_data_id = request.json['input_data_id']  # Required

        # Required
        school_year_and_semester = request.json['school_year_and_semester']

        # Type confirm to confirm the prediction and save it to the database
        type_confirm = request.json['type_confirm']

        if type_confirm == input_source:
            try:
                conn = mysql.connector.connect(
                    host=host, user=user, password=password, database=database)
                cursor = conn.cursor()
                cursor.execute("SELECT {} FROM {}".format(input_source, table))
                data = cursor.fetchall()

                cursor.execute("SELECT {}, {}, {}, {} "
                               "FROM {}".
                               format(evaluatee, evaluatee_dept, course_code, input_data_id, table))
                info = cursor.fetchall()

                infor_evaluatee = [x[0] for x in info]
                infor_evaluatee_dept = [x[1] for x in info]
                infor_course_code = [x[2] for x in info]
                infor_input_data_id = [x[3] for x in info]
                data = [x[0] for x in data]

                # @desc: if the data is NoneType, then it will be replaced with an empty string to avoid errors
                # when lower casing the data
                for i in range(len(data)):
                    if data[i] is None:
                        data[i] = ''
                    else:
                        data[i] = data[i].lower()

                # @desc: Tokenize the data
                data = tokenizer.texts_to_sequences(data)
                # @desc: Convert the text to sequences
                data = pad_sequences(data, padding='post', maxlen=300)

                # @desc: Predict the sentiment of the data
                # @desc: Convert the sentiment to a string
                # @desc: Save the sentiment to the database
                predictions = model.predict(data)
                predictions = predictions.tolist()
                # Limit the number of decimal places to 4
                predictions = [round(x[0], 2) * 100 for x in predictions]
                now = datetime.now()
                analyzed = now.strftime("%A %d %B, %Y at %I:%M:%S %p")

                # Add the sentiment to the database with the following columns (evaluatee, evaluatee_dept, course_code,
                # input_data_id, sentiment, analyzed) and the sentiment will be saved to the database
                for i in range(len(predictions)):
                    matrix_cursor.execute(
                        "INSERT INTO 21_predicted_data "
                        "(`input_source`, `evaluatee`, `evaluatee_dept`, `course_code`, `input_data_id`, "
                        "`input_data`, `input_sentiment`, `is_predicted`, `date_analyzed`, "
                        "`school_year_and_semester`) "
                        "VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                            input_source, infor_evaluatee[i], infor_evaluatee_dept[i], infor_course_code[i],
                            infor_input_data_id[i], data[i], predictions[i],
                            '1', analyzed, school_year_and_semester))

                connect_to_matrix.commit()
                return jsonify(
                    {'status': 'success', 'message': 'Input data analyzed and saved',
                     'column_selected': input_source, })
            except mysql.connector.Error as err:
                return jsonify({'status': 'error', 'message': 'Connection failed: {}'.format(err)})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid request'})
