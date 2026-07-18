"""Módulo para la evaluación del rendimiento y captura de métricas de memoria en xv6.

Este módulo automatiza la ejecución de QEMU directamente en la raíz del repositorio,
inyecta de forma transparente el programa cowtest y registra las métricas en un archivo.
"""

import subprocess
import time

class XV6Benchmarker:
    """Administra la ejecución y el registro de métricas para las simulaciones de xv6."""

    def __init__(self, output_filename: str = "metrics_log.txt") -> None:
        """Inicializa el evaluador de rendimiento con un archivo de salida objetivo.

        Args:
            output_filename (str): El nombre del archivo de texto donde se guardarán las métricas.
        """
        self._output_filename: str = output_filename

    def run_benchmark(self, timeout_seconds: int = 25) -> None:
        """Lanza xv6 a través de QEMU, ejecuta cowtest y redirecciona el flujo a un archivo.

        Args:
            timeout_seconds (int): Tiempo máximo en segundos a esperar para completar los tests.
        """
        print(f"[INFO] Iniciando el banco de pruebas de xv6. Guardando en {self._output_filename}...")

        # Para abrir el archivo en la máquina virtual
        with open(self._output_filename, "w", encoding="utf-8") as output_file:
            process = subprocess.Popen(
                ["make", "qemu"],
                stdin=subprocess.PIPE,
                stdout=output_file,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Espera de 5 segundos a que xv6 complete su secuencia de arranque ($)
            time.sleep(5)

            if process.stdin:
                # Automatiza la digitación del comando 'cowtest' y "presiona" Enter dentro de xv6
                process.stdin.write("cowtest\n")
                process.stdin.flush()

            # Otorga el tiempo parametrizado para que se completen los forks del test 4
            time.sleep(timeout_seconds)

            # Finaliza el proceso de QEMU
            process.terminate()
            print(f"[SUCCESS] Métricas almacenadas correctamente en: {self._output_filename}\n")

if __name__ == "__main__":
    benchmarker = XV6Benchmarker(output_filename="metrics_cow.txt")
    benchmarker.run_benchmark(timeout_seconds=25)
