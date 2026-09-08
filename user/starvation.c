#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

struct hog_report {
  int chunk;
  int tick;
  int gap;
};

static volatile uint64 work_sink;

static uint64
burn(uint64 value, int rounds)
{
  for (int i = 0; i < rounds; i++) {
    value = value * 6364136223846793005ULL + i;
    work_sink = value;
  }
  return value;
}

static void
short_job(int job)
{
  uint64 checksum = burn((uint64)job + 1, 120000);
  if (checksum == 0)
    printf("starvation: impossible short-job checksum\n");
  exit(0);
}

static void
hog(int reportfd)
{
  uint64 checksum = 3;
  int last_tick = uptime();

  for (int chunk = 1; chunk <= 40; chunk++) {
    struct hog_report report;

    checksum = burn(checksum, 5000000);
    if (chunk % 4 == 0) {
      report.chunk = chunk;
      report.tick = uptime();
      report.gap = report.tick - last_tick;
      last_tick = report.tick;
      if (write(reportfd, &report, sizeof(report)) != sizeof(report))
        exit(1);
    }
  }
  if (checksum == 0)
    printf("starvation: impossible hog checksum\n");
  close(reportfd);
  exit(0);
}

int
main(void)
{
  int fds[2];
  int max_gap = 0;
  int reports = 0;
  int status;
  int hogpid;

  if (pipe(fds) < 0) {
    printf("starvation: pipe failed\n");
    exit(1);
  }
  hogpid = fork();
  if (hogpid < 0) {
    printf("starvation: fork hog failed\n");
    exit(1);
  }
  if (hogpid == 0) {
    close(fds[0]);
    hog(fds[1]);
  }

  close(fds[1]);
  printf("starvation: hog %d with short-job churn\n", hogpid);
  for (int round = 0; round < 20; round++) {
    for (int job = 0; job < 4; job++) {
      int pid = fork();
      if (pid < 0) {
        printf("starvation: short-job fork failed at round %d\n", round);
        exit(1);
      }
      if (pid == 0)
        short_job(round * 4 + job);
    }
    for (int job = 0; job < 4; job++)
      if (wait(&status) < 0 || status != 0) {
        printf("starvation: short-job wait failed\n");
        exit(1);
      }
  }

  for (;;) {
    struct hog_report report;
    int n = read(fds[0], &report, sizeof(report));

    if (n == 0)
      break;
    if (n != sizeof(report)) {
      printf("starvation: partial hog report\n");
      exit(1);
    }
    reports++;
    if (report.gap > max_gap)
      max_gap = report.gap;
    printf("starvation: hog chunk %d tick %d gap %d\n", report.chunk,
           report.tick, report.gap);
  }
  close(fds[0]);
  if (wait(&status) != hogpid || status != 0) {
    printf("starvation: hog failed\n");
    exit(1);
  }
  printf("starvation: PASS reports %d max-observed-gap %d ticks\n", reports,
         max_gap);
  exit(0);
}
