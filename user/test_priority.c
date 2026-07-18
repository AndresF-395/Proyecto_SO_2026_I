#include "kernel/types.h"
#include "user.h"

int
main(void)
{
  int pid;

  pid = fork();
  if (pid == 0) {
    setpriority(1);   // Prioridad alta (numero bajo = mayor prioridad)
    for (volatile long i = 0; i < 2000000000L; i++) {}
    printf("Proceso ALTA prioridad (pid %d) termino en tick %d\n", getpid(), uptime());
    exit(0);
  }

  pid = fork();
  if (pid == 0) {
    setpriority(19);  // Prioridad baja
    for (volatile long i = 0; i < 2000000000L; i++) {}
    printf("Proceso BAJA prioridad (pid %d) termino en tick %d\n", getpid(), uptime());
    exit(0);
  }

  wait(0);
  wait(0);
  exit(0);
}