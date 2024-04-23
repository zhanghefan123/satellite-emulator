sudo iptables -A FORWARD -j ACCEPT
int br_handle_frame_finish(struct net *net, struct sock *sk, struct sk_buff *skb)
{
	struct net_bridge_port *p = br_port_get_rcu(skb->dev);
	enum br_pkt_type pkt_type = BR_PKT_UNICAST;
	struct net_bridge_fdb_entry *dst = NULL;
	struct net_bridge_mcast_port *pmctx;
	struct net_bridge_mdb_entry *mdst;
	bool local_rcv, mcast_hit = false;
	struct net_bridge_mcast *brmctx;
	struct net_bridge_vlan *vlan;
	struct net_bridge *br;
	u16 vid = 0;
	u8 state;

	if (!p)
		goto drop;

	br = p->br;

	if (br_mst_is_enabled(br)) {
		state = BR_STATE_FORWARDING;
	} else {
		if (p->state == BR_STATE_DISABLED)
			goto drop;

		state = p->state;
	}

	brmctx = &p->br->multicast_ctx;
	pmctx = &p->multicast_ctx;
	if (!br_allowed_ingress(p->br, nbp_vlan_group_rcu(p), skb, &vid,
				&state, &vlan))
		goto out;

	if (p->flags & BR_PORT_LOCKED) {
		struct net_bridge_fdb_entry *fdb_src =
			br_fdb_find_rcu(br, eth_hdr(skb)->h_source, vid);

		if (!fdb_src || READ_ONCE(fdb_src->dst) != p ||
		    test_bit(BR_FDB_LOCAL, &fdb_src->flags))
			goto drop;
	}

	nbp_switchdev_frame_mark(p, skb);

	/* insert into forwarding database after filtering to avoid spoofing */
	if (p->flags & BR_LEARNING)
		br_fdb_update(br, p, eth_hdr(skb)->h_source, vid, 0);

	local_rcv = !!(br->dev->flags & IFF_PROMISC);
	if (is_multicast_ether_addr(eth_hdr(skb)->h_dest)) {
		/* by definition the broadcast is also a multicast address */
		if (is_broadcast_ether_addr(eth_hdr(skb)->h_dest)) {
			pkt_type = BR_PKT_BROADCAST;
			local_rcv = true;
		} else {
			pkt_type = BR_PKT_MULTICAST;
			if (br_multicast_rcv(&brmctx, &pmctx, vlan, skb, vid))
				goto drop;
		}
	}

	if (state == BR_STATE_LEARNING)
		goto drop;

	BR_INPUT_SKB_CB(skb)->brdev = br->dev;
	BR_INPUT_SKB_CB(skb)->src_port_isolated = !!(p->flags & BR_ISOLATED);

	if (IS_ENABLED(CONFIG_INET) &&
	    (skb->protocol == htons(ETH_P_ARP) ||
	     skb->protocol == htons(ETH_P_RARP))) {
		br_do_proxy_suppress_arp(skb, br, vid, p);
	} else if (IS_ENABLED(CONFIG_IPV6) &&
		   skb->protocol == htons(ETH_P_IPV6) &&
		   br_opt_get(br, BROPT_NEIGH_SUPPRESS_ENABLED) &&
		   pskb_may_pull(skb, sizeof(struct ipv6hdr) +
				 sizeof(struct nd_msg)) &&
		   ipv6_hdr(skb)->nexthdr == IPPROTO_ICMPV6) {
			struct nd_msg *msg, _msg;

			msg = br_is_nd_neigh_msg(skb, &_msg);
			if (msg)
				br_do_suppress_nd(skb, br, vid, p, msg);
	}

	switch (pkt_type) {
	case BR_PKT_MULTICAST:
		mdst = br_mdb_get(brmctx, skb, vid);
		if ((mdst || BR_INPUT_SKB_CB_MROUTERS_ONLY(skb)) &&
		    br_multicast_querier_exists(brmctx, eth_hdr(skb), mdst)) {
			if ((mdst && mdst->host_joined) ||
			    br_multicast_is_router(brmctx, skb)) {
				local_rcv = true;
				br->dev->stats.multicast++;
			}
			mcast_hit = true;
		} else {
			local_rcv = true;
			br->dev->stats.multicast++;
		}
		break;
	case BR_PKT_UNICAST:
		dst = br_fdb_find_rcu(br, eth_hdr(skb)->h_dest, vid);
		break;
	default:
		break;
	}

	if (dst) {
		unsigned long now = jiffies;

		if (test_bit(BR_FDB_LOCAL, &dst->flags))
			return br_pass_frame_up(skb);

		if (now != dst->used)
			dst->used = now;
		br_forward(dst->dst, skb, local_rcv, false);
	} else {
		if (!mcast_hit)
			br_flood(br, skb, pkt_type, local_rcv, false);
		else
			br_multicast_flood(mdst, skb, brmctx, local_rcv, false);
	}

	if (local_rcv)
		return br_pass_frame_up(skb);

out:
	return 0;
drop:
	kfree_skb(skb);
	goto out;
}