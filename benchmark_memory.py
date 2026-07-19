"""Módulo para la captura segura y filtrada de métricas en xv6.

Este módulo automatiza la ejecución de QEMU usando un tiempo de espera fijo,
recuperando de forma robusta todo el texto de la consola al finalizar.
"""

import subprocess
import time


class XV6SafeBenchmarker:
    """Administra la simulación de xv6 garantizando la captura completa del output."""

    def __init__(self, output_filename: str = "metrics_log.txt") -> None:
        """Inicializa el evaluador con el archivo de salida objetivo.

        Args:
            output_filename (str): Nombre del archivo para guardar las métricas.
        """
        self._output_filename: str = output_filename

    def run_benchmark(self, timeout_seconds: int = 110) -> None:
        """Lanza xv6, inyecta cowtest y recupera el output tras el tiempo asignado.

        Args:
            timeout_seconds (int): Tiempo de espera (110s para Original, ~30s para COW).
        """
        print(f"[INFO] Iniciando simulación segura. Destino: {self._output_filename}")
        print(f"[INFO] Esperando {timeout_seconds} segundos a que finalicen las pruebas...")

        # Lanza QEMU
        process = subprocess.Popen(
            ["make", "qemu"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        try:
            # 1. Espera 6 segundos para garantizar que esté listo
            time.sleep(6)

            # 2. Introduce el comando de forma directa
            if process.stdin:
                process.stdin.write("cowtest\n")
                process.stdin.flush()

            # 3. .communicate() mantiene el proceso vivo el tiempo asignado y recupera TODO el texto
            stdout_data, _ = process.communicate(timeout=timeout_seconds)

        except subprocess.TimeoutExpired:
            # Si se cumple el tiempo, fuerza el cierre limpio de QEMU y rescata lo que alcanzó a generar
            process.terminate()
            stdout_data, _ = process.communicate()

        # 4. FILTRADO: Procesa el bloque completo de texto recuperado
        filtered_lines = []
        is_test_output = False

        for line in stdout_data.splitlines():
            if "=== cowtest" in line:
                is_test_output = True

            if is_test_output:
                filtered_lines.append(line)

        # 5. Guarda exclusivamente los printf del test en el archivo .txt
        with open(self._output_filename, "w", encoding="utf-8") as output_file:
            for line in filtered_lines:
                output_file.write(line + "\n")

        print(f"[SUCCESS] Métricas guardadas correctamente en: {self._output_filename}\n")


if __name__ == "__main__":
    benchmarker = XV6SafeBenchmarker(output_filename="metrics_cow.txt")
    benchmarker.run_benchmark(timeout_seconds=110)  # Tiempo de espera para almacenar todas las métricas desde QEMU
