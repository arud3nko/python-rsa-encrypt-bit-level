import asyncio
import os
import uuid

from flask import Flask, render_template, request, session, make_response, send_file
from flask_session import Session

from app import rsa2

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

def generate_keypair():
    public_key, private_key = asyncio.run(rsa2.generate_rsa_keypair())
    return public_key, private_key

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        public_key, private_key = generate_keypair()
        session['public_key'] = public_key
        session['private_key'] = private_key

        file = request.files['open_text']

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        filetype = file_path[file_path.rfind('.'):]
        filename = str(uuid.uuid4()) + filetype
        output = os.path.join(app.config['RESULTS_FOLDER'], filename)

        encoded_file = asyncio.run(rsa2.encode_file(file_path=file_path,
                                                    public=public_key,
                                                    output=output))

        response = make_response(render_template('result.html',
                               public_key=public_key,
                               secret_key=private_key,
                               filename=filename,
                               download=filename))

        response.set_cookie('public_key', str(public_key))

        return response


    return render_template('index.html')


@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    response = send_file(os.path.join(app.config['RESULTS_FOLDER'], filename), as_attachment=True)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response



@app.route('/decode', methods=['GET', 'POST'])
def decoder():
    public_key, private_key = session.get('public_key', None), session.get('private_key', None)
    if request.method == 'POST':
        secret = request.form["secret"]

        file = request.files['encoded_text']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        filetype = file_path[file_path.rfind('.'):]
        filename = str(uuid.uuid4()) + filetype
        output = os.path.join(app.config['RESULTS_FOLDER'], filename)

        decoded_file = asyncio.run(rsa2.decode_file(file_path=file_path,
                                                    secret=eval(secret),
                                                    output=output))

        response = make_response(render_template('result.html',
                               public_key=public_key,
                               secret_key=private_key,
                               filename=filename,
                               download=filename))

        return response

    return render_template('decode.html')

if __name__ == '__main__':
    app.run(debug=True)
