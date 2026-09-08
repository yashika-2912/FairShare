#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

static uint64
short_burst(uint64 value)
{
  for (int i = 0; i < 80000; i++)
    value = value * 1103515245 + 12345 + i;
  return value;
}

int
main(void)
{
  uint64 checksum = 7;

  printf("iobound: start tick %d\n", uptime());
  for (int iteration = 1; iteration <= 20; iteration++) {
    checksum = short_burst(checksum);
    pause(3);
    if (iteration % 5 == 0)
      printf("iobound: iteration %d tick %d\n", iteration, uptime());
  }
  printf("iobound: done tick %d checksum %lx\n", uptime(), checksum);
  exit(0);
}
