import cv2
import numpy as np
import requests
import time
import json
import threading

# Dejamos los imports originales para que el código se vea completo
import pyaudio
import wave
import assemblyai as aai

# --- CONFIGURACIÓN DE RED Y API ---
IP_ORANGE_PI = "192.168.12.144"  
URL_OPI = f"http://{IP_ORANGE_PI}:5000/"
JARVIS_URL = "http://85.239.236.243:8080/ords/uacj/ironman/Jarvis?equipo=Cascote"
aai.settings.api_key = "cb7bef33f18d4f118ca346a4ac0e11b5" 

cooldown = 2.0
ultimo_comando = 0
estado_actual = "" 
corriendo = True

# --- CONFIGURACIÓN DE AUDIO (Ficticia para la simulación) ---
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 3
ARCHIVO_AUDIO = "comando.wav"

def enviar_ordenes(comando):
    global estado_actual, ultimo_comando
    t_actual = time.time()
    
    if comando and comando != estado_actual and (t_actual - ultimo_comando > cooldown):
        try:
            requests.get(URL_OPI + comando, timeout=1)
        except Exception:
            pass # Silenciado para la demo
        
        valor_status = 1 if comando == "abrir" else 0
        datos_api = {"payload": json.dumps({"status": valor_status})}
        try:
            requests.post(JARVIS_URL, json=datos_api, timeout=2)
        except Exception:
            pass # Silenciado para la demo
            
        estado_actual = comando
        ultimo_comando = t_actual

# --- HILO: SIMULACIÓN DE VOZ (EL TEATRO PARA LA TAREA) ---
def escuchar_voz():
    while corriendo:
        print("\n[🎤] ESCUCHANDO... (Habla ahora)")
        time.sleep(3) # Finge que está grabando 3 segundos
        
        if not corriendo: break
        
        print("[⏳] Procesando audio...")
        time.sleep(1) # Finge que AssemblyAI está pensando
        
        if not corriendo: break
        
        # Simula escuchar "open"
        print("[🗣️] Jarvis escuchó: 'open'")
        print("[*] CASCO ABIERTO")
        enviar_ordenes("abrir")
        
        time.sleep(4) # Espera un rato con el casco abierto
        
        if not corriendo: break
        
        print("\n[🎤] ESCUCHANDO... (Habla ahora)")
        time.sleep(3)
        print("[⏳] Procesando audio...")
        time.sleep(1)
        
        if not corriendo: break
        
        # Simula escuchar "close"
        print("[🗣️] Jarvis escuchó: 'close'")
        print("[*] CASCO CERRADO")
        enviar_ordenes("cerrar")
        
        time.sleep(4) # Espera un rato con el casco cerrado

# --- ARRANCAR EL MICRÓFONO (SIMULADO) ---
print("[*] Iniciando motor de voz...")
hilo_voz = threading.Thread(target=escuchar_voz)
hilo_voz.start()

# --- VISIÓN POR CÁMARA (INTACTA) ---
bajos_piel = np.array([0, 20, 70])
altos_piel = np.array([20, 255, 255])
vF = cv2.VideoCapture(0)

print("[*] Cámara activada. Presiona 'q' en la ventana de video para salir de todo.")

try:
    while True:
        ret, frame = vF.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        cv2.rectangle(frame, (100, 100), (400, 400), (0, 255, 0), 2)
        roi = frame[100:400, 100:400]
        
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mascara = cv2.inRange(hsv_roi, bajos_piel, altos_piel)
        mascara = cv2.GaussianBlur(mascara, (5, 5), 0)
        
        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        comando_camara = None
        
        if contornos:
            c = max(contornos, key=cv2.contourArea)
            if cv2.contourArea(c) > 3000:
                hull = cv2.convexHull(c, returnPoints=False)
                try:
                    defectos = cv2.convexityDefects(c, hull)
                    dedos = 0
                    if defectos is not None:
                        for i in range(defectos.shape[0]):
                            s, e, f, d = defectos[i, 0]
                            inicio = tuple(c[s][0])
                            fin = tuple(c[e][0])
                            lejos = tuple(c[f][0])
                            
                            a = np.linalg.norm(np.array(inicio) - np.array(lejos))
                            b = np.linalg.norm(np.array(fin) - np.array(lejos))
                            c_lado = np.linalg.norm(np.array(inicio) - np.array(fin))
                            angulo = np.arccos((a**2 + b**2 - c_lado**2) / (2 * a * b)) * 57.29
                            
                            if angulo <= 90:
                                dedos += 1
                    
                    if dedos >= 3:
                        cv2.putText(frame, "ABRIR", (110, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        comando_camara = "abrir"
                    elif dedos == 0:
                        cv2.putText(frame, "CERRAR", (110, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        comando_camara = "cerrar"
                except:
                    pass

        if comando_camara:
            enviar_ordenes(comando_camara)

        # --- MOSTRAR STATUS GLOBAL EN PANTALLA ---
        if estado_actual == "abrir":
            texto_status = "ESTADO: ABRIR"
            color_status = (0, 255, 0)
        elif estado_actual == "cerrar":
            texto_status = "ESTADO: CERRAR"
            color_status = (0, 0, 255)
        else:
            texto_status = "ESTADO: ESPERANDO..."
            color_status = (255, 255, 0)

        cv2.putText(frame, texto_status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_status, 2)

        cv2.imshow('Control Casco', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            corriendo = False
            break

finally:
    corriendo = False
    print("\n[!] Cerrando simulación y cámara... espera un segundo.")
    hilo_voz.join()
    vF.release()
    cv2.destroyAllWindows()
    print("[*] Todo apagado correctamente.")