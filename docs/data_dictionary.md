# Data Dictionary

**Source:** CMS Medicare Part D Prescribers, from data.cms.gov
**Datasets:** (1) Prescribers by Provider and Drug, (2) Prescribers by Provider
**Years used:** 2021, 2022, 2023, 2024
**Coverage:** Medicare Part D beneficiaries only, not the full US market
**Scope of our extract:** SGLT2 inhibitors only (drug-level rows where the generic name contains "gliflozin"), plus the by-Provider rows for prescribers who appear in that drug-level data

---

## Table 1: Prescribers by Provider and Drug
**File:** `data/raw/sglt2_by_provider_and_drug_2021_2024.parquet`
**Grain:** one row per prescriber (NPI) per drug (brand + generic) per year
**Rows:** about 969,000 across four years

| Column | Meaning | How we use it |
|---|---|---|
| Prscrbr_NPI | Prescriber's National Provider Identifier | Join key between tables |
| Prscrbr_Last_Org_Name, Prscrbr_First_Name | Prescriber name | Dropped early (privacy) |
| Prscrbr_City | City | Not used |
| Prscrbr_State_Abrvtn, Prscrbr_State_FIPS | State (abbreviation and FIPS code) | Territory and geography |
| Prscrbr_Type | Prescriber specialty (e.g. Endocrinology) | Specialty features and segments |
| Prscrbr_Type_Src | Where the specialty value comes from (e.g. claim specialty) (verify) | Reference only |
| Brnd_Name | Brand name of the drug | Maps to focus brand vs competitors |
| Gnrc_Name | Generic name of the drug | Maps to drug family |
| Tot_Clms | Number of Part D claims, including refills | Main volume measure and basis of the target |
| Tot_30day_Fills | Standardized 30-day fills, including refills | Volume cross-check |
| Tot_Day_Suply | Total days of supply | Not used initially |
| Tot_Drug_Cst | Total drug cost, including amounts paid by the plan, the beneficiary, subsidies and other payers | Cost features |
| Tot_Benes | Number of beneficiaries; may be blank if suppressed | Patient-count feature |
| GE65_* columns | Same measures restricted to beneficiaries aged 65 and over | Not used initially |
| GE65_Sprsn_Flag, GE65_Bene_Sprsn_Flag | Flags explaining why a value is blank (suppressed) | Quality checks |
| Year | Reporting year | **Added by our extract script, not by CMS** |

**Important rules**
- Rows with fewer than 11 total claims for a drug are excluded from the file entirely, so a prescriber with a handful of claims for a drug will not appear for it.
- A blank number means "suppressed for privacy", not zero.
- All columns were saved as text during extraction. Numeric columns are converted during cleaning.

---

## Table 2: Prescribers by Provider
**File:** `data/raw/partd_by_provider_sglt2_prescribers_2021_2024.parquet`
**Grain:** one row per prescriber per year (all drugs combined)
**Scope:** only prescribers who appear in Table 1 in at least one year

### Columns we plan to use
| Column | Meaning | Use |
|---|---|---|
| Prscrbr_NPI | Prescriber NPI | Join key |
| Prscrbr_Ent_Cd | Whether the prescriber is an individual or an organization (verify codes) | Keep individuals only |
| Prscrbr_Cntry | Country | Keep US rows only |
| Prscrbr_State_Abrvtn | State | Territory |
| Prscrbr_Zip5 | 5-digit ZIP code | Territory grouping |
| Prscrbr_RUCA, Prscrbr_RUCA_Desc | Rural-urban classification of the practice location | Rural vs urban feature |
| Prscrbr_Type | Specialty | Specialty grouping |
| Tot_Clms | Total Part D claims across all drugs | Overall prescribing volume |
| Tot_Drug_Cst | Total drug cost across all drugs | Cost feature |
| Tot_Benes | Total beneficiaries | Panel size feature |
| Brnd_Tot_Clms, Gnrc_Tot_Clms | Claims split by brand vs generic | Brand-leaning prescribing feature |
| Bene_Avg_Age | Average age of the prescriber's beneficiaries | Patient mix |
| Bene_Avg_Risk_Scre | Average beneficiary risk score (higher means sicker patients) (verify) | Patient mix |
| Bene_Dual_Cnt, Bene_Ndual_Cnt | Beneficiaries eligible for both Medicare and Medicaid vs not | Patient mix |
| LIS_Tot_Clms, NonLIS_Tot_Clms | Claims for low-income-subsidy vs other beneficiaries | Patient mix |
| MAPD_Tot_Clms, PDP_Tot_Clms | Claims under Medicare Advantage drug plans vs standalone drug plans (verify) | Plan mix |
| Year | Reporting year | **Added by our extract script** |

### Columns we will not use
- **Race columns (`Bene_Race_*`):** excluded on purpose. Choosing which doctors to target based on the racial makeup of their patients could create biased targeting.
- **Opioid, antibiotic and antipsychotic columns:** describe unrelated drug classes.
- **Name and street address columns:** dropped early for privacy. Outputs show NPI, specialty and state only.

---

## Provisional modelling decisions (to be confirmed on Day 4)
- **Drug family** = first word of the generic name (empagliflozin, dapagliflozin, canagliflozin, ertugliflozin).
- **Combination products** (e.g. Synjardy, Invokamet) are included in their family.
- **Sotagliflozin (Inpefa)** is excluded: marketed for heart failure and only about 160 rows.
- **Focus brand** = canagliflozin (Invokana, Invokamet, Invokamet XR); other families are competitors.
- Keep individual US prescribers only.

---

## Known limitations
1. **Medicare Part D only.** Younger and commercially insured patients are not represented, so this is not the full market.
2. **Small counts are dropped.** Drug-level rows under 11 claims are missing, so focus-brand share is under-counted for light prescribers.
3. **Selection effect.** Our extract contains only prescribers who appear in the SGLT2 data. Prescribers who never prescribed the class, or prescribed it below the threshold, are not in our data. The model describes existing SGLT2 prescribers, not all doctors.
4. **No call activity data.** We cannot see which doctors were visited, so we estimate potential, not the causal effect of a sales call.
5. **Rapid class growth.** The class more than doubled in prescribers between 2021 and 2024, so volume trends upward for almost everyone. Evaluate the model mainly on ranking.
6. **Claims are not patients.** Refills and new starts are not distinguished.
7. **Class use extends beyond diabetes.** SGLT2 drugs are also used in heart failure and kidney disease, so specialties such as cardiology and nephrology appear.