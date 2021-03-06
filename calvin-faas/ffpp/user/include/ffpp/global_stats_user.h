/*
gloabls_stats_user.h
*/

#ifndef GLOBAL_STATS_USER_H
#define GLOBAL_STATS_USER_H

// #include <unistd.h>
// #include <stdlib.h>

#define TOTAL_VALS 100000

extern double g_csv_pps[TOTAL_VALS];
extern double g_csv_ts[TOTAL_VALS];
extern double g_csv_iat[TOTAL_VALS];
extern double g_csv_cpu_util[TOTAL_VALS];
extern unsigned int g_csv_freq[TOTAL_VALS];
extern unsigned int g_csv_num_val;
extern int g_csv_num_round;
extern int g_csv_empty_cnt;
extern int g_csv_empty_cnt_threshold;
extern bool g_csv_saved_stream;

extern double cur_time;

#endif
