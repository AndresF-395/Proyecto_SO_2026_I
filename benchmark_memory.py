"""Módulo automatizado y dinámico para el análisis de rendimiento en xv6.

Este módulo ejecuta QEMU, detecta dinámicamente la finalización de 'cowtest'
sin usar tiempos de espera fijos, y filtra el archivo de salida para conservar
únicamente los resultados impresos por el programa de pruebas.
"""

import subprocess
import time


class XV6DynamicBenchmarker:
    """Administra la simulación interactiva de xv6 con filtrado de datos en tiempo real."""

    def __init__(self, output_filename: str = "metrics_log.txt") -> None:
        """Inicializa el evaluador dinámico configurando el archivo de salida.

        Args:
            output_filename (str): Nombre del archivo donde se guardarán las métricas filtradas.
        """
        self._output_filename: str = output_filename

    def run_benchmark(self) -> None:
        """Lanza xv6, ejecuta cowtest y procesa el flujo de salida dinámicamente."""
        print(f"[INFO] Iniciando entorno dinámico. Destino: {self._output_filename}")

        # Para comenzar la ejecución dentro de la máquina virtual
        with open(self._output_filename, "w", encoding="utf-8") as output_file:
            process = subprocess.Popen(
                ["make", "qemu"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Bandera lógica para saber cuándo empezar a escribir en el archivo .txt
            is_test_output: bool = False

            # Bandera para controlar si ya se envió el comando de ejecución
            command_sent: bool = False

            # Lee la salida de la consola línea por línea en tiempo real
            while True:
                # El método readline se bloquea automáticamente esperando salida de QEMU
                line = process.stdout.readline()
                if not line:
                    break

                # Detecta si xv6 llegó al shell listo para recibir comandos
                if "$" in line and not command_sent:
                    # Espera un instante corto de estabilización e introduce el comando
                    time.sleep(1)
                    if process.stdin:
                        process.stdin.write("cowtest\n")
                        process.stdin.flush()
                        command_sent = True
                    continue

                # FILTRADO: Activa la escritura cuando inicie formalmente el binario cowtest
                if "== test 1" in line:
                    is_test_output = True

                # Si la línea pertenece a cowtest, se preserva en el archivo de texto
                if is_test_output:
                    output_file.write(line)
                    output_file.flush()

                # DETENCIÓN DINÁMICA: Si detecta el mensaje de finalización, cierra con éxito
                if "      sube NFORKS en el codigo" in line:
                    print("[INFO] Indicador de finalización detectado con éxito.")
                    break

                # DETENCIÓN POR FALLA: Si un test falla, captura el error y finaliza
                if "FALLO:" in line or "panic:" in line:
                    output_file.write(line)
                    print(f"  [ALERTA] Se detectó una falla en la ejecución: {line.strip()}")
                    break

            process.terminate()
            print(f"[SUCCESS] Proceso concluido. Archivo generado: {self._output_filename}\n")


if __name__ == "__main__":
    benchmarker = XV6DynamicBenchmarker(output_filename="metrics_cow.txt")
    benchmarker.run_benchmark()
