import pyaudio
import wave
import assemblyai as aai
import requests
import json

# --- Configuración ---
aai.settings.api_key = "cb7bef33f18d4f118ca346a4ac0e11b5" 
NOMBRE_EQUIPO = "Tony_stark" 
URL_JARVIS = f"http://85.239.236.243:8080/ords/uacj/ironman/Jarvis?equipo={NOMBRE_EQUIPO}"
ARCHIVO_AUDIO = "comando.wav"

# --- Configuración del Micrófono ---
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 3 # Segundos de grabación

def grabar_audio():
    p = pyaudio.PyAudio()
    print("\n GRABANDO... DI TU COMANDO AHORA (tienes 3 segundos)")
    
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []
    
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        
    print("Grabación terminada.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Guarda el audio
    with wave.open(ARCHIVO_AUDIO, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def enviar_comando_jarvis(status):
    # Envolvemos el status dentro de "payload" convertido a texto
    datos_api = {"payload": json.dumps({"status": status})}
    respuesta = requests.post(URL_JARVIS, json=datos_api)
    print(f"Jarvis notificado. Código HTTP: {respuesta.status_code}")

if __name__ == "__main__":
    # 1. Grabar voz
    grabar_audio()
    
    # 2. Transcribir (Corrección aplicada aquí)
    config = aai.TranscriptionConfig(
        speech_models=["universal-3-pro", "universal-2"], 
        language_code="es"
    )
    transcriber = aai.Transcriber(config=config)

    print("Enviando audio a AssemblyAI...")
    transcript = transcriber.transcribe(ARCHIVO_AUDIO)

    if transcript.status == aai.TranscriptStatus.error:
        print(f"Error en transcripción: {transcript.error}")
    else:
        texto = transcript.text.lower()
        print(f"Texto detectado: '{texto}'")
        
        # 3. Enviar comando
        if "abrir casco" in texto:
            print("Ejecutando: Abrir casco")
            enviar_comando_jarvis(1) 
        elif "cerrar casco" in texto:
            print("Ejecutando: Cerrar casco")
            enviar_comando_jarvis(0) 
        else:
            print("Comando no reconocido. Vuelve a correr el script.")