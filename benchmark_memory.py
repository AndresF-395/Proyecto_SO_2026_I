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

        # Apertura del descriptor de archivo para almacenar las métricas filtradas
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

                # FILTRADO: Se activa con la primera impresión del main en C sin importar espacios
                if "=== cowtest" in line:
                    is_test_output = True

                # Si la línea pertenece a cowtest, se preserva de manera íntegra
                if is_test_output:
                    output_file.write(line)
                    output_file.flush()
                    print(f"  [CAPTURADO] {line.strip()}")

                # DETENCIÓN DINÁMICA: Busca una subcadena única y segura sin espacios al inicio
                if "todas las pruebas de correctitud pasaron" in line:
                    # Captura las últimas tres líneas de notas informativas antes de salir
                    try:
                        note_line_1 = process.stdout.readline()
                        note_line_2 = process.stdout.readline()
                        note_line_3 = process.stdout.readline()
                        output_file.write(note_line_1)
                        output_file.write(note_line_2)
                        output_file.write(note_line_3)
                        print(f"  [CAPTURADO] {note_line_1.strip()}")
                        print(f"  [CAPTURADO] {note_line_2.strip()}")
                        print(f"  [CAPTURADO] {note_line_3.strip()}")
                    except Exception:
                        pass  # Previene cierres abruptos

                    print("[INFO] Indicador de finalización detectado con éxito.")
                    break

                # DETENCIÓN POR FALLA: Si un test falla, captura el error y finaliza
                if "FALLO:" in line or "panic:" in line:
                    output_file.write(line)
                    print(f"  [ALERTA] Se detectó una falla en la ejecución: {line.strip()}")
                    break

            # Fuerza la finalización de QEMU una vez cumplida la condición de parada
            process.terminate()
            print(f"[SUCCESS] Proceso concluido. Archivo generado: {self._output_filename}\n")


if __name__ == "__main__":
    benchmarker = XV6DynamicBenchmarker(output_filename="metrics_original.txt")
    benchmarker.run_benchmark()
