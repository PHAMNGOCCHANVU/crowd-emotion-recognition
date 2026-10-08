def get_alert(result, threshold=0.50):
    distribution = result.get("emotion_distribution", {})
    risk = distribution.get("Sad", 0.0) + distribution.get("Surprised", 0.0)

    if risk >= threshold + 0.20:
        return "CRITICAL", risk, "High abnormal-emotion density"
    if risk >= threshold:
        return "WARNING", risk, "Elevated abnormal-emotion density"
    return "NORMAL", risk, "No abnormal signal"
