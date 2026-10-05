// Client-side mirror of the EBS read-only guard (adapters/source_ebs.py). The
// source ERP is read-only (invariant #1): only a single SELECT/WITH statement
// may run. This is a UX pre-check; the backend enforces it authoritatively.
const FORBIDDEN =
  /\b(insert|update|delete|merge|upsert|drop|alter|create|truncate|grant|revoke|call|exec|execute|begin|declare|commit|rollback|savepoint|lock)\b/i;

function scrub(sql: string): string {
  return sql
    .replace(/\/\*[\s\S]*?\*\//g, ' ') // block comments
    .replace(/--[^\n]*/g, ' ') // line comments
    .replace(/'(?:''|[^'])*'/g, "''") // string literals
    .trim()
    .replace(/;+\s*$/, '')
    .trim();
}

export function isReadonlySelect(sql: string): boolean {
  const s = scrub(sql);
  if (!s) return false;
  if (s.includes(';')) return false; // reject stacked statements
  if (!/^(select|with)\b/i.test(s)) return false;
  if (FORBIDDEN.test(s)) return false;
  return true;
}
