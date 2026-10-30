# Data Sources Research (Phase 2)

**Status:** Phase 2 deliverable, **approved 2026-10-29** (NOTES.md D-015). Approved choices: Strategy 1, "BTS-centric hybrid" (D-016), with D-017 to D-021. This document's text is otherwise kept as the research record from 2026-10-28.
**Research date:** 2026-10-28. Time-boxed to about 2 hours (NOTES.md D-009).
**Method:** small read-only HTTP requests (curl, plus Python standard-library scripts in the session scratchpad). Nothing was added to the repository except this file and NOTES.md updates.

## 0. Evidence labels

| Label | Meaning |
|---|---|
| **[LIVE]** | Verified with a real HTTP request on 2026-10-28. The status code and the observed fields are recorded here. |
| **[DOC]** | Verified from official documentation only. Not exercised. |
| **[NOT VERIFIED]** | Not checked, or the check was inconclusive. Must not be relied on. |
| **[REC]** / **[ASSUMPTION]** | Our recommendation or assumption. Not a fact about the source. |

> Numbers quoted below are **raw values observed during feasibility probes**. They show that the data exists and how definitions affect results. They are **not** final answers to the assignment questions: no metric definitions have been approved.

---

## 1. Summary

1. **BTS (US DOT) is the strongest source family.** One dataset is a real public JSON API with no key required (Socrata SODA): monthly traffic per origin airport, 2014 → **July 2026**. Route-level T-100 data (distance, service class, scheduled vs. performed departures) is downloadable programmatically, through a web form rather than a documented API.
2. **Q3 (Anchorage long-haul %) is directly measurable** from T-100 Segment data once "long haul" and cargo inclusion are defined. The probe confirmed the cargo issue is material: in Dec 2025, all-cargo service classes (G + P) made up **4,330 of 6,872** ANC departures performed (about 63%).
3. **Q1 (New England expansion) is feasible as an indicator ranking.** Demand, growth, and load-factor data are available. **Terminal capacity data was not found** in any machine-readable public source.
4. **Q2 (LAX vs. SNA congestion):** historical delay data comes from BTS on-time files (bulk monthly files). Delay, taxi-out, cancellation, and delay-cause fields were **verified** (§3.3). FAA live APIs provide only real-time status snapshots. FAA runway capacity profiles exist only as old PDFs.
5. **Q4 (SFO unmet demand):** **proxy-only.** Possible proxies: load factor, scheduled vs. performed departures, delay causes, the FAA demand forecast (TAF), and capacity profiles. Any "why" must be limited to factors visible in the data.
6. **Blockers found:**
   - OpenSky historical flights need an account (anonymous access returns 403).
   - The FAA ASPM/ATADS portals returned 503 when tested.
   - The legacy FAA ASWS host no longer resolves.
   - The BTS bulk on-time download is slow (more than 5 minutes for about 33 MB in one attempt).
   - The T-100 route-level download depends on a fragile ASP.NET form.

---

## 2. Source inventory

### 2.1 BTS Socrata API: "AFF - T100 Segment Summary By Origin Airport" (`r495-tyji`) **[LIVE]**
- **Docs:** https://data.bts.gov/d/r495-tyji · SODA API docs https://dev.socrata.com/
- **Endpoints tested:**
  - `GET https://data.bts.gov/resource/r495-tyji.json?$limit=2` → **200**, JSON
  - `GET https://data.bts.gov/api/views/r495-tyji.json` → **200**, metadata (description: "Commercial air passengers, seats, freight, and mail by origin airport.")
  - SoQL aggregation (`$select=…sum(total_departures)…&$group=origin_airport_code,year`) → **200**. Server-side filtering and aggregation work.
- **Fields (verified):** `origin_airport_code`, `year`, `reporting_month`, `total_departures`, `total_passengers`, `total_seats`, `total_load_factor`, `total_distance_flight_sm` (average distance per flight), `total_freight_lbs`, `total_mail_lbs`, domestic_* equivalents, and `outbound_international*` / `inbound_international*` fields (departures, passengers, seats, load, distance, freight). Some international field names are **truncated or ambiguous** (`outbound_international_1` … `_4`), and their meaning was **[NOT VERIFIED]** beyond inference from values.
- **Coverage/freshness (verified):** monthly rows from **2014-01 to 2026-07** (12 months for each year 2014–2025, 7 months for 2026). Dataset updated 2026-10-27. **About a 3-month lag.** All US origin airports with T-100 reports, including small ones (for example "01A").
- **Auth/pricing/limits:**
  - **[LIVE]** No key needed.
  - **[DOC]** An optional app token gives higher throttling limits. Unauthenticated requests share an IP-based pool and may get HTTP 429.
- **Limitations:**
  - No state or region field. Regions must be mapped through a reference dataset (§2.6 / §2.4).
  - Only **monthly averages per airport**. There is no distance distribution, so Q3 cannot be answered from this dataset alone.
  - Whether foreign carriers are included is **[NOT VERIFIED]**.
- **Probe observation (annual sums, illustrative only):** for example, SFO departures 2019 = 213,016 → 2024 = 177,573 → 2025 = 190,110. ANC freight 2025 ≈ 5.8 bn lbs vs. ANC passengers ≈ 2.71 M.

### 2.2 BTS TranStats: T-100 Segment (All Carriers), table FMG **[LIVE]**
- **Docs:** https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FMG · download page `https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FMG&QO_fu146_anzr=Nv4%20Pn44vr45` (**200**, "Latest Available Data: July 2026").
- **How it was tested:** a stdlib Python script fetched the form, reused the ASP.NET `__VIEWSTATE`/`__EVENTVALIDATION`, and POSTed `cboYear=2025, cboPeriod=12` with selected fields. Result: **200**, `application/zip`, `T_T100_SEGMENT_ALL_CARRIER_*.zip` (626 KB), with 49,291 route rows for Dec 2025.
- **Fields (verified in the downloaded CSV):** `DEPARTURES_SCHEDULED`, `DEPARTURES_PERFORMED`, `SEATS`, `PASSENGERS`, `FREIGHT`, `DISTANCE` (miles between airports), `UNIQUE_CARRIER`, `ORIGIN`, `DEST`, `DEST_COUNTRY`, `YEAR`, `MONTH`, `CLASS`. The form also offers `AIRCRAFT_TYPE`, `AIR_TIME`, `RAMP_TO_RAMP`, `DISTANCE_GROUP`, `ORIGIN_STATE_ABR`, and more (field list verified on the page).
- **CLASS codes [DOC]:**
  - F = scheduled passenger/cargo
  - G = scheduled all-cargo
  - L = non-scheduled civilian passenger/cargo
  - P = non-scheduled civilian all-cargo
  - Sources: [eCFR 14 CFR 291.45](https://www.ecfr.gov/current/title-14/chapter-II/subchapter-A/part-291/subpart-E/section-291.45), [BTS T-100 guide (2007)](https://www.bts.gov/sites/bts.dot.gov/files/docs/explore-topics-and-geography/topics/airlines-and-airports/219466/t100-guide-april-2007.pdf). The TranStats lookup URL we tried returned an error page.
- **Auth/limits:** none observed. **[NOT VERIFIED]** whether automated form posting is permitted or rate limited.
- **Limitations:**
  - **This is not a documented API.** It is a form postback that could break if the page changes.
  - Downloads cover one month for the whole country. Origin filtering happens client-side.
  - DEPARTURES_SCHEDULED is 0 or absent for non-scheduled classes.
- **Probe observation (Dec 2025, departures performed from ANC, illustrative only):**

  | Distance band (miles) | All classes | Passenger classes only (F+L) |
  |---|---|---|
  | < 1,500 | 3,252 | 2,104 |
  | 1,500–2,999 | 1,265 | 402 |
  | 3,000–4,499 | 1,854 | 33 |
  | ≥ 4,500 | 501 | 3 |
  | **Total** | **6,872** | **2,542** |

  The share of flights at or above any threshold changes sharply depending on whether cargo is included. This confirms OQ-5 is high-impact.

### 2.3 BTS TranStats: Reporting Carrier On-Time Performance (bulk monthly ZIP) **[LIVE]**, fields verified in §3.3
- **Docs:** https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FGJ
- **Endpoint tested:** `HEAD https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2026_7.zip` → **200**, 33,075,361 bytes, Last-Modified 2026-09-21. Files for 2026_6 and 2025_12 also returned 200. The directory listing `https://www.transtats.bts.gov/PREZIP/` returned 200.
- **Content [LIVE]:** flight-level records with origin, destination, departure/arrival delay, taxi-out, cancellations, delay causes, and distance. See §3.3.
- **Limitations:**
  - Large files. The full download took 356 s, and an earlier attempt timed out at 300 s.
  - **Reporting carriers only.** ANC cargo flights were absent in the probe. "Domestic only" is **[DOC, to confirm]**.
  - About a 2–3 month lag.

### 2.4 FAA: CY2025 Commercial Service Enplanements (Excel) **[LIVE]**
- **Docs/page:** https://www.faa.gov/airports/planning_capacity/passenger_allcargo_stats/passenger (**200**)
- **Endpoint tested:** `GET …/passenger/arp-cy2025-commercial-service-enplanements.xlsx` → **200**, 58 KB. Also linked: all-enplanements and all-cargo CY2025 files.
- **Fields (verified):** `Rank, RO (FAA region), ST (state), Locid, City, Airport Name, S/L (service level, e.g. P = primary, CS = non-primary commercial service), Hub (L/M/S/N), CY 25 Enplanements, CY 24 Enplanements, % Change`. 522 airport rows.
- **New England (verified):** 27 airports with `RO = NE`, covering CT, ME, MA, NH, RI, VT. Of those, 16 are primary airports (S/L = P). This was corrected in Phase 5 from a miscount of 15 (NOTES.md P-040). for example BOS (L hub), BDL (M), PVD, PWM, HVN, BTV, MHT (S). This gives a defensible, official airport list for Q1.
- **Limitations:**
  - An annual file, not an API.
  - Only two years per file. Earlier years need earlier files **[NOT VERIFIED]**.
  - Published as XLSX, so parsing needs care. The probe used stdlib XML parsing.

### 2.5 FAA live status APIs **[LIVE]**
| Endpoint | Result | Content |
|---|---|---|
| `GET https://nasstatus.faa.gov/api/airport-status-information` | **200**, XML | Current closures, ground stops, ground delays. Snapshot only. |
| `GET https://nasstatus.faa.gov/api/airport-events` | **200**, JSON | Current airport events (ground stop/delay, closures, NOTAM free-form). |
| `GET https://external-api.faa.gov/asws/api/airport/status/SFO` | **200**, JSON | Name, IATA/ICAO, `Delay`, `DelayCount`, `Status`, `Weather`, and `SupportedAirport` (**SNA returned `"SupportedAirport": false`**). |
| `GET https://soa.smext.faa.gov/asws/api/airport/status/SFO` | **DNS failure** (curl exit 6) | Legacy host. Do not use. |

- **Auth:** none required for the observed requests.
- **Limitation:** **real-time snapshots only, with no history.** Not suitable on their own for "congestion levels" over time. Could add current context (for example, an active ground delay program).
- **Observation:** both feeds showed a recurring nightly closure NOTAM for SNA (`AD AP CLSD DLY 0630-1315` UTC). This is relevant context for capacity at SNA. Its interpretation (for example, a curfew) is **[NOT VERIFIED]**.

### 2.6 OurAirports reference data (CSV) **[LIVE]**
- **Endpoint tested:** `GET https://davidmegginson.github.io/ourairports-data/airports.csv` → **200**, about 12.7 MB.
- **Fields (verified):** `ident, type, name, latitude_deg, longitude_deg, iso_country, iso_region (e.g. US-MA), municipality, scheduled_service, icao_code, iata_code, …`
- **Entity resolution (verified):** KSNA = "John Wayne Orange County International Airport", municipality **Santa Ana** (supports A-007). KLAX, KSFO, PANC, and KBOS are present. Coordinates allow great-circle distances.
- **License:** **[NOT VERIFIED]** in this session.

### 2.7 FAA Airport Capacity Profiles (PDF) **[LIVE: files exist]**
- **Index:** https://www.faa.gov/airports/planning_capacity/profiles (**200**). Profiles are listed for about 34 airports, including **LAX (2014)**, **SFO (2019)**, **BOS (2019)**, and **SNA (2014 appendix)**. The SFO and LAX PDFs returned **200**.
- **Content [DOC, search summary]:** hourly runway capacity ranges (ATC "called" rates and model estimates) by weather condition.
- **Limitations:**
  - These are PDFs from 2014–2019 and may be outdated.
  - The values were **not extracted or verified** in this session.
  - Manual transcription would be needed and must be cited.
  - Runway (airside) capacity is not terminal capacity.

### 2.8 FAA Terminal Area Forecast (TAF) **[LIVE: file]**, values **[NOT VERIFIED]**
- **Page:** https://www.faa.gov/data_research/aviation/taf (**200**). Bulk file `https://taf.faa.gov/Downloads/APO100_TAF_Final_2025.zip` → **200**, 15.7 MB. It contains `Airports.xlsx`, `AirportsOperations.xlsx`, `Enplanements.xlsx`, `BasedAircraft.xlsx`, and `Tracon.xlsx`.
- **Headers (verified):**
  - Enplanements: `locid, scenario, ayear, aac, aat, commuter, us_flag, frgn_flag`
  - Operations: `locid, scenario, ayear, itn_Ac, itn_at, itn_ga, itn_mil, loc_ga, loc_mil, tot_overs`
  - Years run from 1976/1990 to **2055**.
- **Not verified:** the stdlib parser did not find SFO, SNA, or BOS rows within the time box. Locid format and field semantics are still to be confirmed.
- **Potential use:** forecast demand vs. current or capacity, as an "unmet/future demand" proxy (Q1/Q4).

### 2.9 OpenSky Network REST API **[LIVE + DOC]**
- **Docs:** https://openskynetwork.github.io/opensky-api/rest.html
- **Endpoints tested:**
  - `GET /api/states/all?lamin=61&lomin=-150.5&lamax=61.3&lomax=-149.8` → **200**, live state vectors (callsigns near ANC, for example `FDX5178`)
  - `GET /api/flights/departure?airport=PANC&begin=…&end=…` → **403** "You cannot access historical flights"
  - `GET /api/flights/arrival?airport=KSFO…` → **403**
- **Auth/limits [DOC]:**
  - OAuth2 client credentials only. Tokens last 30 minutes.
  - Daily credits: anonymous 400, standard user 4,000.
  - Anonymous users get only current state vectors.
  - Flights endpoints are limited to intervals of about 2 days. The docs contain conflicting wording for `/flights/departure`.
- **Limitations:**
  - Requires account registration. **This is a blocker** for anonymous or reviewer use.
  - Departure and arrival airports are *estimated* from ADS-B coverage.
  - Passenger and cargo are not distinguished except by inference from callsigns.
  - Terms of use: **[NOT VERIFIED]**.

### 2.10 Checked and not usable (as tested)
| Source | Result |
|---|---|
| BTS Socrata on-time / delay items (`rns4-gpqn`, `eaz9-4bny`, `hdqs-8yds`) | **[LIVE]** These are *chart* assets. The underlying data covers national or top-5 summaries, not per-airport. |
| BTS Socrata `kqac-tdpz` "U.S. Airline Traffic Analytics" | **[LIVE]** 403 "non-tabular". |
| FAA ATADS/OPSNET (`aspm.faa.gov/opsnet/sys/airport.asp`) and ASPM | **[LIVE]** 301, then **503** at test time. ASPM access requirements **[NOT VERIFIED]**. |

### 2.11 Not verified (candidates only)
- **BTS DB1B (O&D survey, 10% ticket sample):** PREZIP files exist up to 2025 Q2 (listing verified). Content, size, and usefulness as a demand or fare proxy were **[NOT VERIFIED]**.
- **Commercial APIs** (for example AviationStack, AeroDataBox, FlightAware AeroAPI, Cirium): **[NOT VERIFIED]**. They usually need keys or paid tiers and add a reviewer setup burden.
- **Terminal / gate capacity** from any source: **not found.** Likely only in airport master plans (PDF), **[NOT VERIFIED]**.

---

## 3. Feasibility per example question

### 3.1 Q1: "Which airports in New England are strong candidates for terminal expansion?"
| Need | Source | Evidence |
|---|---|---|
| Airport list for New England | FAA enplanements (`RO=NE`, `ST`), OurAirports (`iso_region`) | LIVE |
| Passenger demand and growth | FAA CY24/CY25; BTS `r495` monthly 2014–2026-07 | LIVE |
| Utilization / pressure | BTS `r495` load factor, seats vs. passengers | LIVE |
| Future demand | FAA TAF | File LIVE, values NOT VERIFIED |
| **Terminal capacity (gates, sq ft)** | **None found** | Missing |

**Verdict: feasible as a transparent *proxy-based indicator ranking*** (demand level, growth, load factor, optionally forecast). It cannot measure terminal capacity utilization directly, and the answer must say so.

### 3.2 Q2: "Compare LA and Santa Ana airport congestion levels."
| Need | Source | Evidence |
|---|---|---|
| Entity resolution | OurAirports, FAA | LIVE (SNA = Santa Ana). "LA" is still ambiguous (OQ-6). |
| Historical delays, taxi-out, cancellations | BTS on-time files | LIVE (§3.3) |
| Traffic volume (departures, seats) | BTS `r495`, T-100 | LIVE |
| Scheduled vs. performed departures | T-100 Segment | LIVE |
| Runway capacity | FAA capacity profiles (PDF, 2014) | Files LIVE, values NOT VERIFIED |
| Current status | FAA NAS status / ASWS | LIVE (snapshot only; ASWS marks SNA unsupported) |

**Verdict: feasible for a *delay-based* congestion comparison** (fields verified in §3.3). A *utilization-based* comparison is only possible with static, dated capacity figures from PDFs. Comparing airports of very different sizes needs rates or normalized metrics.

### 3.3 On-time file field check **[LIVE]**
- **Download:** the July 2026 file returned **200**, 33,075,361 bytes, in **356 s**. It contains `On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2026_7.csv` with **110 columns**.
- **Fields verified (subset):** `FlightDate, Reporting_Airline, Origin, OriginState, Dest, DestState, DepDelay, DepDelayMinutes, DepDel15, TaxiOut, TaxiIn, ArrDelay, ArrDel15, Cancelled, CancellationCode, Diverted, Distance, DistanceGroup, CarrierDelay, WeatherDelay, NASDelay, SecurityDelay, LateAircraftDelay`.
- **Coverage observed (July 2026, departures from each airport in the file):** LAX 17,454 · SNA 3,992 · SFO 13,841 · ANC 2,513.
  - These counts are lower than the T-100 counts for the same airports, because only *reporting carriers* are included.
  - ANC cargo flights are absent.
- **Probe values (July 2026, illustrative only, definitions not approved):**

  | Airport | % departures ≥15 min late | Avg taxi-out (min) | Avg dep. delay (min) | Cancelled |
  |---|---|---|---|---|
  | LAX | 25.5 | 18.8 | 15.7 | 210 |
  | SNA | 26.0 | 16.8 | 16.8 | 45 |
  | SFO | 35.5 | 25.1 | 22.5 | 159 |

  Delay-cause minutes on arrivals into SFO were dominated by `NASDelay` (207,720 min, vs. 89,393 carrier and 109,456 late-aircraft). NAS delay covers air-traffic, airport, and weather-related system constraints [DOC, to cite precisely]. This is the kind of data-backed "why" evidence Q4 can use.
- **Implication:** Q2 is **feasible for delay-based congestion**. Q4 gains a cause breakdown. One month is not representative: a 12-month window would mean about 12 × 33 MB of downloads. This volume and download time are risks, and ingestion and caching must be designed for them.

### 3.4 Q3: "What is the percentage of long haul flights out of Anchorage airport?"
| Need | Source | Evidence |
|---|---|---|
| Departures per route with distance | T-100 Segment (`DISTANCE`, `DEPARTURES_PERFORMED`) | LIVE |
| Passenger vs. cargo split | T-100 `CLASS` (F/G/L/P) | LIVE (codes DOC) |
| Average distance and international share only | BTS `r495` | LIVE |

**Verdict: directly measurable** once **(a)** the long-haul threshold, **(b)** cargo inclusion, and **(c)** the time window are defined. The probe shows these choices change the result dramatically (§2.2 table). The answer should show the definition and could show the sensitivity.

### 3.5 Q4: "What is the unmet flight demand in SFO airport and why?"
| Candidate proxy | Source | Evidence |
|---|---|---|
| Load factor (passengers ÷ seats) | BTS `r495`, T-100 | LIVE |
| Scheduled vs. performed departures (cancellations) | T-100 | LIVE |
| Traffic vs. pre-2020 peak (recovery gap) | BTS `r495` 2014–2026 | LIVE |
| Delay causes (weather, NAS, carrier) | BTS on-time | LIVE (§3.3) |
| Forecast demand vs. current | FAA TAF | File LIVE, values NOT VERIFIED |
| Runway capacity by weather | FAA SFO capacity profile (2019 PDF) | File LIVE, values NOT VERIFIED |

**Verdict: proxy-only.** Unmet demand cannot be observed. The agent can report evidence *consistent with* constrained demand, such as high load factors, delay causes, and gaps between forecast and actual traffic. "Why" must be limited to data-backed factors, phrased as likely contributors with uncertainty. It must not draw on LLM background knowledge.

---

## 4. Access approaches compared

| Approach | Description | Meets "Use public APIs to gather data"? | Pros | Cons / risks |
|---|---|---|---|---|
| **A. Live API calls at query time** | The agent calls SODA, FAA status, and similar APIs for each question. | **Yes, most literal** | Fresh. Clearly API-driven. | Only some sources are true APIs. Latency, throttling, and outages during a demo. No route-level or on-time data through an API. |
| **B. Cached API responses** | The same API calls, cached locally with timestamps. | Yes (data still comes from public APIs) | Fast, reproducible demo. Resilient to outages. | Cache staleness must be disclosed. |
| **C. Public datasets (bulk files)** | Downloaded T-100 / on-time / FAA files, pre-processed. | **Interpretation risk (OQ-7):** files are public data, but not an "API" in the strict sense. | Richest data (route-level, delays). Deterministic. | Not "API" in the strict sense. Large or slow downloads. Fragile form postback for T-100. |
| **D. Hybrid** [REC] | Live SODA API for airport-level metrics. Programmatic, cached ingestion of public BTS/FAA files for route-level and delay data. Optional live FAA status for current context. Every answer cites source and data period. | **Yes, with a documented interpretation:** a real public API is used live, and supplementary public datasets are fetched programmatically. | Covers all four questions. Defensible. Demo-stable. | More moving parts. The interpretation must be stated in `architecture.md`. |

---

## 5. Recommended data strategies (for approval, none selected)

### Strategy 1: "BTS-centric hybrid" [REC, preferred]
- **Sources:**
  - Live: BTS SODA `r495-tyji`.
  - Programmatic, cached: T-100 Segment (All Carriers) monthly extract, BTS on-time monthly file(s) aggregated per airport, FAA CY2025 enplanements, OurAirports.
  - Optional live: FAA NAS status / ASWS.
- **Q1:** proxy ranking ✔ · **Q2:** delay-based ✔ · **Q3:** direct ✔ · **Q4:** proxy ✔ (limited "why")
- **Tradeoffs:**
  - Best coverage and credibility.
  - Needs a fixed data window (for example, the latest 12 months) and a cache.
  - The T-100 form-scraping step is fragile. Mitigation: pre-fetch it once and commit a small derived snapshot if allowed (licensing **[NOT VERIFIED]**).

### Strategy 2: "Live-API-first, minimal files"
- **Sources:** BTS SODA `r495-tyji` (live), FAA NAS status / ASWS (live), FAA enplanements, OurAirports. No T-100 route-level or on-time data.
- **Q1:** proxy ranking ✔ · **Q2:** volume and load proxies plus a live status snapshot only (weak) · **Q3:** only an *international share / average distance* proxy, **not** a true long-haul % (weak) · **Q4:** load factor and recovery-gap proxy (weak "why")
- **Tradeoffs:** simplest and most literal reading of "API". Q2–Q4 answers are noticeably weaker.

### Strategy 3: "Hybrid + OpenSky" (optional extension)
- Strategy 1 plus authenticated OpenSky for recent observed departures (for example, cross-checking ANC destinations).
- **Tradeoffs:**
  - Requires registering an account and OAuth credentials. Reviewers would need their own.
  - Airports are estimated, and passenger vs. cargo is ambiguous.
  - Adds little over T-100 for the four questions. **Not recommended for the MVP.**

### Feasibility verdict per strategy
| Question | Strategy 1 | Strategy 2 | Strategy 3 |
|---|---|---|---|
| Q1 New England expansion | Proxy ranking | Proxy ranking | Proxy ranking |
| Q2 LAX vs. SNA congestion | Delay-based | Weak | Delay-based |
| Q3 ANC long-haul % | **Direct** (with definitions) | Proxy only | Direct, plus a recent cross-check |
| Q4 SFO unmet demand / why | Proxy, data-backed factors | Weak proxy | Proxy |

---

## 6. Missing data and the direct vs. proxy distinction
- **Direct measurements available:**
  - departures, passengers, seats, load factor, freight, and distance per route (T-100)
  - scheduled vs. performed departures
  - delays, delay causes, cancellations, and taxi-out for reporting carriers (on-time, §3.3)
  - annual enplanements and hub class (FAA)
- **Proxies only:**
  - terminal capacity pressure
  - congestion when defined as utilization
  - unmet demand
  - causes ("why")
  - investment attractiveness (NOTES.md D-010)
- **Missing:**
  - terminal or gate capacity
  - current runway capacity in machine-readable form
  - airport financials and project costs
  - real-time historical flight data without registration

## 7. Open items for Phase 3 decisions
See NOTES.md (§3 assumptions, §2 open decisions). Key decisions:
- the strategy (1, 2, or 3)
- the "public API" interpretation (OQ-7)
- the data window
- whether to commit derived data snapshots to the repo
- definitions for long haul, cargo inclusion, congestion, and the unmet-demand proxy
