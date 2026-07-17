// cowtest.c
//
// Programa de usuario para probar la implementación de Copy-on-Write.
// Va en el directorio user/ del repo de xv6, y hay que agregarlo a
// UPROGS en el Makefile (ver instrucciones al final).
//
// Pruebas incluidas:
//   1. correctness_basic  -> padre e hijo escriben la misma variable,
//                            no se deben ver afectados entre sí.
//   2. correctness_multi  -> varios hijos escriben páginas distintas
//                            de un arreglo grande (varias páginas),
//                            se verifica aislamiento total.
//   3. correctness_reread -> confirma que LEER (sin escribir) una
//                            página COW no dispara ninguna copia.
//   4. timing_fork        -> mide el tiempo de muchos fork() de un
//                            proceso con memoria grande, para comparar
//                            antes/después de implementar COW.
//
// Uso: correr "cowtest" desde el shell de xv6.

#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

#define PGSIZE 4096


// 1. Prueba básica: padre e hijo escriben la misma variable de datos
//    (misma página COW) y no se deben ver afectados entre sí.

void
correctness_basic(void)
{
  printf("== test 1: correctness_basic ==\n");

  volatile int shared_var = 111;
  int pid = fork();

  if (pid < 0) {
    printf("fork failed\n");
    exit(1);
  }

  if (pid == 0) {
    
    shared_var = 222;
    if (shared_var != 222) {
      printf("FALLO: hijo no ve su propio valor escrito\n");
      exit(1);
    }
    printf("hijo: shared_var = %d (esperado 222)\n", shared_var);
    exit(0);
  } else {
    wait(0);
    
    if (shared_var != 111) {
      printf("FALLO: padre ve shared_var = %d (esperado 111) -- "
             "la memoria del padre fue corrompida por el hijo\n",
             shared_var);
      exit(1);
    }
    printf("padre: shared_var = %d (esperado 111)\n", shared_var);
    printf("test 1: OK\n\n");
  }
}


// 2. Varios hijos escriben en distintas partes de un arreglo grande
//    (varias páginas físicas), para probar refcounting con más de
//    2 referencias simultáneas a la misma página.

#define NCHILD 4
#define ARR_PAGES 4
#define ARR_SIZE ((PGSIZE * ARR_PAGES) / sizeof(int))

int big_array[ARR_SIZE];

void
correctness_multi(void)
{
  printf("== test 2: correctness_multi ==\n");

  for (int i = 0; i < ARR_SIZE; i++)
    big_array[i] = 1000;

  int pids[NCHILD];
  int i;

  for (i = 0; i < NCHILD; i++) {
    int pid = fork();
    if (pid < 0) {
      printf("fork failed\n");
      exit(1);
    }
    if (pid == 0) {
      
      int myval = 2000 + i;
      for (int j = 0; j < ARR_SIZE; j++)
        big_array[j] = myval;

      
      for (int j = 0; j < ARR_SIZE; j++) {
        if (big_array[j] != myval) {
          printf("FALLO: hijo %d ve big_array[%d] = %d (esperado %d)\n",
                 i, j, big_array[j], myval);
          exit(1);
        }
      }
      exit(0);
    }
    pids[i] = pid;
  }

  for (i = 0; i < NCHILD; i++)
    wait(0);

  
  for (i = 0; i < ARR_SIZE; i++) {
    if (big_array[i] != 1000) {
      printf("FALLO: padre ve big_array[%d] = %d (esperado 1000) -- "
             "algún hijo corrompió la memoria del padre\n",
             i, big_array[i]);
      exit(1);
    }
  }

  printf("test 2: OK (%d hijos, %d paginas, sin corrupcion cruzada)\n\n",
         NCHILD, ARR_PAGES);
}


// 3. Leer (sin escribir) una página COW no debe requerir copia.
//    No podemos medir directamente "no hubo copia" desde espacio de
//    usuario, pero sí podemos confirmar que la lectura funciona
//    correctamente sobre la página compartida sin haber escrito antes.

int readonly_data[PGSIZE / sizeof(int)];

void
correctness_reread(void)
{
  printf("== test 3: correctness_reread ==\n");

  for (int i = 0; i < PGSIZE / sizeof(int); i++)
    readonly_data[i] = 42;

  int pid = fork();
  if (pid < 0) {
    printf("fork failed\n");
    exit(1);
  }

  if (pid == 0) {
    
    int sum = 0;
    for (int i = 0; i < PGSIZE / sizeof(int); i++)
      sum += readonly_data[i];

    if (sum != 42 * (PGSIZE / sizeof(int))) {
      printf("FALLO: suma incorrecta al leer pagina COW: %d\n", sum);
      exit(1);
    }
    printf("hijo: lectura de pagina COW correcta (sum=%d)\n", sum);
    exit(0);
  } else {
    wait(0);
    printf("test 3: OK\n\n");
  }
}


// 4. Medición de tiempo: fork() repetido de un proceso con memoria
//    grande. Compara esto antes/después de implementar COW -- debería
//    bajar notablemente porque ya no se copia físicamente cada página.

#define TIMING_PAGES 16
#define TIMING_SIZE ((PGSIZE * TIMING_PAGES) / sizeof(int))
int timing_array[TIMING_SIZE];

void
timing_fork(void)
{
  printf("== test 4: timing_fork ==\n");

  for (int i = 0; i < TIMING_SIZE; i++)
    timing_array[i] = i;

  int NFORKS = 20;
  int start = uptime();

  for (int i = 0; i < NFORKS; i++) {
    int pid = fork();
    if (pid < 0) {
      printf("fork failed\n");
      exit(1);
    }
    if (pid == 0) {
      
      exit(0);
    } else {
      wait(0);
    }
  }

  int end = uptime();
  printf("tiempo total: %d ticks para %d forks de un proceso de %d KB\n",
         end - start, NFORKS, (TIMING_PAGES * PGSIZE) / 1024);
  printf("promedio: %d ticks/fork (ver nota abajo)\n\n",
         (end - start) / NFORKS);
}

int
main(int argc, char *argv[])
{
  printf("=== cowtest: pruebas de Copy-on-Write ===\n\n");

  correctness_basic();
  correctness_multi();
  correctness_reread();
  timing_fork();

  printf("=== todas las pruebas de correctitud pasaron ===\n");
  printf("nota: 'uptime' mide en ticks del reloj (~cada 1/10 seg en xv6),\n");
  printf("      asi que con pocos forks el numero puede salir en 0.\n");
  printf("      sube NFORKS en el codigo si quieres mas resolucion.\n");
  exit(0);
}
