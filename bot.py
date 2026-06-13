# Pulse - Weather Alert Bot
# Fetches: weather (OpenWeatherMap)
# Alerts:  email if temp > 35°C or rain is predicted
# Runs:    every day at 8 AM IST via GitHub Actions

import os
import smtplib
from datetime import date
from email.mime.text import MIMEText

import requests

CITY = "Thiruvananthapuram"
TEMP_ALERT_C = 35
OWM_BASE = "https://api.openweathermap.org/data/2.5"
RAIN_CONDITIONS = {"Rain", "Drizzle", "Thunderstorm"}


def _get_api_key():
    key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if not key:
        raise ValueError("OPENWEATHERMAP_API_KEY environment variable is not set")
    return key


def _is_rain(weather_entry):
    return weather_entry.get("main") in RAIN_CONDITIONS


def fetch_weather(city=CITY):
    """Fetch current weather and check for rain in the next 24 hours."""
    api_key = _get_api_key()
    params = {"q": city, "appid": api_key, "units": "metric"}

    current_resp = requests.get(f"{OWM_BASE}/weather", params=params, timeout=10)
    current_resp.raise_for_status()
    current = current_resp.json()

    forecast_resp = requests.get(f"{OWM_BASE}/forecast", params=params, timeout=10)
    forecast_resp.raise_for_status()
    forecast = forecast_resp.json()

    temp_c = current["main"]["temp"]
    conditions = current["weather"][0]["description"]
    rain_now = any(_is_rain(w) for w in current["weather"])

    rain_predicted = rain_now
    if not rain_predicted:
        for item in forecast["list"][:8]:
            if any(_is_rain(w) for w in item["weather"]):
                rain_predicted = True
                break
            if item.get("pop", 0) >= 0.5:
                rain_predicted = True
                break

    return {
        "city": city,
        "temp_c": temp_c,
        "conditions": conditions,
        "rain_now": rain_now,
        "rain_predicted": rain_predicted,
    }


def get_alert_reasons(weather):
    """Return list of human-readable reasons that warrant an email alert."""
    reasons = []
    if weather["temp_c"] > TEMP_ALERT_C:
        reasons.append(f"High temperature: {weather['temp_c']:.1f}°C (threshold: {TEMP_ALERT_C}°C)")
    if weather["rain_predicted"]:
        if weather["rain_now"]:
            reasons.append("Rain is currently falling")
        else:
            reasons.append("Rain is predicted in the next 24 hours")
    return reasons


def send_email_alert(subject, body):
    """Send an alert email via SMTP (Gmail-compatible)."""
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    recipient = os.environ.get("EMAIL_RECIPIENT", sender)

    if not sender or not password:
        raise ValueError("EMAIL_SENDER and EMAIL_PASSWORD environment variables must be set")

    # Gmail app passwords are 16 chars; Google often displays them with spaces.
    password = password.replace(" ", "")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(
            "Gmail login failed. Set EMAIL_PASSWORD to a Gmail App Password "
            "(not your normal password). Enable 2-Step Verification, then create one at "
            "https://myaccount.google.com/apppasswords — use the same Gmail address as EMAIL_SENDER."
        ) from e


def build_report(weather, reasons):
    """Build the log/artifact text for this run."""
    today = date.today().strftime("%A, %d %B %Y")
    status = "ALERT TRIGGERED" if reasons else "No alert needed"

    lines = [
        "=====================================",
        "PULSE - Weather Alert",
        today,
        "=====================================",
        "",
        f"CITY:       {weather['city']}",
        f"TEMP:       {weather['temp_c']:.1f}°C",
        f"CONDITIONS: {weather['conditions']}",
        f"RAIN NOW:   {'Yes' if weather['rain_now'] else 'No'}",
        f"RAIN SOON:  {'Yes' if weather['rain_predicted'] else 'No'}",
        "",
        f"STATUS: {status}",
    ]

    if reasons:
        lines.append("")
        lines.append("ALERT REASONS")
        for reason in reasons:
            lines.append(f"- {reason}")

    lines.append("")
    lines.append("=====================================")
    return "\n".join(lines)


def run():
    """Main entry point. Called by GitHub Actions."""
    weather = fetch_weather()
    reasons = get_alert_reasons(weather)
    report = build_report(weather, reasons)

    print(report)

    if reasons:
        subject = f"Weather Alert: {weather['city']}"
        body = report
        send_email_alert(subject, body)
        print("Alert email sent.")

    with open("daily_summary.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("Pulse ran successfully.")


if __name__ == "__main__":
    run()
