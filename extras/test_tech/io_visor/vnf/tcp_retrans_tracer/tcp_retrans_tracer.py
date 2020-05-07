#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
About: Trace TCP retransmission with eBPF
Ref  : bcc/tools/tcpretrans.py
"""

from __future__ import print_function

import argparse
import ctypes as ct
from socket import AF_INET, AF_INET6, inet_ntop
from struct import pack
from time import strftime

from bcc import BPF

examples = """Examples:
    ./tcpretrans           # Trace TCP retransmits
    ./tcpretrans -l        # Include TLP attempts
"""

parser = argparse.ArgumentParser(
    description="Trace TCP retransmits",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples,
)

parser.add_argument(
    "-l", "--lossprobe", action="store_true", help="Include tail loss probe attempts."
)

args = parser.parse_args()

# Define BPF program
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>
#define RETRANSMIT  1
#define TLP         2

// Separate data structs for ipv4 and ipv6
struct ipv4_data_t {
    // XXX: switch some to u32's when supported
    u64 pid;
    u64 ip;
    u64 saddr;
    u64 daddr;
    u64 lport;
    u64 dport;
    u64 state;
    u64 type;
};

BPF_PERF_OUTPUT(ipv4_events);

struct ipv6_data_t {
    u64 pid;
    u64 ip;
    unsigned __int128 saddr;
    unsigned __int128 daddr;
    u64 lport;
    u64 dport;
    u64 state;
    u64 type;
};

BPF_PERF_OUTPUT(ipv6_events);

static int trace_event(struct pt_regs *ctx, struct sock *skp, int type)
{
    if (skp == NULL)
        return 0;
    u32 pid = bpf_get_current_pid_tgid();
    // pull in details
    u16 family = skp->__sk_common.skc_family;
    u16 lport = skp->__sk_common.skc_num;
    u16 dport = skp->__sk_common.skc_dport;
    char state = skp->__sk_common.skc_state;
    if (family == AF_INET) {
        struct ipv4_data_t data4 = {.pid = pid, .ip = 4, .type = type};
        data4.saddr = skp->__sk_common.skc_rcv_saddr;
        data4.daddr = skp->__sk_common.skc_daddr;
        // lport is host order
        data4.lport = lport;
        data4.dport = ntohs(dport);
        data4.state = state;
        ipv4_events.perf_submit(ctx, &data4, sizeof(data4));
    } else if (family == AF_INET6) {
        struct ipv6_data_t data6 = {.pid = pid, .ip = 6, .type = type};
        bpf_probe_read(&data6.saddr, sizeof(data6.saddr),
            skp->__sk_common.skc_v6_rcv_saddr.in6_u.u6_addr32);
        bpf_probe_read(&data6.daddr, sizeof(data6.daddr),
            skp->__sk_common.skc_v6_daddr.in6_u.u6_addr32);
        // lport is host order
        data6.lport = lport;
        data6.dport = ntohs(dport);
        data6.state = state;
        ipv6_events.perf_submit(ctx, &data6, sizeof(data6));
    }
    // else drop
    return 0;
}
int trace_retransmit(struct pt_regs *ctx, struct sock *sk)
{
    trace_event(ctx, sk, RETRANSMIT);
    return 0;
}
int trace_tlp(struct pt_regs *ctx, struct sock *sk)
{
    trace_event(ctx, sk, TLP);
    return 0;
}
"""


# Event data


class Data_ipv4(ct.Structure):
    _fields_ = [
        ("pid", ct.c_ulonglong),
        ("ip", ct.c_ulonglong),
        ("saddr", ct.c_ulonglong),
        ("daddr", ct.c_ulonglong),
        ("lport", ct.c_ulonglong),
        ("dport", ct.c_ulonglong),
        ("state", ct.c_ulonglong),
        ("type", ct.c_ulonglong),
    ]


class Data_ipv6(ct.Structure):
    _fields_ = [
        ("pid", ct.c_ulonglong),
        ("ip", ct.c_ulonglong),
        ("saddr", (ct.c_ulonglong * 2)),
        ("daddr", (ct.c_ulonglong * 2)),
        ("lport", ct.c_ulonglong),
        ("dport", ct.c_ulonglong),
        ("state", ct.c_ulonglong),
        ("type", ct.c_ulonglong),
    ]


# From bpf_text:
type = {}
type[1] = "R"
type[2] = "L"

# Check net/tcp_states.h
# Wiki: https://en.wikipedia.org/wiki/Transmission_Control_Protocol
tcpstate = {}
tcpstate[1] = "ESTABLISHED"
tcpstate[2] = "SYN_SENT"
tcpstate[3] = "SYN_RECV"
tcpstate[4] = "FIN_WAIT1"
tcpstate[5] = "FIN_WAIT2"
tcpstate[6] = "TIME_WAIT"
tcpstate[7] = "CLOSE"
tcpstate[8] = "CLOSE_WAIT"
tcpstate[9] = "LAST_ACK"
tcpstate[10] = "LISTEN"
tcpstate[11] = "CLOSING"
tcpstate[12] = "NEW_SYN_RECV"


# Process event


def print_ipv4_event(cpu, data, size):
    event = ct.cast(data, ct.POINTER(Data_ipv4)).contents
    print(
        "%-8s %-6d %-2d %-20s %1s> %-20s %s"
        % (
            strftime("%H:%M:%S"),
            event.pid,
            event.ip,
            "%s:%d" % (inet_ntop(AF_INET, pack("I", event.saddr)), event.lport),
            type[event.type],
            "%s:%s" % (inet_ntop(AF_INET, pack("I", event.daddr)), event.dport),
            tcpstate[event.state],
        )
    )


def print_ipv6_event(cpu, data, size):
    event = ct.cast(data, ct.POINTER(Data_ipv6)).contents
    print(
        "%-8s %-6d %-2d %-20s %1s> %-20s %s"
        % (
            strftime("%H:%M:%S"),
            event.pid,
            event.ip,
            "%s:%d" % (inet_ntop(AF_INET6, event.saddr), event.lport),
            type[event.type],
            "%s:%d" % (inet_ntop(AF_INET6, event.daddr), event.dport),
            tcpstate[event.state],
        )
    )


# Initilize the BPF
b = BPF(text=bpf_text)
b.attach_kprobe(event="tcp_retransmit_skb", fn_name="trace_retransmit")
if args.lossprobe:
    b.attach_kprobe(event="tcp_send_loss_probe", fn_name="trace_tlp")

# header
print(
    "%-8s %-6s %-2s %-20s %1s> %-20s %-4s"
    % ("TIME", "PID", "IP", "LADDR:LPORT", "T", "RADDR:RPORT", "STATE")
)

# Read events from perf buffer
b["ipv4_events"].open_perf_buffer(print_ipv4_event)
b["ipv6_events"].open_perf_buffer(print_ipv6_event)

while True:
    b.kprobe_poll()
