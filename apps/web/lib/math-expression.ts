type Token =
  | { type: "number"; value: number }
  | { type: "identifier"; value: string }
  | { type: "operator"; value: "+" | "-" | "*" | "/" | "**" }
  | { type: "leftParen" | "rightParen" | "comma" | "eof" };

const FUNCTIONS: Record<string, (value: number) => number> = {
  abs: Math.abs,
  cos: Math.cos,
  exp: Math.exp,
  log: Math.log,
  sin: Math.sin,
  sqrt: Math.sqrt,
  tan: Math.tan,
};

const CONSTANTS: Record<string, number> = {
  e: Math.E,
  pi: Math.PI,
};

export type PlotPoint = { x: number; y: number };

export type PlotPoints = {
  pts: PlotPoint[];
  minY: number;
  maxY: number;
};

function tokenize(expression: string): Token[] {
  if (!expression || expression.length > 200) {
    throw new Error("Unsupported expression length");
  }

  const tokens: Token[] = [];
  let index = 0;
  const source = expression.replace(/\^/g, "**");

  while (index < source.length) {
    const char = source[index];
    if (/\s/.test(char)) {
      index += 1;
      continue;
    }
    if (/\d/.test(char) || (char === "." && /\d/.test(source[index + 1] || ""))) {
      const start = index;
      index += 1;
      while (index < source.length && /[\d.]/.test(source[index])) index += 1;
      const value = Number(source.slice(start, index));
      if (!Number.isFinite(value)) throw new Error("Invalid number");
      tokens.push({ type: "number", value });
      continue;
    }
    if (/[A-Za-z_]/.test(char)) {
      const start = index;
      index += 1;
      while (index < source.length && /[A-Za-z0-9_]/.test(source[index])) index += 1;
      tokens.push({ type: "identifier", value: source.slice(start, index).toLowerCase() });
      continue;
    }
    if (char === "(") {
      tokens.push({ type: "leftParen" });
      index += 1;
      continue;
    }
    if (char === ")") {
      tokens.push({ type: "rightParen" });
      index += 1;
      continue;
    }
    if (char === ",") {
      tokens.push({ type: "comma" });
      index += 1;
      continue;
    }
    if ("+-*/".includes(char)) {
      if (char === "*" && source[index + 1] === "*") {
        tokens.push({ type: "operator", value: "**" });
        index += 2;
      } else {
        tokens.push({ type: "operator", value: char as "+" | "-" | "*" | "/" });
        index += 1;
      }
      continue;
    }
    throw new Error("Unsupported character");
  }

  tokens.push({ type: "eof" });
  return tokens;
}

class Parser {
  private index = 0;
  private readonly tokens: Token[];
  private readonly x: number;

  constructor(tokens: Token[], x: number) {
    this.tokens = tokens;
    this.x = x;
  }

  parse(): number {
    const value = this.parseAddSub();
    if (this.current().type !== "eof") {
      throw new Error("Unexpected token");
    }
    return value;
  }

  private current(): Token {
    return this.tokens[this.index];
  }

  private advance(): Token {
    const token = this.current();
    this.index += 1;
    return token;
  }

  private currentOperator(...values: Array<"+" | "-" | "*" | "/" | "**">): Extract<Token, { type: "operator" }> | null {
    const token = this.current();
    if (token.type === "operator" && values.includes(token.value)) {
      return token;
    }
    return null;
  }

  private parseAddSub(): number {
    let value = this.parseMulDiv();
    let operator = this.currentOperator("+", "-");
    while (operator) {
      this.advance();
      const right = this.parseMulDiv();
      value = operator.value === "+" ? value + right : value - right;
      operator = this.currentOperator("+", "-");
    }
    return value;
  }

  private parseMulDiv(): number {
    let value = this.parsePower();
    let operator = this.currentOperator("*", "/");
    while (operator) {
      this.advance();
      const right = this.parsePower();
      value = operator.value === "*" ? value * right : value / right;
      operator = this.currentOperator("*", "/");
    }
    return value;
  }

  private parsePower(): number {
    const value = this.parseUnary();
    if (this.currentOperator("**")) {
      this.advance();
      return value ** this.parsePower();
    }
    return value;
  }

  private parseUnary(): number {
    const operator = this.currentOperator("+", "-");
    if (operator) {
      this.advance();
      const value = this.parseUnary();
      return operator.value === "-" ? -value : value;
    }
    return this.parsePrimary();
  }

  private parsePrimary(): number {
    const token = this.advance();
    if (token.type === "number") return token.value;
    if (token.type === "leftParen") {
      const value = this.parseAddSub();
      if (this.advance().type !== "rightParen") throw new Error("Missing right parenthesis");
      return value;
    }
    if (token.type === "identifier") {
      if (token.value === "x") return this.x;
      if (token.value in CONSTANTS) return CONSTANTS[token.value];
      if (!(token.value in FUNCTIONS) || this.advance().type !== "leftParen") {
        throw new Error(`Unsupported identifier: ${token.value}`);
      }
      const argument = this.parseAddSub();
      if (this.advance().type !== "rightParen") throw new Error("Missing right parenthesis");
      return FUNCTIONS[token.value](argument);
    }
    throw new Error("Unexpected token");
  }
}

export function evaluateMathExpression(expression: string, x: number): number {
  const value = new Parser(tokenize(expression), x).parse();
  if (!Number.isFinite(value)) {
    throw new Error("Expression did not produce a finite number");
  }
  return value;
}

export function buildPlotPoints(
  expression: string,
  minX: number,
  maxX: number,
  samples = 100,
): PlotPoints | null {
  if (!Number.isFinite(minX) || !Number.isFinite(maxX) || minX >= maxX || samples < 2) {
    return null;
  }

  const step = (maxX - minX) / samples;
  const pts: PlotPoint[] = [];
  let minY = Infinity;
  let maxY = -Infinity;

  for (let i = 0; i <= samples; i++) {
    const x = minX + step * i;
    try {
      const y = evaluateMathExpression(expression, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      pts.push({ x, y });
    } catch {
      // Singular samples are omitted so continuous portions can still render.
    }
  }

  if (!pts.length || !Number.isFinite(minY) || !Number.isFinite(maxY)) {
    return null;
  }

  const yRange = maxY === minY ? 1 : maxY - minY;
  return {
    pts,
    minY: minY - yRange * 0.1,
    maxY: maxY + yRange * 0.1,
  };
}
