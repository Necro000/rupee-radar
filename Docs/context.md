# RupeeRadar — Project Context

## Overview

**RupeeRadar** is an AI-powered personal finance assistant built for the AI Challenge. It helps users understand where their money is going by analyzing bank statement data and turning raw transactions into actionable insights.

## Problem

Working professionals often make hundreds of monthly transactions across UPI, cards, bank transfers, subscriptions, EMIs, rent, shopping, food delivery, travel, and investments. Bank statements contain this information, but transaction descriptions are messy, inconsistent, and hard to categorize manually.

## Objective

Build an end-to-end solution that converts raw financial transaction data into meaningful personal finance insights.

The application should help users answer:

- What are my biggest spending categories?
- How much did I spend this month?
- Which transactions are recurring subscriptions or EMIs?
- What was my biggest transaction?
- What are the top insights from my spending behavior?

## Core Requirements

1. **Input** — Accept bank statement data as input.
2. **Extract & clean** — Parse and normalize transactions into a structured format.
3. **Categorize** — Assign transactions to meaningful groups:
   - Food, Travel, Shopping, Bills, EMI, Subscriptions, Salary, Rent, Investments, Other
4. **Recurring detection** — Identify recurring payments such as subscriptions, EMIs, rent, SIPs, or insurance.
5. **Metrics** — Calculate key financial metrics:
   - Total income, total spend, savings
   - Top categories, biggest transactions
6. **Insights** — Generate clear, human-readable spending insights using actual transaction amounts.
7. **Presentation** — Deliver results via a simple UI, dashboard, or downloadable report.

## Expected Output (Prototype)

The working prototype must demonstrate:

- Cleaned transaction data
- Categorized expenses
- Recurring payment detection
- Spend summary dashboard
- At least three personalized financial insights
- A final report or visual summary that can be shared

## Evaluation Criteria

Submissions are judged on:

| Area | Focus |
|------|--------|
| Accuracy | Transaction cleaning and categorization |
| Insights | Quality of financial insights |
| Robustness | Handling real-world messy transaction descriptions |
| UX | Simplicity and usefulness of the user experience |
| Workflow | Completeness of the end-to-end pipeline |
| Privacy | Conscious handling of sensitive financial data |

## Constraints

- Prioritize a **working end-to-end prototype** over perfect support for every bank format.
- Technology stack and implementation approach are **participant's choice**.
- Final deliverable: a **deployed or locally runnable** application that takes raw bank statement data and produces a clear personal finance summary.

## End-to-End Flow

```
Raw bank statement → Upload → Extract/clean → Categorize → Detect recurring
    → Compute metrics → Generate insights → Dashboard / report
```

## Key Categories (Reference)

`Food` · `Travel` · `Shopping` · `Bills` · `EMI` · `Subscriptions` · `Salary` · `Rent` · `Investments` · `Other`

## Recurring Transaction Types (Reference)

Subscriptions · EMIs · Rent · SIPs · Insurance payments
