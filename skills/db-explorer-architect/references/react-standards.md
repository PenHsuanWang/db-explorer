# React + TypeScript Coding Standards for Database Explorer

## Overview
This document defines the React and TypeScript coding standards for the Database Explorer frontend. All code must adhere to these standards to ensure maintainability, type safety, and excellent user experience.

**Technology Stack**:
- **React**: 18+ with functional components and hooks
- **TypeScript**: 5+ with strict mode
- **Build Tool**: Vite for fast development and optimized builds
- **Testing**: Vitest with React Testing Library
- **HTTP Client**: Axios for API communication
- **Styling**: CSS Modules or Tailwind CSS

## Project Setup

### Directory Structure
```
web-ui/src/
├── main.tsx                    # Application entry point
├── App.tsx                     # Root component
├── vite-env.d.ts               # Vite type definitions
│
├── components/                 # React components
│   ├── QueryEditor/            # Feature-based organization
│   │   ├── QueryEditor.tsx     # Component implementation
│   │   ├── QueryEditor.module.css  # Component styles
│   │   ├── QueryEditor.test.tsx    # Component tests
│   │   └── index.ts            # Barrel export
│   ├── SchemaExplorer/
│   └── ResultsTable/
│
├── hooks/                      # Custom React hooks
│   ├── useQuery.ts
│   └── useSchema.ts
│
├── services/                   # API service layer
│   ├── api.ts                  # Axios instance configuration
│   ├── queryService.ts         # Query-related API calls
│   └── schemaService.ts        # Schema-related API calls
│
├── types/                      # TypeScript type definitions
│   ├── query.ts                # Query-related types
│   └── schema.ts               # Schema-related types
│
├── utils/                      # Utility functions
│   ├── formatters.ts
│   └── validators.ts
│
└── styles/                     # Global styles
    ├── globals.css
    └── variables.css
```

## TypeScript Standards

### Strict Mode Configuration
Always use TypeScript strict mode in `tsconfig.json`:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### Type Definitions

**Good**: Explicit, descriptive types
```typescript
// Query types
interface QueryRequest {
    sql: string;
    database: 'oracle' | 'clickhouse' | 'databricks';
    params?: Record<string, unknown>;
    maxRows?: number;
}

interface QueryResult {
    columns: ColumnDefinition[];
    rows: Record<string, unknown>[];
    executionTime: number;
    rowCount: number;
}

interface ColumnDefinition {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'date';
    nullable: boolean;
}
```

**Bad**: Implicit any or loose types
```typescript
// ❌ Avoid implicit any
interface QueryRequest {
    sql: string;
    params: any;  // Don't use 'any'
}

// ❌ Avoid untyped objects
const result = {};  // Type is {}

// ❌ Avoid loose string types when enums are better
interface QueryRequest {
    database: string;  // Use union type instead
}
```

### Interface Naming Conventions
- **Props Interfaces**: Suffix with `Props`
  ```typescript
  interface QueryEditorProps {
      initialQuery?: string;
      onExecute: (query: string) => void;
  }
  ```

- **State Interfaces**: Descriptive names without suffix
  ```typescript
  interface QueryState {
      sql: string;
      isExecuting: boolean;
      result: QueryResult | null;
      error: Error | null;
  }
  ```

- **API Response Types**: Suffix with `Response`
  ```typescript
  interface QueryExecutionResponse {
      success: boolean;
      data: QueryResult;
  }
  ```

## Component Standards

### File Organization
Each component should be in its own directory with:
- `[ComponentName].tsx` - Component implementation
- `[ComponentName].module.css` - Component-specific styles
- `[ComponentName].test.tsx` - Component tests
- `index.ts` - Barrel export

**Example**: `components/QueryEditor/`
```
QueryEditor/
├── QueryEditor.tsx
├── QueryEditor.module.css
├── QueryEditor.test.tsx
└── index.ts
```

### Component Structure

**Good**: Well-structured functional component
```typescript
import React, { useState, useCallback } from 'react';
import styles from './QueryEditor.module.css';

interface QueryEditorProps {
    initialQuery?: string;
    database: 'oracle' | 'clickhouse' | 'databricks';
    onExecute: (query: string) => Promise<void>;
    disabled?: boolean;
}

export const QueryEditor: React.FC<QueryEditorProps> = ({
    initialQuery = '',
    database,
    onExecute,
    disabled = false,
}) => {
    const [query, setQuery] = useState<string>(initialQuery);
    const [isExecuting, setIsExecuting] = useState<boolean>(false);

    const handleExecute = useCallback(async () => {
        if (!query.trim() || disabled) return;

        setIsExecuting(true);
        try {
            await onExecute(query);
        } catch (error) {
            console.error('Query execution failed:', error);
        } finally {
            setIsExecuting(false);
        }
    }, [query, onExecute, disabled]);

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.dbLabel}>Database: {database}</span>
            </div>
            <textarea
                className={styles.editor}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your SQL query..."
                disabled={disabled || isExecuting}
            />
            <button
                className={styles.executeButton}
                onClick={handleExecute}
                disabled={disabled || isExecuting || !query.trim()}
            >
                {isExecuting ? 'Executing...' : 'Execute Query'}
            </button>
        </div>
    );
};
```

**Bad**: Poorly structured component
```typescript
// ❌ No type annotations
export const QueryEditor = (props) => {
    // ❌ No destructuring
    const [query, setQuery] = useState(props.initialQuery);
    
    // ❌ Inline handlers (not memoized)
    return (
        <div>
            <textarea 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
            />
            <button onClick={() => props.onExecute(query)}>Execute</button>
        </div>
    );
};
```

### Naming Conventions
- **Components**: PascalCase - `QueryEditor`, `ResultsTable`
- **Functions**: camelCase - `handleExecute`, `formatResult`
- **Constants**: UPPER_SNAKE_CASE - `MAX_QUERY_LENGTH`, `DEFAULT_TIMEOUT`
- **Props**: camelCase - `onExecute`, `initialQuery`
- **CSS Modules**: camelCase - `styles.container`, `styles.executeButton`

## Custom Hooks

### Hook Structure

**Good**: Well-structured custom hook
```typescript
import { useState, useCallback, useEffect } from 'react';
import { executeQuery } from '../services/queryService';
import type { QueryResult, QueryRequest } from '../types/query';

interface UseQueryReturn {
    result: QueryResult | null;
    isLoading: boolean;
    error: Error | null;
    execute: (request: QueryRequest) => Promise<void>;
    reset: () => void;
}

export const useQuery = (): UseQueryReturn => {
    const [result, setResult] = useState<QueryResult | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);

    const execute = useCallback(async (request: QueryRequest) => {
        setIsLoading(true);
        setError(null);
        
        try {
            const response = await executeQuery(request);
            setResult(response);
        } catch (err) {
            const error = err instanceof Error ? err : new Error('Query execution failed');
            setError(error);
            setResult(null);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const reset = useCallback(() => {
        setResult(null);
        setError(null);
        setIsLoading(false);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            setResult(null);
            setError(null);
        };
    }, []);

    return { result, isLoading, error, execute, reset };
};
```

### Return Type Definitions
Always define explicit return types for hooks:

```typescript
// ✅ Good: Explicit return type
export const useSchema = (): UseSchemaReturn => {
    // ...
};

// ❌ Bad: Implicit return type
export const useSchema = () => {
    // ...
};
```

### useState and useCallback Best Practices
```typescript
// ✅ Good: Explicit types, memoized callbacks
const [count, setCount] = useState<number>(0);
const increment = useCallback(() => setCount((prev) => prev + 1), []);

// ❌ Bad: Implicit types, non-memoized callbacks
const [count, setCount] = useState(0);
const increment = () => setCount(count + 1);  // Creates new function on every render
```

## API Services

### Service Layer Pattern

**File**: `services/api.ts`
```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const api: AxiosInstance = axios.create({
    baseURL: BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            // Handle unauthorized
            console.error('Unauthorized - redirecting to login');
        } else if (error.response?.status >= 500) {
            // Handle server errors
            console.error('Server error:', error.message);
        }
        return Promise.reject(error);
    }
);
```

### Type-Safe Service Functions

**File**: `services/queryService.ts`
```typescript
import { api } from './api';
import type { QueryRequest, QueryResult, QueryHistory } from '../types/query';

export const executeQuery = async (request: QueryRequest): Promise<QueryResult> => {
    const response = await api.post<QueryResult>('/queries/execute', request);
    return response.data;
};

export const getQueryHistory = async (limit: number = 10): Promise<QueryHistory[]> => {
    const response = await api.get<QueryHistory[]>('/queries/history', {
        params: { limit },
    });
    return response.data;
};

export const saveQuery = async (query: string, name: string): Promise<void> => {
    await api.post('/queries/save', { query, name });
};
```

**File**: `services/schemaService.ts`
```typescript
import { api } from './api';
import type { Schema, Table, Column } from '../types/schema';

export const getSchemas = async (database: string): Promise<Schema[]> => {
    const response = await api.get<Schema[]>(`/schemas/${database}`);
    return response.data;
};

export const getTables = async (database: string, schema: string): Promise<Table[]> => {
    const response = await api.get<Table[]>(`/schemas/${database}/${schema}/tables`);
    return response.data;
};

export const getColumns = async (
    database: string,
    schema: string,
    table: string
): Promise<Column[]> => {
    const response = await api.get<Column[]>(
        `/schemas/${database}/${schema}/tables/${table}/columns`
    );
    return response.data;
};
```

## Testing Standards

### Component Testing with React Testing Library

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryEditor } from './QueryEditor';

describe('QueryEditor', () => {
    it('renders with initial query', () => {
        const initialQuery = 'SELECT * FROM users';
        render(
            <QueryEditor
                initialQuery={initialQuery}
                database="oracle"
                onExecute={vi.fn()}
            />
        );
        
        const textarea = screen.getByPlaceholderText(/enter your sql query/i);
        expect(textarea).toHaveValue(initialQuery);
    });

    it('calls onExecute with query when button clicked', async () => {
        const mockExecute = vi.fn().mockResolvedValue(undefined);
        const query = 'SELECT * FROM products';
        
        render(
            <QueryEditor
                database="clickhouse"
                onExecute={mockExecute}
            />
        );
        
        const textarea = screen.getByPlaceholderText(/enter your sql query/i);
        const button = screen.getByRole('button', { name: /execute query/i });
        
        fireEvent.change(textarea, { target: { value: query } });
        fireEvent.click(button);
        
        await waitFor(() => {
            expect(mockExecute).toHaveBeenCalledWith(query);
        });
    });

    it('disables button when query is empty', () => {
        render(
            <QueryEditor
                database="oracle"
                onExecute={vi.fn()}
            />
        );
        
        const button = screen.getByRole('button', { name: /execute query/i });
        expect(button).toBeDisabled();
    });

    it('shows loading state during execution', async () => {
        const slowExecute = vi.fn(() => new Promise((resolve) => setTimeout(resolve, 100)));
        
        render(
            <QueryEditor
                initialQuery="SELECT 1"
                database="oracle"
                onExecute={slowExecute}
            />
        );
        
        const button = screen.getByRole('button', { name: /execute query/i });
        fireEvent.click(button);
        
        expect(screen.getByRole('button', { name: /executing/i })).toBeInTheDocument();
        
        await waitFor(() => {
            expect(screen.getByRole('button', { name: /execute query/i })).toBeInTheDocument();
        });
    });
});
```

### Hook Testing

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useQuery } from './useQuery';
import * as queryService from '../services/queryService';

vi.mock('../services/queryService');

describe('useQuery', () => {
    it('executes query successfully', async () => {
        const mockResult = {
            columns: [{ name: 'id', type: 'number', nullable: false }],
            rows: [{ id: 1 }],
            executionTime: 123,
            rowCount: 1,
        };

        vi.mocked(queryService.executeQuery).mockResolvedValue(mockResult);

        const { result } = renderHook(() => useQuery());

        await result.current.execute({
            sql: 'SELECT * FROM users',
            database: 'oracle',
        });

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
            expect(result.current.result).toEqual(mockResult);
            expect(result.current.error).toBeNull();
        });
    });

    it('handles query execution errors', async () => {
        const mockError = new Error('Query failed');
        vi.mocked(queryService.executeQuery).mockRejectedValue(mockError);

        const { result } = renderHook(() => useQuery());

        await result.current.execute({
            sql: 'INVALID SQL',
            database: 'oracle',
        });

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
            expect(result.current.result).toBeNull();
            expect(result.current.error).toEqual(mockError);
        });
    });
});
```

## Code Quality Tools

### ESLint Configuration
```javascript
// .eslintrc.cjs
module.exports = {
    root: true,
    env: { browser: true, es2020: true },
    extends: [
        'eslint:recommended',
        'plugin:@typescript-eslint/recommended',
        'plugin:react/recommended',
        'plugin:react/jsx-runtime',
        'plugin:react-hooks/recommended',
        'plugin:jsx-a11y/recommended',
    ],
    ignorePatterns: ['dist', '.eslintrc.cjs'],
    parser: '@typescript-eslint/parser',
    plugins: ['react-refresh', '@typescript-eslint', 'react', 'jsx-a11y'],
    rules: {
        'react-refresh/only-export-components': [
            'warn',
            { allowConstantExport: true },
        ],
        '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
        '@typescript-eslint/explicit-function-return-type': 'off',
        '@typescript-eslint/explicit-module-boundary-types': 'off',
        'react/prop-types': 'off', // Using TypeScript for prop validation
    },
};
```

### Prettier Configuration
```json
{
    "semi": true,
    "trailingComma": "es5",
    "singleQuote": true,
    "printWidth": 100,
    "tabWidth": 4,
    "useTabs": false,
    "arrowParens": "always",
    "endOfLine": "lf"
}
```

## Performance Best Practices

### Memoization
Use `React.memo`, `useMemo`, and `useCallback` to optimize renders:

```typescript
// Memoize expensive components
export const ResultsTable = React.memo<ResultsTableProps>(({ data, columns }) => {
    // Component logic
});

// Memoize expensive computations
const sortedData = useMemo(() => {
    return data.sort((a, b) => a.id - b.id);
}, [data]);

// Memoize callbacks passed to child components
const handleRowClick = useCallback((rowId: string) => {
    console.log('Row clicked:', rowId);
}, []);
```

### Code Splitting
Use `React.lazy` for route-based code splitting:

```typescript
import { lazy, Suspense } from 'react';

const QueryEditor = lazy(() => import('./components/QueryEditor'));
const SchemaExplorer = lazy(() => import('./components/SchemaExplorer'));

function App() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <QueryEditor />
            <SchemaExplorer />
        </Suspense>
    );
}
```

### Debouncing Expensive Operations
```typescript
import { useState, useEffect } from 'react';

export const useDebounce = <T,>(value: T, delay: number): T => {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
};

// Usage in component
const SearchInput = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const debouncedSearchTerm = useDebounce(searchTerm, 500);

    useEffect(() => {
        if (debouncedSearchTerm) {
            // Perform search with debounced value
            performSearch(debouncedSearchTerm);
        }
    }, [debouncedSearchTerm]);

    return <input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />;
};
```

## Accessibility

### Semantic HTML
Use proper HTML elements:
```typescript
// ✅ Good: Semantic HTML
<nav>
    <ul>
        <li><a href="/queries">Queries</a></li>
        <li><a href="/schemas">Schemas</a></li>
    </ul>
</nav>

<main>
    <h1>Database Explorer</h1>
    <section>
        <h2>Query Results</h2>
        <table>...</table>
    </section>
</main>

// ❌ Bad: Div soup
<div>
    <div>
        <div>Queries</div>
        <div>Schemas</div>
    </div>
</div>
```

### ARIA Labels
Provide descriptive labels for screen readers:
```typescript
<button
    aria-label="Execute SQL query"
    onClick={handleExecute}
>
    Execute
</button>

<input
    type="text"
    aria-label="SQL query input"
    aria-describedby="query-help"
    value={query}
    onChange={handleChange}
/>
<span id="query-help">Enter a valid SQL query</span>
```

### Keyboard Navigation
Ensure all interactive elements are keyboard accessible:
```typescript
<div
    role="button"
    tabIndex={0}
    onClick={handleClick}
    onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            handleClick();
        }
    }}
>
    Click me
</div>
```

### Focus Management
```typescript
import { useRef, useEffect } from 'react';

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, children }) => {
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isOpen && modalRef.current) {
            modalRef.current.focus();
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div
            ref={modalRef}
            role="dialog"
            aria-modal="true"
            tabIndex={-1}
            onKeyDown={(e) => {
                if (e.key === 'Escape') {
                    onClose();
                }
            }}
        >
            {children}
        </div>
    );
};
```

## Summary

Follow these standards to ensure:
- **Type Safety**: Strict TypeScript with explicit types
- **Maintainability**: Consistent structure and naming conventions
- **Performance**: Optimized rendering with memoization and code splitting
- **Accessibility**: WCAG compliant components
- **Testability**: Comprehensive tests with React Testing Library
- **Code Quality**: ESLint, Prettier, and TypeScript checks

For questions or clarifications, refer to the project's contributing guidelines or reach out to the team.
