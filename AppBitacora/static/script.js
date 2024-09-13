document.addEventListener("DOMContentLoaded", function() {
    const questionElement = document.getElementById("question");
    const responsesElement = document.getElementById("responses");

    // Función para actualizar la pregunta en la interfaz y hablarla
    function updateQuestion(question) {
        questionElement.innerText = question;
        const utterance = new SpeechSynthesisUtterance(question);
        utterance.lang = 'es-CO';
        window.speechSynthesis.speak(utterance);
    }

    // Función para actualizar las respuestas en la interfaz
    function updateResponses(response) {
        responsesElement.innerHTML += response + "<br>";
    }

    // Función para manejar el reconocimiento de voz
    function startSpeechRecognition() {
        return new Promise((resolve, reject) => {
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'es-CO';
            recognition.interimResults = false;
            recognition.onresult = (event) => {
                const response = event.results[0][0].transcript;
                resolve(response);
            };
            recognition.onerror = (event) => {
                reject(event.error);
            };
            recognition.start();
        });
    }

    // Función para manejar la secuencia de preguntas y respuestas
    async function handleQuestion() {
        const questions = [
            "¿Cuál es la Compañía?",
            "¿Cuál es la Especialidad?",
            "¿Qué actividades se realizaron?",
            "¿Quién es la Persona Encargada?",
            "¿Cuál es la Fecha de Entrega de la Actividad?",
            "¿Cuál es el Estado de la Actividad?"
        ];
        
        for (const question of questions) {
            updateQuestion(question);
            try {
                const response = await startSpeechRecognition();
                updateResponses(response);
            } catch (error) {
                console.error('Error en el reconocimiento de voz:', error);
                updateResponses('No se pudo reconocer la respuesta.');
            }
            // Esperar antes de la siguiente pregunta
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }

    // Iniciar la secuencia de preguntas
    handleQuestion();
});

document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startCameraButton = document.getElementById('start-camera');
    const takePhotoButton = document.getElementById('take-photo');
    const saveRecordButton = document.getElementById('save-record');

    let streaming = false;

    function startCamera() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                video.play();
                streaming = true;
            })
            .catch(err => {
                console.error('Error al acceder a la cámara: ', err);
            });
    }

    function takePhoto() {
        if (streaming) {
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataURL = canvas.toDataURL('image/png');

            fetch('/upload-photo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: dataURL })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Imagen guardada:', data);
            })
            .catch(error => console.error('Error al guardar la imagen:', error));
        } else {
            console.log('No se está transmitiendo video.');
        }
    }

    function saveRecord() {
        const data = {
            responses: document.getElementById('responses').innerText.split('\n') // Convertir respuestas en una lista
        };

        fetch('/save-record', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Registro guardado:', data);
        })
        .catch(error => console.error('Error al guardar el registro:', error));
    }

    startCameraButton.addEventListener('click', startCamera);
    takePhotoButton.addEventListener('click', takePhoto);
    saveRecordButton.addEventListener('click', saveRecord);
});