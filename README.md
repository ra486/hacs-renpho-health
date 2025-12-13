# Renpho Health Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/ra486/hacs-renpho-health.svg)](https://github.com/ra486/hacs-renpho-health/releases)
[![License](https://img.shields.io/github/license/ra486/hacs-renpho-health.svg)](LICENSE)

A Home Assistant integration that fetches body composition data from Renpho smart scales using the Renpho Health app API.

## Features

This integration provides the following sensors:

| Sensor | Unit | Description |
|--------|------|-------------|
| Weight | kg / lbs | Current weight |
| Body Fat | % | Body fat percentage |
| BMI | - | Body Mass Index |
| Muscle Mass | % | Muscle mass percentage |
| Body Water | % | Body water percentage |
| Bone Mass | kg | Bone mass |
| BMR | kcal | Basal Metabolic Rate |
| Body Age | years | Metabolic age |
| Visceral Fat | - | Visceral fat level (1-59) |
| Subcutaneous Fat | % | Subcutaneous fat percentage |
| Protein | % | Protein percentage |
| Lean Body Mass | kg | Lean body mass |
| Fat Free Weight | kg | Fat-free weight |
| Heart Rate | bpm | Heart rate (if available) |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/ra486/hacs-renpho-health`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Renpho Health" and install it
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [Releases page](https://github.com/ra486/hacs-renpho-health/releases)
2. Extract and copy the `custom_components/renpho_health` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Renpho Health"
4. Enter your Renpho account email and password
5. Click **Submit**

### Options

After setup, you can configure:
- **Refresh interval**: How often to fetch new data (default: 3600 seconds / 1 hour)

## Supported Devices

This integration works with Renpho smart scales that sync data to the **Renpho Health** app, including:
- Renpho Smart Body Fat Scale
- Renpho Bluetooth Body Fat Scale
- Renpho WiFi Smart Scale
- And other Renpho body composition scales

## API Details

This integration uses the Renpho Health cloud API (`cloud.renpho.com`) with AES-128 ECB encryption.

### Token Caching

To minimize logouts from the mobile app, this integration:
- Caches the authentication token locally after the first login
- Reuses the cached token for subsequent API calls
- Only re-authenticates when the token expires or becomes invalid

This significantly reduces the frequency of mobile app logouts compared to integrations that login on every refresh.

### Endpoints Used

- `renpho-aggregation/user/login` - Authentication
- `RenphoHealth/healthManage/dailyCalories` - Body composition data

## Troubleshooting

### "Invalid email or password"
- Verify your credentials work in the Renpho Health app
- Make sure you're using the email/password, not social login

### "Failed to connect"
- Check your internet connection
- Renpho servers may be temporarily unavailable

### Sensors show "unknown"
- Wait for the first data refresh (up to 1 hour by default)
- Check Home Assistant logs for errors
- Ensure you have recent measurements in the Renpho app

## Credits

- API encryption details from [RenphoGarminSync-CLI](https://github.com/forkerer/RenphoGarminSync-CLI)
- Original API research from [hass-renpho](https://github.com/neilzilla/hass-renpho)

## Disclaimer

This integration is unofficial and not affiliated with Renpho. Use at your own risk. The API may change without notice.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
