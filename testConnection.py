from xarm.wrapper import XArmAPI

def main():
    # 1) Dirección IP del controlador xArm
    ip_robot = '192.168.1.250'

    # 2) Instanciar API y conectar
    arm = XArmAPI(ip_robot)
    # Espera a que el robot responda
    arm.wait_ready(timeout=5.0)

    # 3) Imprimir estado para verificar
    print("State:", arm.state, "| Mode:", arm.mode, "| Error Code:", arm.error_code)

    # 4) Ejemplo: llevar el robot a posición home
    arm.motion_enable(enable=True)
    arm.set_mode(0)       # 0: modo posición
    arm.set_state(0)      # 0: estado inactivo → permite comandos
    arm.clean_error()
    arm.set_servo_angle_j([0,0,0,0,0,0], speed=30, mvacc=1000, wait=True)
    print("¡Movimiento a home completado!")

    arm.disconnect()

if __name__ == "__main__":
    main()
