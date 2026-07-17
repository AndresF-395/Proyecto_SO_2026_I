// Physical memory allocator, for user processes,
// kernel stacks, page-table pages,
// and pipe buffers. Allocates whole 4096-byte pages.

#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "riscv.h"
#include "defs.h"

void freerange(void *pa_start, void *pa_end);

extern char end[]; // first address after kernel.
                   // defined by kernel.ld.

struct run {
  struct run *next;
};

struct {
  struct spinlock lock;
  struct run *freelist;
} kmem;

// Copy-on-write: contador de referencias por página física.
// Indexado por número de página (pa / PGSIZE).
struct spinlock reflock;
uint8 refcount[PHYSTOP / PGSIZE];

#define PA2IDX(pa) (((uint64)(pa)) / PGSIZE)

void
kinit()
{
  initlock(&kmem.lock, "kmem");
  initlock(&reflock, "refcount");
  freerange(end, (void *)PHYSTOP);
}

void
freerange(void *pa_start, void *pa_end)
{
  char *p;
  p = (char *)PGROUNDUP((uint64)pa_start);
  for (; p + PGSIZE <= (char *)pa_end; p += PGSIZE)
    kfree(p);
}

// Free the page of physical memory pointed at by pa,
// which normally should have been returned by a
// call to kalloc().  (The exception is when
// initializing the allocator; see kinit above.)
void
kfree(void *pa)
{
  struct run *r;

  if (((uint64)pa % PGSIZE) != 0 || (char *)pa < end || (uint64)pa >= PHYSTOP)
    panic("kfree");

  // Decrementar el refcount. Si otro proceso todavía referencia esta
  // página física (caso COW compartido), no la liberamos todavía.
  acquire(&reflock);
  if (refcount[PA2IDX(pa)] > 0)
    refcount[PA2IDX(pa)]--;
  int rc = refcount[PA2IDX(pa)];
  release(&reflock);

  if (rc > 0)
    return;

  // Fill with junk to catch dangling refs.
  memset(pa, 1, PGSIZE);

  r = (struct run *)pa;

  acquire(&kmem.lock);
  r->next = kmem.freelist;
  kmem.freelist = r;
  release(&kmem.lock);
}

// Allocate one 4096-byte page of physical memory.
// Returns a pointer that the kernel can use.
// Returns 0 if the memory cannot be allocated.
void *
kalloc(void)
{
  struct run *r;

  acquire(&kmem.lock);
  r = kmem.freelist;
  if (r)
    kmem.freelist = r->next;
  release(&kmem.lock);

  if (r) {
    memset((char *)r, 5, PGSIZE); // fill with junk

    // Toda página recién asignada arranca con una única referencia.
    acquire(&reflock);
    refcount[PA2IDX(r)] = 1;
    release(&reflock);
  }
  return (void *)r;
}

// Incrementa el refcount de una página física.
// Usado por uvmcopy() al compartir una página COW entre padre e hijo.
void
krefinc(void *pa)
{
  acquire(&reflock);
  refcount[PA2IDX(pa)]++;
  release(&reflock);
}

// Consulta el refcount de una página física.
// Usado por vmfault() para decidir si copiar o solo reactivar PTE_W.
int
krefcount(void *pa)
{
  int rc;
  acquire(&reflock);
  rc = refcount[PA2IDX(pa)];
  release(&reflock);
  return rc;
}