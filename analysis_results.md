# Analysis of Hanle Published AWS Data

This document provides a detailed breakdown of the telemetry and weather data stored in the Hanle published Automatic Weather Station (AWS) log files located in [data/raw/hanle_published/](file:///c:/Users/2021n/Downloads/era5_wind_data_analysis/data/raw/hanle_published/).

---

## File Summary and Data Dimensions

There are two sample log files available:
1. **[20200101_MetsSerServr.txt](file:///c:/Users/2021n/Downloads/era5_wind_data_analysis/data/raw/hanle_published/20200101_MetsSerServr.txt)**
   * **Size:** ~1.46 MB
   * **Total Lines:** 8,763 (8,739 parsed records)
   * **Log Time Range:** 2020-01-01 17:19:31.562 to 2020-01-02 05:29:55.359
   * **Sensor Time Range:** 2020-01-01 17:43:52 to 2020-01-02 05:54:17 (approx. 12 hours)
2. **[20200104_MetsSerServr.txt](file:///c:/Users/2021n/Downloads/era5_wind_data_analysis/data/raw/hanle_published/20200104_MetsSerServr.txt)**
   * **Size:** ~2.89 MB
   * **Total Lines:** 17,278 (17,278 parsed records)
   * **Log Time Range:** 2020-01-04 05:30:01.906 to 2020-01-05 05:29:58.000
   * **Sensor Time Range:** 2020-01-04 05:54:22 to 2020-01-05 05:54:17 (approx. 24 hours)

---

## Telemetry String Structure (Rows)

Each valid log line recorded by the serial server program (`MetsSerServr`) contains a raw serial package of **13 comma-separated fields** wrapped inside an envelope:

```
2020/01/01 17:22:06.375  *** Logged string = "<013>AA,2020/01/01,17:46:27,-11.5,******,018.6,15.2,223,0,053.45,-00.26,ZZ,3504<013><010>" ***
```

* **`<013>`** represents ASCII Carriage Return (`\r`).
* **`<010>`** represents ASCII Line Feed (`\n`).
* The payload string sent from the station is: `\rAA,2020/01/01,17:46:27,-11.5,******,018.6,15.2,223,0,053.45,-00.26,ZZ,3504\r\n`.

---

## Column Descriptions

Here is the parsed schema of the 13 comma-separated columns based on statistical ranges, correlation matrices, and physical characteristics:

| Col Index | Field Name | Data Type | Sample Values | Statistical Range | Description / Physical Interpretation |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **0** | `Header` | String | `AA` | Constant `AA` | Start-of-line payload marker. |
| **1** | `Date` | String | `2020/01/01` | `2020/01/01` to `2020/01/05` | Sensor system date (`YYYY/MM/DD`). |
| **2** | `Time` | String | `17:46:27` | `00:00:00` to `23:59:59` | Sensor system time (`HH:MM:SS`). |
| **3** | `Temperature` | Float | `-11.5` | `-18.4°C` to `-11.5°C` | Ambient air temperature (in Celsius). |
| **4** | `Pressure/DewPoint`| String | `******` | Constant `******` | Missing or disabled parameter (likely Barometric Pressure or Dew Point). |
| **5** | `Relative Humidity`| Float | `018.6` | `18.3%` to `40.5%` | Relative humidity (in %). Strong negative correlation with Temperature ($r = -0.764$). |
| **6** | `Wind Speed` | Float | `15.2` | `0.0` to `21.7 m/s` | Instantaneous wind speed (in m/s). |
| **7** | `Wind Direction` | Integer | `223` | `0°` to `358°` | Wind direction in degrees (0° to 360°). |
| **8** | `Precipitation` | Integer | `0` | Constant `0` | Rain gauge accumulation (inactive/zero in winter). |
| **9** | `System Voltage` | Float | `053.45` | `52.83 V` to `53.59 V` | Power bank battery voltage. Matches a 48V nominal battery system floating level. |
| **10** | `System Current` | Float | `-00.26` | `-0.31 A` to `0.89 A` | Charger/load battery current. Consistently around `-0.27 A` (consumes ~15 Watts). |
| **11** | `Footer` | String | `ZZ` | Constant `ZZ` | End-of-payload marker. |
| **12** | `Checksum` | Integer | `3504` | `3457` to `3531` | Sum of ASCII codes of characters from initial `\r` up to `ZZ,`. |

---

## Key Telemetry Findings & Quirks

### 1. 5-Second Sampling Frequency
The weather station transmits data packages exactly every **5 seconds**. The time delta frequency count shows that over $99.9\%$ of consecutive records are exactly 5 seconds apart.

### 2. Midnight Rollover Hour Format Bug
An interesting firmware quirk was discovered in the sensor's clock:
* Instead of printing `00:00:XX` during the first minute of the day (from 12:00:00 AM to 12:00:59 AM), the sensor formats the hour as `24:`.
* Example sequence from log:
  * `2020/01/01,23:59:57` (23:59:57 PM)
  * `2020/01/02,24:00:03` (representing 00:00:03 AM)
  * `2020/01/02,24:00:58` (representing 00:00:58 AM)
  * `2020/01/02,00:01:02` (00:01:02 AM)
* Notice that once the minute counter hits `01`, the hour correctly formats as `00`. To parse these datetimes in Python without error, the hour `24` must be replaced with `00` before parsing.

### 3. Systematic Clock Offset
There is a highly stable time difference between the PC logger's clock and the internal AWS clock:
* **Clock Offset:** The sensor's clock is systematically ahead (fast) by **24 minutes and 20 seconds** (mean offset of $1461.3\text{ s}$ for Jan 1 and $1459.6\text{ s}$ for Jan 4).
* **Drift Rate:** The drift is very low, changing by only about $1.7\text{ s}$ per day ($Std \approx 0.4\text{ s}$–$0.5\text{ s}$).

### 4. Alternating Power Telemetry (Dual-Channel/Redundancy)
The power telemetry columns (`col_9` and `col_10`) alternate values every 5 seconds between two states:
* **State A:** Voltage $\approx 53.0\text{ V}$, Current $\approx -0.30\text{ A}$ (Power $\approx 15.9\text{ W}$)
* **State B:** Voltage $\approx 53.4\text{ V}$, Current $\approx -0.27\text{ A}$ (Power $\approx 14.4\text{ W}$)
This suggests the weather station monitors two redundant battery banks or power controllers in an alternating query sequence.

### 5. Checksum Verification
The final column (`col_12`) acts as an integrity checksum. It is calculated by taking the sum of the ASCII values of all characters starting from the leading Carriage Return (`\r` or `<013>`) through the final comma after `ZZ`.

For example, on the line:
`\rAA,2020/01/01,17:46:27,-11.5,******,018.6,15.2,223,0,053.45,-00.26,ZZ,3504`
The ASCII sum of `\rAA,2020/01/01,17:46:27,-11.5,******,018.6,15.2,223,0,053.45,-00.26,ZZ,` equals exactly **3504**.
