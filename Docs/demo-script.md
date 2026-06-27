# RupeeRadar — Prototype Evaluation Demo Script

This script provides step-by-step guidance for judges or evaluators to test and review the **RupeeRadar** personal finance prototype.

---

## Step 1: Launch the Services

Verify the project is up and running:

### Option A: Using Docker Compose (Recommended)
```bash
# Build and run containerized services
docker compose build
docker compose up -d
```
- Open the Web App: `http://localhost:3000`
- Open the API Health endpoint: `http://localhost:8000/health`
- Open the Backend Swagger API: `http://localhost:8000/docs`

### Option B: Running Locally for Development
1. **FastAPI Backend**:
   ```bash
   cd apps/api
   # Activate your virtual environment and run:
   uvicorn main:app --reload --port 8000
   ```
2. **Next.js Frontend**:
   ```bash
   cd apps/web
   # Run the development server:
   npm run dev
   ```

---

## Step 2: Initialize Session & Upload Bank Statement

1. Navigate to the client dashboard in your browser: `http://localhost:3000`.
2. Look at the **API Online** badge in the header confirming connectivity.
3. Locate the **DropZone** upload container in the center.
4. Drag and drop the sample statement file from the repository: `d:\Ai notes\Rupee-Radar\data\sample.csv` (or use the browse link to select it).
5. Click the **Analyze Statement** button.
6. Observe the progress loader indicating:
   - Creating session
   - Uploading statement
   - Classifying categories & tracking EMIs
   - Completing analysis
7. Once finished, you will be redirected to the live dashboard page at `/dashboard/[sessionId]`.

---

## Step 3: Explore the Financial Summary (Overview)

1. Review the 5 KPI summary cards at the top of the **Overview** tab:
   - **Total Income**: Sum of all salary or positive credit transactions (e.g. ₹1,00,000+).
   - **Total Spend**: Total outflow expenses.
   - **Net Savings**: Net savings amount.
   - **Savings Rate**: Percentage of income saved.
   - **Recurring Total**: Sum of monthly equivalents for subscriptions and EMIs.
2. Inspect the **Largest Single Expense** card indicating the highest debit amount, date, description, and category.
3. Review the top 2 behavioral insights cards rendered at the bottom of the overview.

---

## Step 4: Inspect Category Charts (Categories)

1. Click the **Categories** tab in the sidebar navigation.
2. Inspect the spend distribution:
   - **Donut Chart**: Hover over sections to see the category names and exact ₹ spends. The central label displays total spend.
   - **Bar Chart**: Switch views using the toggle controls to compare expenses side-by-side.
   - **Grid View**: Switch to grid view to inspect custom categories progress bars and exact percentages.

---

## Step 5: Auditing & Correcting Records (Transactions)

1. Click the **Transactions** tab in the sidebar navigation.
2. Search for specific records:
   - Type `Swiggy` or `Rent` in the search bar and click **Apply** to filter transactions instantly.
   - Use the **All Categories** dropdown to view only `Shopping` or `Subscriptions` records.
3. Perform a **Category Correction Override**:
   - Locate an "Other" or incorrectly categorized transaction.
   - Click the dropdown in the **Correct Category** column.
   - Select a new category (e.g., change `Other` to `Food` or `Travel`).
   - Observe the confirmation toast at the top indicating a new rule has been learned and applied to all matching description rows.
   - Verify that the card stats refresh dynamically.

---

## Step 6: Inspect Recurring Payment commitments (Recurring)

1. Click the **Recurring** tab in the sidebar navigation.
2. Review the list of detected commitments grouped by frequency (weekly, monthly, quarterly) and type (subscriptions, EMIs, rent, SIPs, insurance).
3. Click any group row (e.g., `Netflix` or `House Rent`) to expand it and review the individual historical payment ledger rows.

---

## Step 7: Evaluate behavioral insights (Insights)

1. Click the **Insights** tab in the sidebar navigation.
2. Inspect the list of 3–5 ranked financial behavioral insights (e.g., Savings rates reviews, top spending details, recurring burden proportions).
3. Critical insights (e.g., negative savings or high fixed expenditures) display red warning layouts and critical urgency labels.

---

## Step 8: Generate and Save PDF Report

1. In the sidebar, select any tab, then click the **Save PDF / Print** equivalent print console or navigate to `/dashboard/[sessionId]/report` in the URL.
2. On the report view, click the **Save PDF / Print** button at the top.
3. Verify that:
   - Page margins are clean.
   - Print controls, return buttons, and sidebars are completely hidden (`print:hidden`).
   - Tables and KPIs fit perfectly on standard A4 paper dimensions.
   - You can export the report directly to a PDF file on your local machine.
4. Click **Back to Dashboard** to return.

---

## Step 9: Delete and Purge Session

1. In the dashboard header, click the **Delete Session** button.
2. Confirm the browser alert warning.
3. You will be redirected back to the upload screen `/`.
4. Try reloading `/dashboard/[sessionId]`; it should return a "Session Error" page confirming the session and all associated files have been permanently deleted.
