# Task 14 – AI Signals Dashboard

## 1. Objective

The objective of Task 14 is to develop an AI Signals Dashboard that presents anomaly analysis, financial risk, forecast trends, forecast confidence intervals, and forecast accuracy in an understandable format.

The dashboard also provides plain-English explanations and AI transparency labels so users can review AI-generated insights before making decisions.

## 2. Implementation

**Dashboard file:** `05_Starter/app_task14.py`

**Source datasets:**
- `03_Data/csv/fact_anomaly.csv`
- `03_Data/csv/fact_forecast.csv`
- `03_Data/csv/fact_headcount_monthly.csv`
- Historical attrition data used by the dashboard

The dashboard includes the following features:

1. **Anomaly Analysis:** Ranks anomaly categories by quantified money at risk, from highest to lowest.
2. **Anomaly Interpretation:** Displays explanations of anomaly categories and distinguishes quantified financial impact from unquantified anomalies.
3. **Headcount Forecast:** Compares historical actual headcount with forecast headcount.
4. **Confidence Interval:** Displays the forecast and its 80% confidence interval.
5. **Attrition Forecast:** Presents historical attrition alongside forecast attrition.
6. **Forecast Accuracy:** Displays forecast error calculations for forecast periods where actual values are available.
7. **AI Transparency:** Displays the label "AI-generated, for human review" alongside AI-generated charts.

## 3. Anomaly Analysis Results

The anomaly dataset contains 405 records.

- Total records: 405
- Records with quantified financial impact: 184
- Records without quantified financial impact: 221
- Total quantified money at risk: 31,421,239.07

The highest quantified anomaly category is `STATISTICAL_OUTLIER`, with a financial impact of 19,432,986.26.

Anomalies without a quantified financial impact are displayed separately and are not treated as zero financial risk.

## 4. Forecast Analysis Results

The forecast dataset contains 72 forecast records.

The headcount forecast covers October 2026 to March 2027.

For the overall (`ALL`) headcount forecast:

| Month | Forecast | Lower 80% | Upper 80% |
|---|---:|---:|---:|
| October 2026 | 426.3 | 417.5 | 435.1 |
| November 2026 | 429.7 | 419.9 | 439.5 |
| December 2026 | 431.4 | 420.7 | 442.2 |
| January 2027 | 436.0 | 424.4 | 447.6 |
| February 2027 | 439.7 | 427.3 | 452.1 |
| March 2027 | 439.8 | 426.6 | 453.0 |

The latest actual headcount available is 441 for September 2026.

The first overall forecast for October 2026 is 426.3. This is 14.7 lower than the latest actual headcount, approximately a 3.33% difference. This baseline difference is highlighted for human review and should not automatically be treated as a forecast error.

The dashboard also displays the attrition forecast for October 2026 to March 2027.

## 5. Forecast Accuracy

The forecast dataset contains 72 forecast records.

At the time of testing, the available actual headcount data ended in September 2026, while forecasts started in October 2026.

Therefore:
- Forecasts with matching actual values: 0
- Forecasts awaiting actual values: 72
- Forecast accuracy cannot yet be calculated for these future periods.

The dashboard communicates this limitation instead of displaying misleading forecast accuracy values.

## 6. Validation and Testing

The following validations were completed:

- Python syntax validation was successful using `python -m py_compile`.
- The Streamlit dashboard was launched successfully.
- Anomaly categories were displayed in descending order of quantified financial impact.
- Unquantified anomalies were distinguished from quantified anomalies.
- Actual and forecast headcount values were displayed.
- The 80% confidence interval was displayed.
- Attrition forecast information was displayed.
- Forecast accuracy information and the availability of actual values were checked.
- AI transparency labels and plain-English explanations were checked.
- Dashboard screenshots were captured as evidence.

## 7. Screenshot Evidence

The following screenshots are saved in `Reports/Task14/`:

1. `Task14_Dashboard_Overview.png`
2. `Task14_Anomaly_Analysis.png`
3. `Task14_Anomaly interpretation.png`
4. `Task14_Headcount_Forecast.png`
5. `Task14_Headcount_Forecast1.png`
6. `Task14_Attrition_Forecast.png`
7. `Task14_Forecast_Accuracy.png`
8. `Task14_AI_Transparency.png`

## 8. Conclusion

Task 14 dashboard implementation and visual testing have been completed.

The dashboard provides anomaly risk analysis, headcount and attrition forecasts, confidence intervals, forecast accuracy information, and AI transparency labels.

Forecast accuracy for future periods remains pending until corresponding actual values become available. All AI-generated insights are intended for human review before decisions are made.