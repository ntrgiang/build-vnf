/*
 * collections.h
 *
 * Container datatype providing convenient encapsulations and operations on
 * DPDK's general built-in packet container: mbuf
 * (https://doc.dpdk.org/guides/prog_guide/mbuf_lib.html)
 *
 */

#ifndef COLLECTIONS_H
#define COLLECTIONS_H

/**
 * @file
 *
 * Container datatype collections
 *
 */

#include <rte_common.h>
#include <rte_mbuf.h>

#include <stdint.h>

/* A vector of mbufs e.g. belonging to one APU */

/**
 * Macro to interate over all mbufs in a vector
 */
#define MVEC_FOREACH_MBUF(i, vec) for (i = 0; (uint16_t)i < vec->len; i = i + 1)

/**
 * struct mvec - DPDK Mbuf vector.
 *
 * For performance, this data structure should always be allocated on the stack.
 * To operate headers and payload like a Linux-like socket buffer.
 *
 * Socket buffer reference: http://vger.kernel.org/~davem/skb_data.html
 */
struct mvec {
	struct rte_mbuf **head;
	uint16_t len; /**< Number of mbufs in the vector */

	uint16_t mbuf_payload_off; /**< Offset of the paload */
} __rte_cache_aligned;

/**
 * mvec_new() - Create a new mbuf vector.
 *
 * @param mbuf_arr: An array of pointers to mbufs.
 * @param len: The length of the array.
 *
 * @return: Pointer to the new mbuf vector.
 */
struct mvec *mvec_new(struct rte_mbuf **mbuf_arr, uint16_t len);

/**
 * mvec_free() - Free all mbufs in the vector.
 *
 * @param vec
 */
void mvec_free(struct mvec *vec);

/**
 * mvec_free_part() - Free a part of mbufs in the vector
 *
 * @param vec
 * @param offset
 */
void mvec_free_part(struct mvec *vec, uint16_t offset);

/**
 * print_mvec() - Print metadata of a mbuf vector.
 *
 * @param vec
 */
void print_mvec(struct mvec *vec);

/**
 * mvec_datacmp() - Compare two mbuf vectors
 *
 * @param v1,v2
 * Pointers to mbuf vector structs
 *
 * @return:
 * -1 if v1 is smaller than v2 in uint8_t format. +1 if v1 is bigger.  0 if v1
 *  and v2 compare equal.
 */
int mvec_datacmp(struct mvec *v1, struct mvec *v2);

/**
 * mvec_push() - Like skb_push. Push data to the reserved header room of all
 * mbufs in the vector. Data is prepended to mbuf data room.
 *
 * @param v: mbuf vector to modify.
 * @param len: Number of bytes to mark as used.
 *
 * Raise panic if header room is not enough.
 *
 */
void mvec_push(struct mvec *v, uint16_t len);

void mvec_push_u8(struct mvec *v, uint8_t value);
void mvec_push_u16(struct mvec *v, uint16_t value);
void mvec_push_u32(struct mvec *v, uint32_t value);
void mvec_push_u64(struct mvec *v, uint64_t value);

/**
 * mvec_pull() - Like skb_pull - Remove data from the beginning of the data room
 * of all mbufs in the vector.
 *
 * @param v: mbuf vector to modify.
 * @param len: Number of bytes to read from the data room.
 *
 * Raise panic if data room is not enough.
 */
void mvec_pull(struct mvec *v, uint16_t len);

void mvec_pull_u8(struct mvec *v, uint8_t *values);
void mvec_pull_u16(struct mvec *v, uint16_t *values);
void mvec_pull_u32(struct mvec *v, uint32_t *values);
void mvec_pull_u64(struct mvec *v, uint64_t *values);

/**
 * mvec_deep_copy() - Return a deep copy of a given mvec. Mbufs are allocated
 * from the pool for the new copied mvec.
 *
 * @param pool
 * @param v
 *
 * @return
 */
struct mvec *mvec_deep_copy(struct rte_mempool *pool, struct mvec *v);

#endif /* !COLLECTIONS_H */
