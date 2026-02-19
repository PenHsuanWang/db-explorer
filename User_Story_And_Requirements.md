# User Story & Product Requirements

## 1. Product Vision: "One Search, All Data"

**DB Explorer** transforms the fragmented experience of managing multiple database clients into a single, unified "Search Engine" for enterprise data. 
Instead of remembering connection strings and SQL syntax for different systems (Oracle, ClickHouse, Databricks), analysts use a Google-like interface to find, preview, and compare data across the entire organization—without ever writing a line of SQL or worrying about breaking the database.

---

## 2. Core UI/UX Design

The application is structured into three distinct, progressive layers designed to guide the user from "Vague Idea" to "Concrete Insight".

### A. The Entry Layer: Global Search Home (Discovery)

**Visual Metaphor:** Google Homepage / Spotlight Search.
**Goal:** Instant access to any data asset with zero friction.

*   **Visual Focus:**
    *   A large, centered **Omnibox** (Universal Search Bar) dominates the screen.
    *   Minimalist design to reduce cognitive load.
*   **Search Capabilities (Fuzzy Search):**
    *   **Scope:** Simultaneously scans metadata across ALL connected databases.
    *   **Targets:** 
        *   `Schema Name` (e.g., "FINANCE_PROD")
        *   `Table Name` (e.g., "MONTHLY_PROFIT_SUMMARY")
        *   `Column Name` (e.g., "net_profit_margin")
        *   `Comments/Descriptions` (e.g., "Tracks Q3 revenue adjustments")
    *   **Input Examples:** `profit`, `user_id`, `Q3_report`, `error_log`.
*   **Advanced Features:**
    *   **"Deep Search" Toggle:** An optional switch to search within *data values* (e.g., finding a specific transaction ID "TX-9988"). 
        *   *UX Requirement:* Must display a warning about performance impact ("This may take longer as it scans actual data").

### B. The Results Layer: Search Results & Facets (Selection)

**Visual Metaphor:** E-commerce Search (Amazon/Airbnb) or Code Search (GitHub).
**Goal:** Rapidly filter noise to identify the correct data source.

*   **Left Sidebar (Facets / Filtering):**
    *   **Source:** Checkboxes to toggle specific databases (e.g., `[x] Oracle (Finance)`, `[ ] Databricks (Archive)`).
    *   **Match Type:** Filter by where the keyword was found (e.g., `[x] Table Name`, `[x] Column Name`, `[ ] Data Value`).
*   **Main Content Area (Cards View):**
    *   Results are displayed as rich **"Data Cards"** rather than a boring list.
*   **Card Anatomy:**
    *   **Header:** `MONTHLY_PROFIT` (Table Name) with an icon indicating the DB type (Oracle/ClickHouse).
    *   **Breadcrumb:** `Oracle (Production) > FINANCE_SCHEMA > MONTHLY_PROFIT` (Full path).
    *   **Highlighting:**
        *   Contextual snippets explaining the match: *"Found 'profit' in table name"* or *"Column `gross_profit` matches search."*
    *   **Quick Preview (Metadata):**
        *   Displays the first 3 columns and their types (e.g., `id (INT)`, `date (DATE)`, `amt (DECIMAL)`) to give immediate context.
    *   **Primary Action (Call to Action):**
        *   **"Pin to Workbench"**: A prominent button (or drag handle) to add this table to the analysis workspace.
        *   **"Peek"**: A secondary button to open a safe, read-only modal with 5 rows of sample data.

### C. The Workspace Layer: Unified Workbench (Analysis)

**Visual Metaphor:** Financial Terminal (Bloomberg) or IDE Split-Pane.
**Goal:** Side-by-side comparison and standardization of heterogeneous data.

*   **Layout:**
    *   **Flexible Grid / Split Pane:** Users can arrange pinned tables side-by-side (Left/Right) or stacked (Top/Bottom).
    *   **Drag & Drop:** Reorder panes easily.
*   **The "Cleaning Engine" Value Proposition:**
    *   **Scenario:** 
        *   **Pane 1 (Left):** Oracle Table `MONTHLY_PROFIT`.
        *   **Pane 2 (Right):** ClickHouse Table `realtime_revenue_log`.
    *   **Visual Unification (The "Magic"):**
        *   Despite coming from different systems with different underlying types, the data LOOKS identical.
        *   **Dates:** Both displayed as `YYYY-MM-DD` (ISO-8601).
        *   **Nulls:** Both displayed as a consistent, greyed-out `<NULL>` placeholder.
        *   **Numbers:** Currency/Amounts standardized to 2 decimal places.
    *   **User Benefit:** The analyst can visually compare row 1 from Oracle with row 1 from ClickHouse without mentally converting formats.

---

## 3. User Journey Scenario

**Scenario:** Analyst Alex needs to find all company data regarding "User Profit" but doesn't know if it's scattered in the Oracle Finance DB or the ClickHouse Activity Logs DB.

### Step 1: Fuzzy Discovery (The Discovery)
1.  Alex opens **DB Explorer**.
2.  He types `profit` into the central search box.
3.  The system instantly returns 15 results.
    *   He sees an Oracle table named `USER_PROFIT_SUMMARY` (Table Name match).
    *   He sees a ClickHouse table named `web_logs` which contains a column named `est_profit` (Column Name match).

### Step 2: Filter & Lock (The Selection)
1.  Alex feels these two are the most relevant. He clicks the **"Peek"** button on the Oracle card.
2.  A modal pops up displaying the first 5 rows of sample data from that table.
    *   *System Action:* The `CleaningEngine` works in the background to ensure data is readable and free of garbled text.
3.  Alex confirms this is what he needs and clicks **"Pin"**. The card flies into the "Dock" at the bottom of the screen.
4.  He performs the same action for the ClickHouse table.

### Step 3: Compare & Analyze (The Analysis)
1.  Alex clicks **"Open Workbench"**.
2.  The screen transitions to a split-pane view (Left/Right).
    *   **Left:** Oracle's `USER_PROFIT_SUMMARY`.
    *   **Right:** ClickHouse's `web_logs`.
3.  **Key Pain Point Resolved:** He notices that Oracle's `user_id` is a string `"U-1001"`, while ClickHouse's is a number `1001`.
4.  He opens the **"Cleaning Rules"** panel at the top.
5.  He sets a rule: `Format: Normalize User ID`.
6.  The `CleaningEngine` instantly unifies the display format of both datasets in the frontend.
7.  Alex can now easily visually compare the data from both sides for consistency without writing any SQL conversion functions.

---

## 4. Architectural Implications

To support this UX, the backend architecture requires two specific designs:

### A. Metadata Indexer
*   **Problem:** Scanning the entire database schema on every search is too slow.
*   **Solution:** A background job that periodically crawls and fetches the Table/Column List from all connected DBs and builds a lightweight local index (e.g., using SQLite or Lucene/Whoosh).
*   **Benefit:** This enables "Global Search" to achieve millisecond-level response times.

### B. Sampling Service
*   **Problem:** Fetching full tables for preview is dangerous and slow.
*   **Solution:** When a user clicks "Peek" or "Pin", the backend `DatabasePort` strictly executes `SELECT * FROM table LIMIT 50`.
*   **Benefit:** This ensures **"Read-Only"** safety and **"High Performance"**, preventing users from accidentally locking the database by querying massive tables.

**Impact:** These designs elevate the product from a simple "DB Client" to a "Data Discovery Platform", truly solving the analyst's two biggest headaches: *"Where is the data?"* and *"Are these two datasets the same?"*.