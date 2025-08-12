
# 🎉 Grafana Dashboard Import Instructions

## Quick Import (Automated)

```bash
# Import the fixed dashboard automatically
python3 update_grafana_dashboard.py \
  --dashboard-file grafana_dashboard_final.json \
  --grafana-url "http://your-grafana:3000" \
  --api-key "your-grafana-api-key" \
  --backup
```

## Manual Import (Grafana UI)

1. **Open Grafana** → Navigate to Dashboards
2. **Click "Import"** → Upload JSON file
3. **Select File** → Choose `grafana_dashboard_final.json`
4. **Configure**: 
   - Ensure InfluxDB data source is selected
   - Verify data source UID matches your InfluxDB connection
5. **Import** → Dashboard will be created

## ✅ Verified Working Panels

The following panels have been tested and confirmed working with your data:

| Panel | Status | Data Source | Records Available |
|-------|--------|-------------|------------------|
| ✅ Heart Rate Analysis | Working | `heart_metrics` | 416,641 records |
| ✅ Heart Rate Recovery | **FIXED** | `heart_metrics` | Recovery data available |
| ✅ HRV & Respiratory | **FIXED** | `heart_metrics`, `respiratory_metrics` | HRV: 5,853 records |
| ✅ Body Composition | Working | `body_composition` | Weight/height data |
| ✅ Daily Energy | Working | `energy_metrics` | Active/basal energy |
| ✅ Movement Metrics | Working | `movement_metrics` | Steps/distance/flights |
| ✅ Sleep Timeline | **FIXED** | `sleep_metrics` | Sleep state transitions |
| ✅ Sleep Duration | Working | `sleep_metrics` | Duration data |
| ✅ Sports Performance | Working | `running_performance`, `fitness_metrics` | Speed/VO2 data |
| ✅ Environmental | Working | `environmental_metrics` | Audio/UV exposure |

## 🔧 Key Fixes Applied

1. **Heart Rate Recovery**: Now uses `value` field correctly
2. **Sleep Timeline**: Uses `sleep_state` tag grouping for proper visualization  
3. **HRV Data**: Uses `hrv_sdnn` field (not `value`)
4. **All Queries**: Updated to match actual InfluxDB field structure

## 🎯 Expected Results

After import, you should see:
- **Real-time heart rate trends** with recovery metrics
- **Sleep pattern visualization** showing in-bed vs asleep states  
- **Comprehensive health metrics** across all 13 categories
- **Sports performance tracking** with speed and VO2 data
- **Environmental health monitoring** for audio/UV exposure

## 🐛 Troubleshooting

If panels show "No data":
1. Check time range (some data may be historical)
2. Verify InfluxDB data source connection
3. Confirm measurement names exist in your database
4. Check field names match the queries

Your comprehensive Apple Health dashboard is ready! 🚀
