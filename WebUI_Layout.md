# Web UI Design & Layout Specification

## Product Value Proposition
**"One Search, All Data."**
The DB Explorer allows data analysts to treat multiple, heterogeneous remote databases (Oracle, ClickHouse, Databricks) as a single, unified virtual database. It provides a "Google-like" search experience with a local-first cleaning engine that standardizes data presentation without modifying the source.

---

## 1. Core UI Layers

The interface is divided into three distinct functional layers:

1.  **Global Search Home:** The entry point for fuzzy discovery.
2.  **Results & Selection:** A faceted browser to filter and identify relevant tables/columns.
3.  **Unified Workbench:** A split-pane dashboard for side-by-side comparison with real-time cleaning.

---

## 2. User Journey Scenario

**Scenario:** Analyst Alex needs to find "User Profit" data but doesn't know if it's in the Oracle Finance DB or the ClickHouse Logs DB.

### Step 1: Fuzzy Discovery
-   **Action:** Alex types `profit` into the global omnibox.
-   **System:** Scans local metadata indexes (Schema, Table, Column, Comments) across all connected DBs.
-   **Result:** Returns 15 matches (e.g., `USER_PROFIT_SUMMARY` in Oracle, `est_profit` column in ClickHouse).

### Step 2: Selection & Preview
-   **Action:** Alex clicks "Peek" on the Oracle result.
-   **System:** `DatabasePort` executes a safe, read-only `SELECT * LIMIT 50`.
-   **Result:** A modal shows raw sample data. Alex confirms relevance and clicks "Pin". He does the same for the ClickHouse table.

### Step 3: Unified Analysis
-   **Action:** Alex opens the "Workbench" with the two pinned tables.
-   **System:** Displays tables side-by-side.
-   **Action:** Alex notices date format discrepancies. He toggles "Normalize Dates" in the Cleaning Toolbar.
-   **Result:** The `CleaningEngine` standardizes both views to `YYYY-MM-DD` instantly.

---

## 3. Wireframes & Layouts

### A. Global Search (Landing Page)
**Goal:** Minimalist, focused entry point.

```text
+---------------------------------------------------------------+
|  [Logo] DB Explorer                                [Settings] |
+---------------------------------------------------------------+
|                                                               |
|                                                               |
|          +-----------------------------------------+          |
|          |  🔍  profit                             |          |  <-- Omnibox (Typeahead)
|          +-----------------------------------------+          |
|                                                               |
|      Suggested: "user_id", "revenue_q3", "error_logs"         |  <-- Smart Chips
|                                                               |
|                                                               |
+---------------------------------------------------------------+
|  Connection Status:                                           |
|  [🟢 Oracle: Finance]  [🟢 ClickHouse: Logs]  [ + Add New ]   |
+---------------------------------------------------------------+
```

### B. Search Results (The Grid)
**Goal:** Filter noise and identify targets using "Cards".

```text
+---------------------------------------------------------------+
|  [< Back]  Search: "profit" (Found 15)           [Filter ▼]   |
+---------------------------------------------------------------+
|  [ Facets ]  |  [ Main Content Area: Cards Grid ]             |
|              |                                                |
|  SOURCE      |  +----------------------+ +------------------+ |
|  [x] Oracle  |  | ORACLE > FINANCE     | | CLICKHOUSE > LOG | |
|  [ ] Databricks| | Table: MONTHLY_PROFIT| | Table: web_logs  | |
|              |  |                      | |                  | |
|  MATCH TYPE  |  | Matches: Table Name  | | Matches: Column  | |
|  [x] Table   |  | Found "PROFIT"       | | "est_profit"     | |
|  [x] Column  |  | [ Peek ]   [ Pin + ] | | [ Peek ] [ Pin +]| | <-- Actions
|              |  +----------------------+ +------------------+ |
|              |                                                |
|              |  +----------------------+                      |
|              |  | ...                  |                      |
+--------------+------------------------------------------------+
|  [ Dock Area (Pinned Items: 2) ]                              | <-- Drag & Drop Targets
+---------------------------------------------------------------+
```

### C. Peek Modal (Safe Preview)
**Goal:** Verify data relevance without heavy loading.

```text
+---------------------------------------------------------------+
|  Preview: ORACLE > FINANCE > MONTHLY_PROFIT         [X Close] |
+---------------------------------------------------------------+
|  Columns: id (PK), report_date, gross_profit, net_profit...   |
|                                                               |
|  +---------------------------------------------------------+  |
|  | id | report_date | gross_profit | net_profit | status   |  |
|  |----|-------------|--------------|------------|----------|  |
|  | 1  | 2023-10-01  | 50000.00     | 12000.00   | FINAL    |  |
|  | 2  | 2023-11-01  | 52000.00     | 11500.00   | DRAFT    |  |
|  | 3  | 2023-12-01  | <NULL>       | <NULL>     | PENDING  |  | <-- Raw Data (Uncleaned)
|  +---------------------------------------------------------+  |
|                                                               |
|  [ View Schema Definition ]          [ Pin to Workbench ]     |
+---------------------------------------------------------------+
```

### D. The Workbench (Split-Pane Analysis)
**Goal:** Side-by-side comparison with local cleaning.

```text
+---------------------------------------------------------------+
|  [Home]  Workbench                                [Export ▼]  |
+---------------------------------------------------------------+
|  [ Toolbar: Cleaning Engine Controls ]                        |
|  [x] Normalize Dates   [x] Hide Nulls   [ ] Trim Spaces       | <-- Applies to ALL panes
+---------------------------------------------------------------+
|             |                                   |             |
|  PANE 1     |                                   |  PANE 2     |
|  Oracle     |                                   |  ClickHouse |
|  (Finance)  |                                   |  (Logs)     |
|             |                                   |             |
|  +-------+  |                                   |  +-------+  |
|  | Date  |  |                                   |  | Date  |  |
|  |-------|  |                                   |  |-------|  |
|  | Oct 1 |  |                                   |  | Oct 1 |  | <-- Visually Aligned
|  +-------+  |                                   |  +-------+  |
|             |                                   |             |
+---------------------------------------------------------------+
```

---

## 4. Architectural Requirements

To support this UI, the backend must implement:

1.  **Metadata Indexer:** A background job that periodically fetches Schema/Table/Column names from all connected DBs to power the **Global Search** (Omnibox) with millisecond latency.
2.  **Sampling Service:** A dedicated `DatabasePort` method (`fetch_sample(limit=50)`) that guarantees **Read-Only** execution for the **Peek Modal**.
3.  **Cleaning Engine:** The runtime processor that accepts raw data + `CleaningConfig` (from the Workbench Toolbar) and returns standardized JSON for the **Workbench**.
