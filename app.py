from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS
from pineconeUtils import ask_question
from flask_socketio import SocketIO
from flask_socketio import send, emit
from uploadtopinecone import getProcessingDocs, upload_documents

load_dotenv()

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


socketio = SocketIO(app, cors_allowed_origins='*')


@socketio.on('rachel')
def handle_message(data):
    try:
        if 'question' not in data or 'caseId' not in data or 'docs' not in data:
            print("not in data")
            emit('rachel', {
                'error': 'Please provide the caseId, question, and the docs'}, broadcast=True)
            return
        question = data['question']
        case_id = data['caseId']
        docs = data['docs']
        case_info = data['caseInfo']

        print("here are docs")

        print(docs)

        answer_generator = ask_question(docs, question, case_id, case_info)

        answer_generating = True
        answer_string = ''
        while answer_generating:
            try:
                next_answer = next(answer_generator)
                answer_string += str(next_answer)
                emit('rachel', {"answer": answer_string,
                     "done": False}, broadcast=True)
            except Exception as e:
                print(e)
                answer_generating = False
                emit('rachel', {"answer": answer_string,
                     "done": True}, broadcast=True)

                print('')

    except Exception as e:
        emit('rachel', {'error': str(e)}, broadcast=True)
        return


@app.route('/updateFiles', methods=['POST'])
def handleUpdate():
    try:
        s3_urls, ids, file_names = getProcessingDocs()
        response = upload_documents(s3_urls, ids, file_names)
        print(response)
        return jsonify({"status": "success", "data": response}), 200
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/')
def welcome():
    return 'Welcome to Avalon'


if __name__ == '__main__':
    app.run(port=33507, debug=True)
    socketio.run(app)
