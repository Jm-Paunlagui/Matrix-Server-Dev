
from config.app import app
import mysql.connector
from flask import jsonify, request
import pickle

from keras.models import load_model

try:
    # @desc MySQL function to get connected and execute queries
    connect_to_matrix = mysql.connector.connect(host="localhost", user="root", password="", database="production_saer")
    matrix_cursor = connect_to_matrix.cursor()
    jsonify({'status': 'success', 'message': 'Connected to the database'})
except Exception as e:
    jsonify({'status': 'error', 'message': 'Failed to connect to the database' + str(e)})

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
@app.route('/get_data_from_database', methods=['POST'])
def get_data_from_database():
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

        school_year_and_semester = request.json['school_year_and_semester']  # Required

        # Type confirm to confirm the prediction and save it to the database
        type_confirm = request.json['type_confirm']

        matrix_cursor.execute("SELECT `input_source`, `input_data_id` FROM `21_predicted_data`")
        matrix_data = matrix_cursor.fetchall()

        if matrix_data:
            for m_data in matrix_data:
                if m_data[0] == input_source and m_data[1] == input_data_id:
                    return jsonify({'status': 'error', 'message': 'This data has already been analyzed and scored by '
                                                                  'the system.'}), 406  # Not Acceptable
        else:
            jsonify({'status': 'success', 'message': 'Ready to analyze and score the data.'}), 200
            if type_confirm == input_source:
                try:
                    conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
                    cursor = conn.cursor()
                    cursor.execute("SELECT {}, {}, {}, {}, {} FROM {}".format(input_source, input_data_id, evaluatee,
                                                                              evaluatee_dept, course_code, table))
                    data = cursor.fetchall()

                    if data:
                        pass

                    else:
                        return jsonify({'status': 'error', 'message': 'No data found'}), 404

                except mysql.connector.Error as err:
                    return jsonify({'status': 'error', 'message': 'Connection failed: {}'.format(err)})
            else:
                return jsonify({'status': 'error', 'message': 'Confirmation failed'}), 406  # Not Acceptable

    else:
        return jsonify({'status': 'error', 'message': 'Invalid request'})
