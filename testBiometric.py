class BiometricInput:
  def __init__(self, heart_rate, hrv, skin_temp, movement, spo2, eda, env_temp):
    self.heart_rate = heart_rate
    self.hrv = hrv
    self.skin_temp = skin_temp
    self.movement = movement
    self.spo2 = spo2
    self.eda = eda
    self.env_temp = env_temp


def detect_state(data: BiometricInput) -> str:
  hr = data.heart_rate
  hrv = data.hrv
  temp = data.skin_temp
  move = data.movement.lower()
  spo2 = data.spo2
  eda = data.eda
  env = data.env_temp

  if 100 <= hr <= 130 and 10 <= hrv <= 35 and 31.5 <= temp <= 32.5 and "tremor" in move and 90 <= spo2 <= 96 and 8 <= eda <= 14:
    return "😰 Anxiety Attack"
  elif 95 <= hr <= 140 and 15 <= hrv <= 40 and eda >= 10 and "sharp" in move:
    return "😡 Rage Attack"
  elif 55 <= hr <= 75 and 50 <= hrv <= 80 and 32.5 <= temp <= 34.5 and (
          "zero" in move or "gentle" in move) and spo2 > 96 and 1 <= eda <= 4:
    return "😌 Rest"
  elif 100 <= hr <= 170 and 30 <= hrv <= 50 and "strong" in move and eda >= 6:
    return "🏃‍♀️ Physical Activity"
  elif 85 <= hr <= 160 and 20 <= hrv <= 40 and "jumps" in move and 5 <= eda <= 10:
    return "💓 Sexual Activity"
  elif 85 <= hr <= 110 and 40 <= hrv <= 65 and 4 <= eda <= 7 and "tremor" in move:
    return "😍 Emotional Excitement"
  elif 70 <= hr <= 100 and 20 <= hrv <= 40 and temp < 32 and "freeze" in move:
    return "🥶 Frozen Fear"
  elif 45 <= hr <= 65 and 50 <= hrv <= 80 and 33 <= temp <= 34.5 and eda <= 3 and "zero" in move:
    return "💤 Deep Sleep"
  elif 80 <= hr <= 100 and 30 <= hrv <= 50 and 3 <= eda <= 6:
    return "🧠 Cognitive Load"
  elif 60 <= hr <= 85 and 40 <= hrv <= 60 and 2 <= eda <= 5:
    return "📺 Binge/Screen Time"
  elif 65 <= hr <= 90 and 25 <= hrv <= 45 and 2 <= eda <= 4:
    return "🧍‍♀️ Loneliness"
  elif temp > 35.5 and 5 <= eda <= 9:
    return "🥵 Fever/Infection"
  elif 90 <= hr <= 120 and hrv < 40 and spo2 < 93:
    return "🫁 Shortness of Breath"
  elif 60 <= hr <= 75 and 30 <= hrv <= 50 and 2 <= eda <= 4:
    return "😴 Fatigue"
  else:
    return "🤷‍♂️ Unknown State"


def test_detect_state():
  test_cases = [
    # מנוחה
    (BiometricInput(60, 70, 33, "zero", 97, 3, 24), "😌 Rest"),

    # פעילות גופנית
    (BiometricInput(150, 40, 32.8, "strong", 96, 8, 25), "🏃‍♀️ Physical Activity"),

    # התקף חרדה
    (BiometricInput(110, 20, 32, "tremor", 93, 10, 22), "😰 Anxiety Attack"),

    # התקף זעם
    (BiometricInput(120, 30, 31, "sharp", 95, 12, 23), "😡 Rage Attack"),

    # שינה עמוקה
    (BiometricInput(50, 60, 34, "zero", 97, 2, 20), "💤 Deep Sleep"),

    # חום/זיהום
    (BiometricInput(90, 35, 36, "minimal", 96, 7, 22), "🥵 Fever/Infection"),

    # קוצר נשימה
    (BiometricInput(100, 30, 31.8, "flat breaths", 90, 6, 21), "🫁 Shortness of Breath"),

    # לא מזוהה
    (BiometricInput(40, 10, 30, "random", 80, 0, 15), "🤷‍♂️ Unknown State"),
  ]

  for i, (input_data, expected) in enumerate(test_cases):
    result = detect_state(input_data)
    assert result == expected, f"Test case {i + 1} failed: got {result}, expected {expected}"
    print(f"Test case {i + 1} passed: {result}")


test_detect_state()


class BiometricInput:
  def __init__(self, heart_rate, hrv, skin_temp, movement, spo2, eda, env_temp):
    self.heart_rate = heart_rate
    self.hrv = hrv
    self.skin_temp = skin_temp
    self.movement = movement
    self.spo2 = spo2
    self.eda = eda
    self.env_temp = env_temp


def test_detect_state():
  test_cases = [
    # מנוחה
    (BiometricInput(60, 70, 33, "zero", 97, 3, 24), "😌 Rest"),

    # פעילות גופנית
    (BiometricInput(150, 40, 32.8, "strong", 96, 8, 25), "🏃‍♀️ Physical Activity"),

    # התקף חרדה
    (BiometricInput(110, 20, 32, "tremor", 93, 10, 22), "😰 Anxiety Attack"),

    # התקף זעם
    (BiometricInput(120, 30, 31, "sharp", 95, 12, 23), "😡 Rage Attack"),

    # שינה עמוקה
    (BiometricInput(50, 60, 34, "zero", 97, 2, 20), "💤 Deep Sleep"),

    # חום/זיהום
    (BiometricInput(90, 35, 36, "minimal", 96, 7, 22), "🥵 Fever/Infection"),

    # קוצר נשימה
    (BiometricInput(100, 30, 31.8, "flat breaths", 90, 6, 21), "🫁 Shortness of Breath"),

    # לא מזוהה
    (BiometricInput(40, 10, 30, "random", 80, 0, 15), "🤷‍♂️ Unknown State"),
  ]

  for i, (input_data, expected) in enumerate(test_cases):
    result = detect_state(input_data)
    assert result == expected, f"Test case {i + 1} failed: got {result}, expected {expected}"
    print(f"Test case {i + 1} passed: {result}")


test_detect_state()

