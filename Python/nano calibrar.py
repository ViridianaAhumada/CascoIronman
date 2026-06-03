import OPi.GPIO as GPIO
import time

# --- CONFIGURACIÓN ORANGE PI ZERO 2W ---
GPIO.setboard(GPIO.ZERO2W)
GPIO.setmode(GPIO.BOARD)

PIN_SERVO_DERECHO = 12   # Brazo gris
PIN_SERVO_IZQUIERDO = 11 # Brazo rojo

GPIO.setup(PIN_SERVO_DERECHO, GPIO.OUT)
GPIO.setup(PIN_SERVO_IZQUIERDO, GPIO.OUT)

# Frecuencia de 50Hz para servos estándar
pwm_der = GPIO.PWM(PIN_SERVO_DERECHO, 50) 
pwm_izq = GPIO.PWM(PIN_SERVO_IZQUIERDO, 50)

pwm_der.start(0)
pwm_izq.start(0)

print("--- CALIBRACIÓN DE SERVOS ---")
print("Ingrese un ángulo entre 0 y 180 para probar.")
print("Presione Ctrl+C para salir.")

try:
    while True:
        entrada = input("\nIngrese ángulo (0-180) o 'q' para salir: ")
        
        if entrada.lower() == 'q':
            break
            
        try:
            angulo = float(entrada)
            if 0 <= angulo <= 180:
                # Cálculo de Duty Cycle (2% a 12%)
                duty = 2 + (angulo / 18)
                
                print(f"[*] Moviendo a {angulo}° (Duty Cycle: {duty:.2f}%)")
                pwm_der.ChangeDutyCycle(duty)
                pwm_izq.ChangeDutyCycle(duty)
                
                time.sleep(1) 
                
                # Enviar a 0 para quitar tensión y evitar sobrecalentamiento
                pwm_der.ChangeDutyCycle(0)
                pwm_izq.ChangeDutyCycle(0)
            else:
                print("[!] Error: El ángulo debe estar entre 0 y 180.")
        except ValueError:
            print("[!] Error: Ingrese únicamente valores numéricos.")

except KeyboardInterrupt:
    pass
finally:
    print("\n[*] Apagando servos y limpiando pines...")
    pwm_der.stop()
    pwm_izq.stop()
    GPIO.cleanup()