# HCP Targeting and Call-Plan Optimization

## Business problem
A pharma commercial team has a fixed number of sales reps, and each rep can
make a limited number of calls. Which doctors should they visit to maximise
prescriptions of the focus brand?

## Scope
- Drug class: SGLT2 inhibitors (type 2 diabetes)
- Focus brand: canagliflozin; competitors: empagliflozin, dapagliflozin, ertugliflozin
- Data: CMS Medicare Part D Prescriber public data (US)

## Approach (planned)
1. Segment prescribers with clustering
2. Predict future prescribing potential with gradient boosting
3. Allocate calls under a capacity constraint with an optimization model

## Success metrics
- Share of high-potential prescribers reached by the plan
- Expected incremental claims versus a "call the biggest prescribers" plan
- Model ranking quality (top-20% of scored prescribers capture X% of future volume)

## Status
Day 1: setup and problem framing complete.