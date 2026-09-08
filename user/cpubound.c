#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

static volatile uint64 work_sink;

static uint64
burn(uint64 seed, int rounds)
{
  uint64 value = seed;

  for (int i = 0; i < rounds; i++) {
    value = value * 1664525 + 1013904223 + i;
    work_sink = value;
  }
  return value;
}

int
main(void)
{
  uint64 checksum = 1;
  int start = uptime();

  printf("cpubound: start tick %d\n", start);
  for (int chunk = 1; chunk <= 24; chunk++) {
    checksum = burn(checksum, 5000000);
    if (chunk % 6 == 0)
      printf("cpubound: chunk %d tick %d\n", chunk, uptime());
  }
  printf("cpubound: done tick %d checksum %lx\n", uptime(), checksum);
  exit(0);
}
