# StayMetrics 🏨
 
StayMetrics is a hospitality analytics platform built to generate realistic hotel booking datasets and power a set of Power BI dashboards that help make sense of occupancy trends, revenue performance, cancellations, and channel behaviour across a multi-city hotel network.
 
The idea behind it is simple: hotel networks operating across different regions need more than raw numbers. They need context. StayMetrics provides that by simulating a full booking operation, from the first reservation to the final revenue settlement, in a way that mirrors how platforms like OYO, Airbnb, or Booking.com actually work.
 
The platform covers three types of markets across India:
- **Metro cities** (Mumbai, Delhi NCR, Bengaluru): high-volume, consistent demand year-round
- **Tourist destinations** (Jaipur, Goa): strong seasonality with clear peak and off-peak windows
- **Tier-2 cities** (Kochi): emerging markets with steadier, more balanced booking patterns
## What It Does
 
At its core, StayMetrics does two things well. First, it generates synthetic but business-accurate booking data. Think 40,000+ transactions across 25–30 hotels, with realistic pricing, cancellation behaviour, and revenue logic baked in. Second, it structures that data so it flows directly into Power BI, where four dashboard pages turn raw numbers into actionable insights.
 
Some of the specifics worth calling out:
- Weekday vs. weekend demand shifts, monsoon dips, and peak-season spikes are all modelled
- Booking channels (App, Web, Walk-In, OTA) each behave differently in terms of discount rates and cancellation likelihood
- Commission rates vary by partner type, region, and channel, just as they would in a real contract
- The output is four clean CSV files, ready to import into Power BI without any cleaning or transformation
## Repository Structure
 
```
StayMetrics/
├── generate_data.py          # The main script. Run this to produce all four CSVs
├── hotel_master.csv          # Hotel dimension table (25–30 hotels)
├── booking_data.csv          # ~40,000–50,000 booking transactions
├── cancellation_data.csv     # ~5,000–7,000 cancellation records with reasons and refund flags
├── revenue_payments.csv      # Revenue settlement data per booking
├── StayMetrics.pbix          # Pre-built Power BI dashboard
└── HPA_project_detail.md     # Full technical documentation
```
 
 
## How the Data Is Structured
 
The data follows a star schema: one dimension table (hotels) and three fact tables (bookings, cancellations, revenue). This structure was chosen specifically because it maps cleanly to Power BI's data model and makes relationship management straightforward.
 
```
Data Generation (generate_data.py)
        │
        ▼
Structured CSV Exports
  ├── hotel_master.csv
  ├── booking_data.csv
  ├── cancellation_data.csv
  └── revenue_payments.csv
        │
        ▼
Power BI Data Model (Star Schema)
  ├── Fact Tables + Dimensions
  ├── DAX Measures (KPIs)
  └── Table Relationships
        │
        ▼
Analytical Dashboards (4 Pages)
  ├── Executive Overview
  ├── Regional Analytics
  ├── Partner Performance
  └── Booking & Channel Analysis
```
 
The relationships between tables look like this:
 
```
hotel_master (1) ──── (M) booking_data
hotel_master (1) ──── (M) revenue_payments
booking_data (1) ──── (M) cancellation_data
booking_data (1) ──── (1) revenue_payments
```
 
 
## Dataset at a Glance
 
| Table | Rows | What It Contains |
|---|---|---|
| `hotel_master` | 25–30 | Hotel metadata: city, property type, partner type, room capacity |
| `booking_data` | ~40,000–50,000 | Daily bookings with pricing, channel, and status |
| `cancellation_data` | ~5,000–7,000 | Cancellation reasons and refund eligibility |
| `revenue_payments` | ~40,000–50,000 | Commission rates and partner/platform revenue splits |
 
The main fact table, `booking_data`, includes these columns:
 
| Column | Type | Description |
|---|---|---|
| `booking_id` | Int | Unique booking identifier |
| `booking_date` | Date | When the booking was made |
| `checkin_date` / `checkout_date` | Date | The guest's stay window |
| `hotel_id` | Int | Links to `hotel_master` |
| `room_nights_booked` | Int | Rooms × length of stay |
| `booking_status` | String | Completed / Cancelled / No-Show |
| `booking_channel` | String | App / Web / Walk-In / OTA Partner |
| `base_price` | Float | Pre-discount nightly rate (₹) |
| `discount_amount` | Float | Discount applied (₹) |
| `final_price_paid` | Float | Actual revenue received (₹) |
 
 
## The Business Logic
 
### Demand Modelling
 
Room bookings are drawn from a Poisson distribution, which naturally reflects the randomness of independent customer arrivals. The demand parameter (λ) is built up from several multipliers:
 
```
λ = total_rooms × 0.55 × weekend_multiplier × season_multiplier × property_multiplier
```
 
| Factor | Range | What It Captures |
|---|---|---|
| Base demand | 0.55 | ~55% average occupancy as a starting point |
| Weekend multiplier | 1.0 / 1.18 | Demand rises ~18% on Fridays through Sundays |
| Season multiplier | 0.82 – 1.25 | Peak winter tourism (+25%) and monsoon slowdown (−18%) |
| Property multiplier | 0.70 – 1.40 | Budget hotels fill faster; Premium properties are more selective |
 
### Pricing
 
Every booking has a base rate sampled from region and property type distributions, then a channel-specific discount is applied:
 
```
final_price = max(base_price − discount, 0.60 × base_price)
```
 
| Channel | Discount Range | Why |
|---|---|---|
| App / Web | 8–18% | Price-sensitive, digital-first customers |
| OTA Partner | 5–20% | Promotional periods vary; platform overhead |
| Walk-In | 0–8% | Last-minute bookings, minimal negotiation |
 
A price floor at 60% of base rate prevents the model from generating economically unrealistic transactions.
 
### Commission Rates
 
Commission isn't flat. It adjusts based on the partner relationship, geography, and booking channel:
 
```
rate = clamp(0.18 + Δ_partner + Δ_region + Δ_channel, 0.10, 0.27)
```
 
| Adjustment | Value | Rationale |
|---|---|---|
| Franchise partner | −3% | Established partners have more bargaining power |
| Affiliate partner | +4% | Newer partners require more platform investment |
| Metro region | −1% | Volume discount in high-density markets |
| OTA channel | +3% | Higher service cost for third-party distribution |
 
 
## Key Metrics and What to Expect
 
| KPI | DAX Formula Sketch |
|---|---|
| **Occupancy Rate** | `SUM(room_nights_booked) / (SUM(total_rooms) × DISTINCTCOUNT(checkin_date))` |
| **ADR** | `SUM(final_price_paid) / SUM(room_nights_booked)` |
| **RevPAR** | `ADR × Occupancy Rate` |
| **Cancellation Rate** | `COUNTROWS(Cancelled) / COUNTROWS(booking_data)` |
| **Platform Revenue** | `SUM(revenue_share_platform)` |
 
When you load the data into Power BI, here's roughly what you should see:
 
| Metric | Expected Range |
|---|---|
| Total Bookings | ~47,500 |
| Cancellation Rate | 14–18% |
| Average Occupancy | 45–65% |
| ADR | ₹1,200 – ₹6,500 |
| RevPAR | ~₹738 |
| Total Gross Revenue | ₹60M–₹70M across 9 months |
 
 
## The Dashboard
 
The Power BI file (`StayMetrics.pbix`) has four report pages, each aimed at a different audience and decision type.
 
**Page 1: Executive KPI Overview**
The at-a-glance page. KPI cards for Revenue, Occupancy, ADR, RevPAR, and Cancellation Rate sit alongside a monthly revenue trend line and hotel leaderboards showing the best and worst performers.
 
**Page 2: Regional Analytics**
A deeper look at how cities and regions compare. Includes an occupancy heatmap by city and month, revenue contribution breakdowns, and a seasonality matrix that makes Goa's monsoon dip very visible.
 
**Page 3: Partner Performance**
Hotels ranked by RevPAR, with comparisons across Franchise, Managed, and Affiliate partner types. An ADR vs. Occupancy scatter plot helps identify which properties are pricing well and which are leaving money on the table.
 
**Page 4: Booking & Channel Analysis**
Where the booking behaviour lives. Channel split, cancellation rate by channel, discount vs. conversion patterns, and a refund liability card that tracks the financial exposure from cancellations.
 
 
## Getting Started
 
### What You'll Need
 
- Python 3.8 or higher
- Power BI Desktop (latest version)
### Setup
 
```bash
# Clone the repository
git clone https://github.com/MercuryConnor/StayMetrics.git
cd StayMetrics
 
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
 
# Install dependencies
pip install numpy pandas
```
 
### Generate the Data
 
```bash
python generate_data.py
```
 
This produces all four CSV files in the project folder. It takes about 10–20 seconds on typical hardware.
 
### Load into Power BI
 
1. Open Power BI Desktop and go to **Home → Get Data → Text/CSV**
2. Import all four CSV files one by one
3. In **Model View**, set up these relationships:
   - `hotel_master.hotel_id → booking_data.hotel_id` (1:M)
   - `hotel_master.hotel_id → revenue_payments.hotel_id` (1:M)
   - `booking_data.booking_id → cancellation_data.booking_id` (1:M)
   - `booking_data.booking_id → revenue_payments.booking_id` (1:1)
4. Create a Date table and link it to `booking_data[booking_date]`
5. Open `StayMetrics.pbix` to explore the pre-built dashboard
### Want Different Data?
 
The script uses a fixed random seed (42) for reproducibility. To generate a fresh dataset, edit line 4 of `generate_data.py`:
 
```python
rng = np.random.default_rng(123)  # swap 42 for any number
```
 
Then re-run the script. The business logic stays the same; only the specific values change.
 
 
## Tech Stack
 
| Tool | Role |
|---|---|
| Python 3.12 | Core data generation |
| NumPy | Poisson and uniform random sampling |
| Pandas | DataFrame operations and CSV export |
| Power BI Desktop | Dashboards, DAX measures, data modelling |
| CSV | Lightweight, universally compatible data format |
 
 
## Known Limitations
 
A few things this version doesn't cover that a real system would:
 
- No real-time or streaming data; everything is generated statically
- No guest profiles, loyalty tiers, or repeat-customer tracking
- Bookings are tracked at the booking level, not individual room level
- Seasonality is month-based, not tied to actual festival or holiday calendars
- No competitor pricing signals or external demand factors
## What's Next
 
- [ ] Guest dimension table with demographics and loyalty tiers
- [ ] Room-type-level inventory (Standard, Deluxe, Suite breakdowns)
- [ ] Demand-responsive dynamic pricing
- [ ] Parquet export for better performance at scale
- [ ] Automated data quality checks with Great Expectations
- [ ] Script to auto-generate the Power BI file with pre-built measures
*Status: Production-Ready | Started: February 2026*
 
