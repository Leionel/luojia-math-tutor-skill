/** Own work before the first await; invalidate all callbacks on a view change. */
export type ChatLease = { controller: AbortController; revision: number; owner: string };
export class ChatLifetime {
  private revision = 0;
  private active: ChatLease | null = null;
  begin(owner: string): ChatLease | null {
    if (this.active) return null;
    const lease = {controller: new AbortController(), revision: this.revision, owner};
    this.active = lease;
    return lease;
  }
  current(lease: ChatLease, owner: string): boolean {
    return this.active === lease && lease.revision === this.revision && lease.owner === owner;
  }
  finish(lease: ChatLease) { if (this.active === lease) this.active = null; }
  cancel() { this.active?.controller.abort(); }
  invalidate() { this.cancel(); this.active = null; this.revision += 1; }
  get version() { return this.revision; }
}
