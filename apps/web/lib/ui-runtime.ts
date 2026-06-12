export const SESSION_BATCH_SIZE = 30;

export type MasteryTrend = "up" | "down" | "flat";

export type MasteryTrendSnapshot = {
  currentFingerprint: string;
  currentAverage: number;
  previousAverage: number | null;
  trend: MasteryTrend | null;
};

export function clampUnit(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

export function projectRadarValues(
  points: Array<{ value: number; assessed: boolean }>,
): number[] {
  return points.map((point) => point.assessed ? clampUnit(point.value) : 0);
}

export function nextVisibleSessionCount(
  current: number,
  total: number,
): number {
  return Math.min(
    Math.max(0, total),
    Math.max(SESSION_BATCH_SIZE, current + SESSION_BATCH_SIZE),
  );
}

function trendFromDifference(difference: number): MasteryTrend {
  if (Math.abs(difference) < 2) return "flat";
  return difference > 0 ? "up" : "down";
}

export function advanceMasteryTrend(
  stored: MasteryTrendSnapshot | null,
  fingerprint: string,
  average: number,
): {
  snapshot: MasteryTrendSnapshot;
  trend: MasteryTrend | null;
  previousAverage: number | null;
} {
  const currentAverage = Math.min(100, Math.max(0, Math.round(average)));

  if (!stored) {
    const snapshot: MasteryTrendSnapshot = {
      currentFingerprint: fingerprint,
      currentAverage,
      previousAverage: null,
      trend: null,
    };
    return { snapshot, trend: null, previousAverage: null };
  }

  if (stored.currentFingerprint === fingerprint) {
    return {
      snapshot: stored,
      trend: stored.trend,
      previousAverage: stored.previousAverage,
    };
  }

  const previousAverage = stored.currentAverage;
  const trend = trendFromDifference(currentAverage - previousAverage);
  const snapshot: MasteryTrendSnapshot = {
    currentFingerprint: fingerprint,
    currentAverage,
    previousAverage,
    trend,
  };
  return { snapshot, trend, previousAverage };
}

export function parseMasteryTrendSnapshot(
  raw: string | null,
): MasteryTrendSnapshot | null {
  if (!raw) return null;

  try {
    const value = JSON.parse(raw) as Partial<MasteryTrendSnapshot>;
    const validTrend = value.trend === null
      || value.trend === "up"
      || value.trend === "down"
      || value.trend === "flat";
    const previousAverage = value.previousAverage;
    const validPrevious = previousAverage === null
      || (
        typeof previousAverage === "number"
        && Number.isFinite(previousAverage)
      );

    if (
      typeof value.currentFingerprint !== "string"
      || typeof value.currentAverage !== "number"
      || !Number.isFinite(value.currentAverage)
      || !validPrevious
      || !validTrend
    ) {
      return null;
    }

    return {
      currentFingerprint: value.currentFingerprint,
      currentAverage: Math.min(100, Math.max(0, value.currentAverage)),
      previousAverage: previousAverage === null
        ? null
        : Math.min(100, Math.max(0, previousAverage as number)),
      trend: value.trend ?? null,
    };
  } catch {
    return null;
  }
}
