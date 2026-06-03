import cv2
import numpy as np
import requests
import time
import json
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# --- 1. CONEXIÓN A COPPELIASIM (ZMQ) ---
print("Conectando a CoppeliaSim...")
try:
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    print("Conectado a la simulación con éxito.")
except Exception as e:
    print(f"Error al conectar con CoppeliaSim: {e}")

# --- 2. CONFIGURACIÓN DE LA API UACJ ---
# El equipo va directo en la URL con la mayúscula y minúscula exacta que usaste
JARVIS_URL = "http://85.239.236.243:8080/ords/uacj/ironman/Jarvis?equipo=Cascote"
cooldown = 2.0
ultimo_comando = 0
estado_actual = "" 

# --- 3. CONFIGURACIÓN VISIÓN ---
bajos_piel = np.array([0, 20, 70])
altos_piel = np.array([20, 255, 255])
vF = cv2.VideoCapture(0)

print("Cámara activada. Presiona 'q' en la ventana para salir.")

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
    
    comando = None
    
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
                    comando = "abrir"
                elif dedos == 0:
                    cv2.putText(frame, "CERRAR", (110, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    comando = "cerrar"
            except:
                pass

    # --- 4. ENVÍO DE DATOS ---
    t_actual = time.time()
    
    if comando and comando != estado_actual and (t_actual - ultimo_comando > cooldown):
        
        # A. Señal a CoppeliaSim
        try:
            sim.setStringSignal("command", comando)
            print(f"[*] CoppeliaSim: {comando}")
        except:
            print("[!] Error enviando a CoppeliaSim")
        
        # B. Enviar POST a la API de la UACJ
        # Lógica basada en tu código de voz: 1 es abrir, 0 es cerrar
        valor_status = 1 if comando == "abrir" else 0
        
        # Estructura exacta extraída de tu script funcional
        datos_api = {
            "payload": json.dumps({"status": valor_status})
        }
        
        try:
            r = requests.post(JARVIS_URL, json=datos_api, timeout=2)
            print(f"[*] API Jarvis notificada: {comando} | Status: {r.status_code}")
        except Exception as e:
            print(f"[!] Error de API: {e}")
            
        estado_actual = comando
        ultimo_comando = t_actual

    cv2.imshow('Control Jarvis', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vF.release()
cv2.destroyAllWindows()