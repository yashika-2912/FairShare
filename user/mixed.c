#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

static uint64
work(uint64 value, int rounds)
{
  for (int i = 0; i < rounds; i++)
    value = (value << 5) - value + i;
  return value;
}

int
main(void)
{
  uint64 checksum = 11;

  printf("mixed: start tick %d\n", uptime());
  for (int iteration = 1; iteration <= 16; iteration++) {
    // The first half is CPU-heavy; the second half sleeps longer.
    if (iteration <= 8) {
      checksum = work(checksum, 1200000);
      pause(1);
    } else {
      checksum = work(checksum, 120000);
      pause(4);
    }
    printf("mixed: iteration %d phase %s tick %d\n", iteration,
           iteration <= 8 ? "cpu" : "io", uptime());
  }
  printf("mixed: done tick %d checksum %lx\n", uptime(), checksum);
  exit(0);
}
