# PRODUCT REQUIREMENT DOCUMENT (PRD) - PROJECT HELIOS REWARDS UPGRADE

## 1. Executive Summary & Goals
Project Helios is the platform upgrade of our legacy Customer Loyalty Rewards engine. The key objective is to transition from batch-processed loyalty calculation pipelines to an instant, transaction-triggered rewards tier engine.

Our goal is to boost customer retention by 15% within the first year of rollout by providing instant customer feedback on purchases.

---

## 2. Functional Requirements & Formulas
Loyalty points must be calculated and assigned instantly when a card transaction triggers the payment gateway API.

### Point Accrual Formulas:
* **Standard Category purchases**: $1 Spent = 1 Loyalty Point.
* **Premium Partner purchases**: $1 Spent = 3 Loyalty Points.
* **Special Promo Window multiplier**: Points = (Amount Spent * Base Rate) * Multiplier.

```
Points_Accrued = floor( Transaction_Amount_USD * Category_Multiplier )
```

### Customer Tiers & Privileges:
* **Bronze Tier**: Under 5,000 points. Standard 24-hour reward redemption.
* **Silver Tier**: 5,000 to 14,999 points. Free shipping perks, 10% coupon incentives.
* **Gold Tier**: 15,000 to 49,999 points. VIP customer desk access, 15% coupon incentives.
* **Platinum Tier**: 50,000+ points. Exclusive partner event invites, priority airport lounges access.

---

## 3. User Stories & Acceptance Criteria

### User Story 1: Real-time Accrual Display
* **As a** registered customer checkout system user,
* **I want** to see my points update within 3 seconds of terminal swipes,
* **So that** I know my loyalty records reflect accurate purchases immediately.

#### Acceptance Criteria:
1. System must trigger points accrual processor within 100ms of `atlas-settlement-worker` success.
2. If network delay occurs, UI displays "Points calculation pending" indicator rather than crash.
3. Points increments must match exact transaction amounts rounded down to the nearest integer.

---

## 4. Integration Specifications & Webhook Schemas
Helios syncs customer updates to Salesforce CRM via outgoing webhooks. The system retries failed updates up to 5 times.

### Outgoing Payload Schema (JSON):
```json
{
  "event_type": "CUSTOMER_TIER_UPGRADE",
  "timestamp": "2026-07-31T12:00:00Z",
  "customer_profile": {
    "account_id": "acc_7812948",
    "first_name": "Marcus",
    "last_name": "Brody",
    "email": "m.brody@enterprise.com"
  },
  "loyalty_summary": {
    "accrued_points": 50120,
    "current_tier": "Platinum",
    "previous_tier": "Gold"
  }
}
```

---

## 5. Technical Architecture Parameters & Indexes
To process high-throughput transaction events, database queries must target optimized table keys.

* **DB Engine**: AWS DynamoDB
* **Partition Key (PK)**: `CUSTOMER#<AccountID>`
* **Sort Key (SK)**: `TRANSACTION#<Timestamp>`
* **Global Secondary Indexes (GSIs)**:
  - `GSI_Email` (PK: Email Address) - used for support desk lookups.
  - `GSI_Tier` (PK: CurrentTier, SK: AccruedPoints) - used for marketing analytics runs.
* **Batch Sync Boundary limit**: Limit batch transaction writes to 25 items per payload.
