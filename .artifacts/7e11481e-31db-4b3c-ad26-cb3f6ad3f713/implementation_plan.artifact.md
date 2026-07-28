# Implementation Plan - Dashboard UI Improvement

The user has requested to improve the Dashboard UI, which currently looks sparse and lacks visual structure. I will redesign the dashboard using premium fintech-style cards, better grouping, and improved layout consistency.

## User Review Required

> [!IMPORTANT]
> I will be replacing the standard `st.metric` calls in the dashboard with custom HTML/CSS cards to achieve a more professional, "premium" look. This provides much more control over typography, spacing, and colors.

## Proposed Changes

### Frontend Improvements

#### [MODIFY] [app.py](file:///Users/midhun/Documents/iitrootkee/ledgerlens/frontend/app.py)
- **Redesign KPI Section**: Group metrics into logical sections (Pipeline Stats and Financial Stats).
- **Custom KPI Cards**: Use the existing `kpi-card` CSS but enhance the layout to be more compact and visually appealing.
- **Refresh Button**: Move the refresh button to be more integrated with the section header or a dedicated utility bar.
- **Improved Grid**: Use a 4-column or 3-column grid for primary metrics and a separate row for secondary metrics to avoid the "jagged" look in the screenshot.
- **Enhanced Charts**: Add some padding and border to the chart containers to match the card aesthetic.

## Verification Plan

### Manual Verification
- View the Dashboard tab in the browser.
- Verify that metrics are clearly readable and well-organized.
- Check that the charts are properly aligned with the metric cards.
- Ensure the Refresh button works as expected.
