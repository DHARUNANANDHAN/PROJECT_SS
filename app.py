from flask import Flask, request, jsonify, send_from_directory, render_template_string
import speech_recognition as sr
import os

app = Flask(__name__)

# Configuration
ISL_GIFS_DIR = 'ISL_Gifs'
LETTERS_DIR = 'letters'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}

# Define keywords and their corresponding GIF filenames
KEYWORDS_TO_GIFS = {
    'god question': 'god_question.gif',
    'take care': 'take_care.gif',
    'good afternoon': 'good_afternoon.gif',
    'good morning': 'good_morning.gif',
    'hello': 'hello.gif',
    'i am fine': 'i_am_fine.gif',
    'i am sorry': 'i_am_sorry.gif',
    'i am tired': 'i_am_tired.gif',
    'lets go for lunch': 'lets_go_for_lunch.gif',
    'nice to meet you': 'nice_to_meet_you.gif',
    'shall I help you': 'shall_i_help_you.gif',
    'sign language interpreter': 'sign_language_interpreter.gif',
    'sit down': 'sit_down.gif',
    'stand up': 'stand_up.gif',
    'what is todays date': 'what_is_todays_date.gif',
    'what is your father do': 'what_is_your_father_do.gif',
    'what is your name': 'what_is_your_name.gif',
    'what are you doing': 'what_are_you_doing.gif'
}

recognizer = sr.Recognizer()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def recognize_audio(file):
    audio_data = sr.AudioData(file.read(), 44100, 2)
    try:
        text = recognizer.recognize_google(audio_data).lower()
        return text
    except sr.UnknownValueError:
        return "Sorry, I did not understand that."
    except sr.RequestError as e:
        return f"Could not request results; {e}"

@app.route('/process-audio', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        recognized_text = recognize_audio(file)
        # Check if recognized text is a keyword for a GIF
        gif_filename = KEYWORDS_TO_GIFS.get(recognized_text, None)
        if gif_filename:
            gif_url = f"/gif/{gif_filename}"
            return jsonify({"recognized_text": recognized_text, "gif_url": gif_url})
        
        # Otherwise, check if recognized text is a single letter for a letter GIF
        elif len(recognized_text) == 1 and recognized_text.isalpha():
            letter_gif_filename = f"{recognized_text}.gif"
            letter_gif_url = f"/gif/{letter_gif_filename}"
            return jsonify({"recognized_text": recognized_text, "gif_url": letter_gif_url})
        
        else:
            return jsonify({"recognized_text": recognized_text, "gif_url": None})
    else:
        return jsonify({"error": "Invalid file type"}), 400

@app.route('/image/<filename>')
def serve_image(filename):
    if allowed_file(filename):
        return send_from_directory(LETTERS_DIR, filename)
    else:
        return "File type not allowed.", 400

@app.route('/gif/<filename>')
def serve_gif(filename):
    if filename.endswith('.gif'):
        return send_from_directory(ISL_GIFS_DIR, filename)
    else:
        return "File type not allowed.", 400

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audio Recording</title>
    </head>
    <body>
        <h1>Audio Processing Application</h1>
        <p>Record audio and upload it:</p>
        <form id="uploadForm" action="/process-audio" method="post" enctype="multipart/form-data">
            <input type="file" id="audioFile" name="file" accept="audio/*" />
            <input type="submit" value="Upload">
        </form>

        <h2>Record Audio</h2>
        <button id="startRecord">Start Recording</button>
        <button id="stopRecord" disabled>Stop Recording</button>
        <audio id="audioPlayback" controls></audio>

        <div id="result">
            <p id="recognizedText"></p>
            <img id="gifOutput" src="" style="display:none;" />
        </div>

        <script>
            let mediaRecorder;
            let audioChunks = [];
            const startButton = document.getElementById('startRecord');
            const stopButton = document.getElementById('stopRecord');
            const audioPlayback = document.getElementById('audioPlayback');
            const recognizedTextElem = document.getElementById('recognizedText');
            const gifOutputElem = document.getElementById('gifOutput');

            startButton.addEventListener('click', async () => {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                startButton.disabled = true;
                stopButton.disabled = false;

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    audioPlayback.src = audioUrl;

                    // Create a file object and upload
                    const file = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
                    const formData = new FormData();
                    formData.append('file', file);

                    fetch('/process-audio', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        recognizedTextElem.textContent = 'Recognized text: ' + data.recognized_text;
                        if (data.gif_url) {
                            gifOutputElem.src = data.gif_url;
                            gifOutputElem.style.display = 'block';
                        } else {
                            gifOutputElem.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
                });
            });

            stopButton.addEventListener('click', () => {
                mediaRecorder.stop();
                startButton.disabled = false;
                stopButton.disabled = true;
            });
        </script>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
