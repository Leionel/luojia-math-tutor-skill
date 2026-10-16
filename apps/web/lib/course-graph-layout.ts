/** Deterministic, bounded force layout. Links describe relationships, not a syllabus order. */
export function layoutCourseNodes<T extends { id: string }>(nodes: T[], edges: Array<{ source: string; target: string }>) {
  if (!nodes.length) return [];
  const sorted = [...nodes].sort((a, b) => a.id.localeCompare(b.id));
  const index = new Map(sorted.map((node, i) => [node.id, i]));
  const links = edges.filter((e) => index.has(e.source) && index.has(e.target) && e.source !== e.target);
  const points = sorted.map((_, i) => {
    const angle = i * 2.399963229728653;
    const radius = 100 + 40 * Math.sqrt(i);
    return { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
  });
  for (let step = 0; step < 360; step++) {
    const force = points.map((p) => ({ x: -p.x * 0.014, y: -p.y * 0.014 }));
    for (let i = 0; i < points.length; i++) {
      for (let j = i + 1; j < points.length; j++) {
        const dx = points[i].x - points[j].x;
        const dy = points[i].y - points[j].y;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const repel = 12000 / (distance * distance) + Math.max(0, 135 - distance) * 0.18;
        force[i].x += dx / distance * repel; force[i].y += dy / distance * repel;
        force[j].x -= dx / distance * repel; force[j].y -= dy / distance * repel;
      }
    }
    for (const link of links) {
      const a = index.get(link.source)!, b = index.get(link.target)!;
      const dx = points[b].x - points[a].x, dy = points[b].y - points[a].y;
      const distance = Math.max(1, Math.hypot(dx, dy));
      const spring = (distance - 160) * 0.035;
      force[a].x += dx / distance * spring; force[a].y += dy / distance * spring;
      force[b].x -= dx / distance * spring; force[b].y -= dy / distance * spring;
    }
    const cooling = 0.9 - step / 600;
    points.forEach((p, i) => {
      p.x += Math.max(-12, Math.min(12, force[i].x)) * cooling;
      p.y += Math.max(-12, Math.min(12, force[i].y)) * cooling;
    });
  }
  return nodes.map((node) => ({ ...node, width: 48, height: 48,
    position: { x: points[index.get(node.id)!].x, y: points[index.get(node.id)!].y } }));
}
