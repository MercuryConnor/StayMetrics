import numpy as np
import pandas as pd

# Random generator with fixed seed for reproducibility
rng = np.random.default_rng(42)

# Master data setup
cities = [
    ("Mumbai", "Maharashtra", "Metro"),
    ("Delhi NCR", "Delhi", "Metro"),
    ("Bengaluru", "Karnataka", "Metro"),
    ("Jaipur", "Rajasthan", "Tourist"),
    ("Goa", "Goa", "Tourist"),
    ("Kochi", "Kerala", "Tier-2"),
]
props = [
    ("Budget", (30, 80)),
    ("Business", (60, 150)),
    ("Boutique", (25, 60)),
    ("Premium", (80, 200)),
]
partner_types = ["Franchise", "Managed", "Affiliate"]

hotels = []
hid = 1
for city, state, region in cities:
    # Between 3 and 5 hotels per city -> 25-30 total
    for _ in range(rng.integers(3, 6)):
        ptype, (lo, hi) = props[rng.integers(0, len(props))]
        hotels.append(
            {
                "hotel_id": hid,
                "hotel_name": f"{city.split()[0]} Stay {hid}",
                "city": city,
                "state": state,
                "region_category": region,
                "property_type": ptype,
                "total_rooms": int(rng.integers(lo, hi)),
                "partner_onboarding_date": pd.Timestamp("2023-06-01")
                + pd.Timedelta(days=int(rng.integers(0, 250))),
                "partner_type": partner_types[rng.integers(0, len(partner_types))],
            }
        )
        hid += 1
hotel_master = pd.DataFrame(hotels)

# Date range (6-9 months window)
start, end = pd.Timestamp("2024-06-01"), pd.Timestamp("2025-02-28")
calendar = pd.date_range(start, end, freq="D")


def base_adr(row: pd.Series) -> float:
    region, ptype = row.region_category, row.property_type
    if region == "Metro":
        if ptype == "Premium":
            return rng.uniform(4500, 6500)
        if ptype == "Business":
            return rng.uniform(3000, 4200)
        if ptype == "Boutique":
            return rng.uniform(2800, 4000)
        return rng.uniform(1600, 2400)
    if region == "Tourist":
        if ptype == "Premium":
            return rng.uniform(4000, 6000)
        if ptype == "Business":
            return rng.uniform(2600, 3600)
        if ptype == "Boutique":
            return rng.uniform(2400, 3400)
        return rng.uniform(1400, 2000)
    # Tier-2
    if ptype == "Premium":
        return rng.uniform(3200, 4500)
    if ptype == "Business":
        return rng.uniform(2400, 3200)
    if ptype == "Boutique":
        return rng.uniform(2000, 3000)
    return rng.uniform(1200, 1800)


channels = ["App", "Web", "Walk-In", "OTA Partner"]
booking_rows = []
book_id = 1
for _, h in hotel_master.iterrows():
    for d in calendar:
        dow = d.dayofweek
        weekend_mult = 1.18 if dow in (4, 5, 6) else 1.0
        month = d.month

        # Seasonality adjustments by city/month
        season_mult = 1.0
        if h.city in ["Goa", "Jaipur", "Kochi"] and month in [11, 12, 1]:
            season_mult = 1.25
        if h.city in ["Goa", "Kochi"] and month in [7, 8]:
            season_mult = 0.82

        demand_lambda = 0.55 * weekend_mult * season_mult
        if h.property_type == "Budget":
            demand_lambda *= 1.4
        if h.property_type == "Premium":
            demand_lambda *= 0.7
        if h.property_type == "Boutique":
            demand_lambda *= 0.95
        if h.property_type == "Business":
            demand_lambda *= 1.05

        room_nights = rng.poisson(h.total_rooms * demand_lambda)
        room_nights = min(max(room_nights, 0), h.total_rooms)
        if room_nights == 0:
            if rng.random() < 0.1:
                room_nights = 1
            else:
                continue

        channel = channels[rng.choice(len(channels), p=[0.35, 0.25, 0.15, 0.25])]
        status = "Completed"
        cancel_prob = 0.14
        if channel in ["App", "OTA Partner"]:
            cancel_prob += 0.04
        if h.city in ["Goa", "Jaipur"] and month in [11, 12, 1]:
            cancel_prob -= 0.03
        if rng.random() < cancel_prob:
            status = "Cancelled"
        elif rng.random() < 0.02:
            status = "No-Show"

        adr = base_adr(h) * weekend_mult * season_mult
        base_price = adr
        disc = 0.0
        if channel in ["App", "Web"]:
            disc = base_price * rng.uniform(0.08, 0.18)
        elif channel == "OTA Partner":
            disc = base_price * (rng.uniform(0.12, 0.20) if rng.random() < 0.4 else rng.uniform(0.05, 0.12))
        else:
            disc = base_price * rng.uniform(0.0, 0.08)
        final_price = max(base_price - disc, base_price * 0.6)

        los = int(rng.choice([1, 2, 3], p=[0.55, 0.32, 0.13]))
        checkin = d
        checkout = d + pd.Timedelta(days=los)

        booking_rows.append(
            {
                "booking_id": book_id,
                "booking_date": d.date(),
                "checkin_date": checkin.date(),
                "checkout_date": checkout.date(),
                "hotel_id": int(h.hotel_id),
                "room_nights_booked": int(room_nights),
                "booking_status": status,
                "booking_channel": channel,
                "base_price": round(base_price, 2),
                "discount_amount": round(disc, 2),
                "final_price_paid": round(final_price, 2),
            }
        )
        book_id += 1

booking_data = pd.DataFrame(booking_rows)

cancel_reasons = [
    "Customer Cancelled",
    "Price Change",
    "Payment Failure",
    "Property Issue",
    "Double Booking",
]
cancel_df = booking_data[booking_data.booking_status == "Cancelled"].copy()
cancel_df["cancellation_reason"] = cancel_df.apply(
    lambda r: rng.choice(cancel_reasons, p=[0.55, 0.12, 0.12, 0.12, 0.09]), axis=1
)
cancel_df["refund_flag"] = cancel_df.apply(
    lambda r: "Yes"
    if ((r.booking_channel in ["App", "OTA Partner"] or r.final_price_paid > 2500) and rng.random() < 0.75)
    else "No",
    axis=1,
)
cancellation_data = cancel_df[["booking_id", "hotel_id", "cancellation_reason", "refund_flag"]]


def commission_rate(row: pd.Series) -> float:
    h = hotel_master.loc[hotel_master.hotel_id == row.hotel_id].iloc[0]
    base = 0.18
    if h.partner_type == "Franchise":
        base -= 0.03
    if h.partner_type == "Affiliate":
        base += 0.04
    if h.region_category == "Metro":
        base -= 0.01
    if row.booking_channel == "OTA Partner":
        base += 0.03
    return round(max(0.10, min(base, 0.27)), 4)


rev_rows = []
for _, r in booking_data.iterrows():
    rate = commission_rate(r)
    platform = r.final_price_paid * rate if r.booking_status == "Completed" else 0.0
    partner = r.final_price_paid - platform
    rev_rows.append(
        {
            "booking_id": r.booking_id,
            "hotel_id": r.hotel_id,
            "commission_rate_pct": rate * 100,
            "revenue_share_partner": round(partner, 2),
            "revenue_share_platform": round(platform, 2),
        }
    )
revenue_payments = pd.DataFrame(rev_rows)

# Persist CSV outputs
hotel_master.to_csv("hotel_master.csv", index=False)
booking_data.to_csv("booking_data.csv", index=False)
cancellation_data.to_csv("cancellation_data.csv", index=False)
revenue_payments.to_csv("revenue_payments.csv", index=False)

print("Generated CSV files:")
print("- hotel_master.csv")
print("- booking_data.csv")
print("- cancellation_data.csv")
print("- revenue_payments.csv")
