from typing import Optional, Dict, Any, Tuple


def get_aqi_category_and_risk(aqi: float) -> Tuple[str, str, str, str]:
    """
    Centralized AQI categorization, risk assessment, and styling utility.
    Returns:
        (category, risk_level, color_hex, health_summary)
    """
    val = float(aqi)
    if val <= 50.0:
        return (
            "Good",
            "Low Risk",
            "#10B981",  # Emerald
            "Air quality is clean and satisfactory, and air pollution poses little or no risk."
        )
    elif val <= 100.0:
        return (
            "Moderate",
            "Moderate Risk",
            "#F59E0B",  # Amber
            "Air quality is acceptable; however, unusually sensitive individuals should consider limiting prolonged outdoor exertion."
        )
    elif val <= 150.0:
        return (
            "Unhealthy for Sensitive Groups",
            "Elevated Risk",
            "#F97316",  # Orange
            "Members of sensitive groups (asthma, children, seniors) may experience health effects. General public is less likely to be affected."
        )
    elif val <= 200.0:
        return (
            "Unhealthy",
            "High Risk",
            "#EF4444",  # Rose/Red
            "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects."
        )
    elif val <= 300.0:
        return (
            "Very Unhealthy",
            "Very High Risk",
            "#8B5CF6",  # Violet/Purple
            "Health alert: The risk of health effects is increased for everyone. Strenuous outdoor physical activity should be avoided."
        )
    else:
        return (
            "Hazardous",
            "Hazardous Risk",
            "#7F1D1D",  # Deep Maroon
            "Health warning of emergency conditions: Everyone is more likely to be affected by severe respiratory and cardiovascular stress."
        )
