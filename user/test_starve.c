#include "kernel/types.h"
#include "user.h"

int
main(void)
{
  int pid1, pid2;
  int start;//, end1, end2;

  start = uptime();

  pid1 = fork();
  if (pid1 == 0) {
    // Hijo 1: trabajo pesado (CPU-bound)
    for (volatile long i = 0; i < 2000000000L; i++) {}
    printf("Hijo 1 (pid %d) termino en tick %d\n", getpid(), uptime());
    exit(0);
  }

  pid2 = fork();
  if (pid2 == 0) {
    // Hijo 2: trabajo pesado (CPU-bound)
    for (volatile long i = 0; i < 2000000000L; i++) {}
    printf("Hijo 2 (pid %d) termino en tick %d\n", getpid(), uptime());
    exit(0);
  }

  
  wait(0);
  wait(0);

  printf("Padre: ambos hijos terminaron. Inicio en tick %d\n", start);
  exit(0);
}