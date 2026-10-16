export function parseTrace(text: string): (number | string)[] {
  const parts = text.trim().split(/[\s,，]+/).filter(Boolean);
  if (parts.length < 2 || parts.length > 101) throw new Error("请填写 2–101 个迭代值，包含初值");
  return parts.map(part => {
    if (["NaN", "Inf", "-Inf"].includes(part)) return part;
    const value = Number(part);
    if (!Number.isFinite(value) || Math.abs(value) > 1e50) throw new Error(`无法识别迭代值：${part}`);
    return value;
  });
}

export function finiteNumber(text: string, label: string): number {
  if (!text.trim() || !Number.isFinite(Number(text))) throw new Error(`${label}需要有限数值`);
  return Number(text);
}

export function notesForSource<T extends {source_id:string;section_id?:string|null}>(notes:T[], sourceId:string|undefined, sectionId:string|null=null):T[]{
  return notes.filter(note=>note.source_id===sourceId && (sectionId===null || note.section_id===sectionId));
}

export function stableRequestId(storage: Pick<Storage, "getItem" | "setItem">, key: string, payload: unknown, createId: () => string): string {
  const fingerprint = JSON.stringify(payload);
  try {
    const previous = JSON.parse(storage.getItem(key) ?? "null");
    if (previous?.fingerprint === fingerprint && typeof previous?.id === "string") return previous.id;
  } catch { /* Recover a corrupt browser draft without changing server records. */ }
  const id = createId();
  storage.setItem(key, JSON.stringify({fingerprint, id}));
  return id;
}

export function paragraphSpans(quote: string): {start:number;end:number;label:string}[] {
  const result = [{start:0,end:Math.min(Array.from(quote).length,6000),label:"当前原文范围（最多6000字符）"}];
  let offset = 0;
  for (const line of quote.split("\n")) {
    const length = Array.from(line).length;
    if (line.trim() && result.length <= 80) result.push({start:offset,end:offset+Math.min(length,6000),label:line.slice(0,70)});
    offset += length + 1;
  }
  return result;
}

/** Restore only valid, unconfirmed choices belonging to this assessment. */
export function assessmentDraft(raw: string | null, questions: {id:string;options:string[]}[], answers: Record<string,number>): Record<string,number> {
  try {
    const value: unknown = JSON.parse(raw ?? "null");
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    const result: Record<string,number> = {};
    for (const q of questions) {
      const option = (value as Record<string,unknown>)[q.id];
      if (!(q.id in answers) && typeof option === "number" && Number.isInteger(option) && option >= 0 && option < q.options.length) result[q.id] = option;
    }
    return result;
  } catch { return {}; }
}
