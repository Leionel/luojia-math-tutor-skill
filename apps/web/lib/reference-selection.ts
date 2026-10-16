/** Clearing a reference supersedes pending validation just like selecting one. */
export class ReferenceSelection {
  private revision = 0;
  begin(environmentCurrent: () => boolean) {
    const revision = ++this.revision;
    return () => revision === this.revision && environmentCurrent();
  }
}
