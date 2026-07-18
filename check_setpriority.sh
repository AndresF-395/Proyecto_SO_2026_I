#!/bin/bash
echo "=== Buscando referencias a 'setpriority' en el árbol de fuentes ==="
grep -rn "setpriority" kernel/ user/ 2>/dev/null
echo ""
echo "=== Si solo aparece 'ksetpriority' en kernel/proc.c, la syscall NO está expuesta a usuario ==="