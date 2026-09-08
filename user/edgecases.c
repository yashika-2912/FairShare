#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

static volatile uint64 work_sink;

static uint64
burn(uint64 value, int rounds)
{
  for (int i = 0; i < rounds; i++) {
    value = value * 214013 + 2531011 + i;
    work_sink = value;
  }
  return value;
}

static void
never_sleep(void)
{
  uint64 checksum = burn(19, 80000000);
  printf("edgecases: never-sleep done tick %d checksum %lx\n", uptime(),
         checksum);
  exit(0);
}

static void
immediate_sleep(void)
{
  for (int i = 0; i < 24; i++)
    pause(1);
  printf("edgecases: immediate-sleep done tick %d\n", uptime());
  exit(0);
}

static void
must_wait_ok(int pid, const char *name)
{
  int status;

  if (wait(&status) != pid || status != 0) {
    printf("edgecases: %s failed\n", name);
    exit(1);
  }
}

int
main(void)
{
  int pid;

  pid = fork();
  if (pid < 0) {
    printf("edgecases: never-sleep fork failed\n");
    exit(1);
  }
  if (pid == 0)
    never_sleep();
  must_wait_ok(pid, "never-sleep");

  pid = fork();
  if (pid < 0) {
    printf("edgecases: immediate-sleep fork failed\n");
    exit(1);
  }
  if (pid == 0)
    immediate_sleep();
  must_wait_ok(pid, "immediate-sleep");

  for (int i = 0; i < 80; i++) {
    pid = fork();
    if (pid < 0) {
      printf("edgecases: churn fork failed at %d\n", i);
      exit(1);
    }
    if (pid == 0)
      exit(0);
    must_wait_ok(pid, "fork-exit churn");
  }
  printf("edgecases: PASS rapid fork/exit churn 80\n");
  exit(0);
}
