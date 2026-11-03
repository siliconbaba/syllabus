# Architecture

Native scheduled runner → supervisor CLI → one descriptor → claimed worker context → immutable result/evidence → submit validation → atomic STATE commit → derived queue views. The CLI never calls an LLM, undocumented endpoint, UI automation or network. It never generates content.

STATE is the transaction record. Single stable LOCK.json inode uses macOS flock; crash releases the kernel lock, regardless of stale JSON metadata. Atomic replace + fsync protects STATE and descriptors. A persistent worker claim prevents concurrent scheduled runs from duplicating work; no automatic lease expiry. Native runner must use a unique real context ID and fresh QA context. Claims and tokens are coordination, not a security boundary.

Current bootstrap hold preserves user prohibition on redesign. Native scheduling is supported, but a scheduled run with independent contexts is not exercised in this bootstrap. launchd fallback only validates/routes; it cannot execute a worker. No active schedule installed.

Application/content files and preexisting artifacts stay untouched. bootstrap-input-hashes.json records preexisting file hashes; bootstrap verification reports any change.
