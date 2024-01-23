from flask import Flask, request, jsonify
import cv2
import numpy as np
import requests
import io
import json
import os
from deep_translator import GoogleTranslator


app = Flask(__name__)

def extract_text_from_file(image_file):
    img_array = np.frombuffer(image_file.read(), dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    url_api = "https://api.ocr.space/parse/image"
    _, compressed_image = cv2.imencode(".jpg", img, [1, 90])
    file_bytes = io.BytesIO(compressed_image)

    result = requests.post(url_api,
                           files={"image.jpg": file_bytes},
                           data={"apikey": "K83400102388957",
                                 "language": "eng"})

    result = result.content.decode()
    result = json.loads(result)

    parsed_results = result.get("ParsedResults", [])
    
    if parsed_results:
        text_detected = parsed_results[0].get("ParsedText", "")
        return text_detected
    else:
        return "No text detected"

def translate_text(input_text, target_language='hi'):
    def translate_chunk(chunk):
        translate = GoogleTranslator(source='auto', target=target_language).translate
        translated_text = ''
        source_text_chunk = ''
        for sentence in chunk.split('. '):
            if len(sentence.encode('utf-8')) + len(source_text_chunk.encode('utf-8')) < 5000:
                source_text_chunk += '. ' + sentence
            else:
                translated_text += ' ' + translate(source_text_chunk)
                if len(sentence.encode('utf-8')) < 5000:
                    source_text_chunk = sentence
                else:
                    message = '<<Omitted Word longer than 5000 bytes>>'
                    translated_text += ' ' + translate(message)
                    source_text_chunk = ''
        if translate(source_text_chunk) is not None:
            translated_text += ' ' + translate(source_text_chunk)
        return translated_text

    try:
        translated_text = translate_chunk(input_text)
        return translated_text
    except Exception as e:
        return str(e)

@app.route('/extract_and_translate', methods=['POST'])
def extract_and_translate():
    image_file = request.files.get('image')
    target_language = request.form.get("lang")

    if image_file:
        text_detected = extract_text_from_file(image_file)
        translated_text = translate_text(text_detected, target_language)

        return jsonify({"text_detected": text_detected, "translated_text": translated_text})
    else:
        return jsonify({"error": "Image file not provided in request"}), 400

@app.route('/extract_text', methods=['POST'])
def extract_text():
    image_file = request.files.get('image')
    target_language = request.form.get("lang")

    if image_file:
        text_detected = extract_text_from_file(image_file)
        return jsonify({"text_detected": text_detected})
    else:
        return jsonify({"error": "Image file not provided in request"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
