const TYPE_COLORS: Record<string, string> = {
  INT: '#58a6ff',
  INTEGER: '#58a6ff',
  BIGINT: '#58a6ff',
  SMALLINT: '#58a6ff',
  FLOAT: '#79c0ff',
  DOUBLE: '#79c0ff',
  DECIMAL: '#79c0ff',
  NUMERIC: '#79c0ff',
  VARCHAR: '#3fb950',
  TEXT: '#3fb950',
  STRING: '#3fb950',
  CHAR: '#3fb950',
  DATE: '#d2a8ff',
  DATETIME: '#d2a8ff',
  TIMESTAMP: '#d2a8ff',
  BOOLEAN: '#ff7b72',
  BOOL: '#ff7b72',
}

export function getTypeColor(type: string): string {
  const upper = type.toUpperCase()
  return TYPE_COLORS[upper] ?? '#8b949e'
}
