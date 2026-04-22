import time

import RPi.GPIO as GPIO


# BCM pin definitions
LED_PIN = 23
BUZZER_PIN = 18
LED_TOGGLE_INTERVAL = 0.5
BUZZER_TOGGLE_INTERVAL = 1.0


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)

    print("Starting adv2-1. Press CTRL+C to exit")

    led_state = GPIO.LOW
    buzzer_state = GPIO.LOW
    last_led_toggle = time.time()
    last_buzzer_toggle = time.time()

    try:
        while True:
            now = time.time()

            if now - last_led_toggle >= LED_TOGGLE_INTERVAL:
                led_state = GPIO.HIGH if led_state == GPIO.LOW else GPIO.LOW
                GPIO.output(LED_PIN, led_state)
                print("LED: {}".format("ON" if led_state == GPIO.HIGH else "OFF"))
                last_led_toggle = now

            if now - last_buzzer_toggle >= BUZZER_TOGGLE_INTERVAL:
                buzzer_state = GPIO.HIGH if buzzer_state == GPIO.LOW else GPIO.LOW
                GPIO.output(BUZZER_PIN, buzzer_state)
                print("BUZZER: {}".format("ON" if buzzer_state == GPIO.HIGH else "OFF"))
                last_buzzer_toggle = now

            time.sleep(0.01)
    finally:
        GPIO.output(LED_PIN, GPIO.LOW)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        GPIO.cleanup()


if __name__ == "__main__":
    main()
