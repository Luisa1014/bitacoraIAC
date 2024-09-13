from flask import Flask, request, jsonify, render_template, send_file
import azure.cognitiveservices.speech as speechsdk
from azure.storage.blob import BlobServiceClient, ContentSettings
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)

def get_speech_config():
    speech_key = '999fcb4d3f34436ab454ec47920febe0'
    service_region = 'centralus'
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "es-CO"
    speech_config.speech_synthesis_language = "es-CO"
    speech_config.speech_synthesis_voice_name = "es-CO-GonzaloNeural"
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "8000")
    return speech_config


def synthesize_speech(text):
    speech_config = get_speech_config()
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return True
    else:
        return False

# Función para hacer preguntas y recibir respuestas
def ask_question(question):
    speech_config = get_speech_config()
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    # Crear sintetizador para la pregunta
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    synthesizer.speak_text_async(question).get()

    # Crear reconocedor para la respuesta
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return None
    
def get_blob_service_client():
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=registrobitacora;AccountKey=y1ypSZq0b/bhuADyaLzu7SWLPWhIYVgM3TGa1Ux4q/66eAU7XdPm2xBaiUGM96rIce76+nenCFWs+AStSDfYmA==;EndpointSuffix=core.windows.net'
    return BlobServiceClient.from_connection_string(connect_str)

def save_to_blob(responses, image_data=None):
    container_name = 'registros'
    responses_text = ', '.join([f"{key}: {value}" for key, value in responses.items()])
    text_blob_name = "registro.txt"
    
    try:
        container_client = blob_service_client.get_container_client(container_name)
        text_blob_client = container_client.get_blob_client(text_blob_name)
        text_blob_client.upload_blob(responses_text, overwrite=True, content_settings=ContentSettings(content_type='text/plain'))
        
        if image_data:
            image_blob_name = "registro_imagen.png"
            image = Image.open(BytesIO(base64.b64decode(image_data.split(',')[1])))
            image.save(f'temp/{image_blob_name}')
            with open(f'temp/{image_blob_name}', 'rb') as image_file:
                image_blob_client = container_client.get_blob_client(image_blob_name)
                image_blob_client.upload_blob(image_file, overwrite=True, content_settings=ContentSettings(content_type='image/png'))
                
        return jsonify({'message': 'Datos guardados correctamente.'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('PrincipalScreen.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # Sintetizar el texto a voz
    success = synthesize_speech(question)
    if success:
        return jsonify({'response': ''}), 200
    else:
        return jsonify({'error': 'Error al sintetizar la pregunta.'}), 500

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    data = request.json
    image_data = data.get('image')
    if image_data:
        return save_to_blob({}, image_data)
    return jsonify({'error': 'No se recibió imagen.'}), 400

@app.route('/save-record', methods=['POST'])
def save_record():
    data = request.json
    responses = data.get('responses', {})
    image_data = data.get('image')
    return save_to_blob(responses, image_data)


if __name__ == '__main__':
    blob_service_client = get_blob_service_client()
    app.run(debug=True)
