# AI Allocation Test Scenarios

Use these JSON bodies to test how the Cloud AI responds to different environmental conditions.

## Scenario 1: The "Worst Case" (Dirty Grid & Night)
**Context:** It's night (low solar), and the grid is very dirty (coal/gas heavy). The AI should stop non-essential tasks to save carbon.

**Request Body:**
```json
{
    "mode": "allocate",
    "solar": 0.0,
    "carbon": 600.0,
    "queue": 50,
    "battery": 20
}
```

**Expected Response:**
```json
{
    "source": "Cloud AI Allocator",
    "action_id": 2,
    "action_label": "🛑 Defer (Hold Load)",
    "reasoning": "Carbon: 600.0, Solar: 0.0"
}
```
*Why? Logic triggers `if carbon > 500 and solar < 50`.*

---

## Scenario 2: The "Best Case" (Sunny Day)
**Context:** It's noon, solar energy is abundant. The AI should process everything immediately because energy is free and green.

**Request Body:**
```json
{
    "mode": "allocate",
    "solar": 450.0,
    "carbon": 300.0,
    "queue": 150,
    "battery": 90
}
```

**Expected Response:**
```json
{
    "source": "Cloud AI Allocator",
    "action_id": 0,
    "action_label": "🚀 Boost (Process All)",
    "reasoning": "Carbon: 300.0, Solar: 450.0"
}
```
*Why? Logic triggers `elif solar > 350`.*

---

## Scenario 3: Critical Backlog (Must Run)
**Context:** The queue is overflowing. Even though it's not perfect weather, we must process tasks to avoid SLA violations.

**Request Body:**
```json
{
    "mode": "allocate",
    "solar": 30.0,
    "carbon": 400.0,
    "queue": 500,
    "battery": 50
}
```

**Expected Response:**
```json
{
    "source": "Cloud AI Allocator",
    "action_id": 0,
    "action_label": "🚀 Boost (Process All)",
    "reasoning": "Carbon: 400.0, Solar: 30.0"
}
```
*Why? Logic triggers `elif queue > 450 ...`.*

---

## Scenario 4: Standard Day (Eco Balance)
**Context:** Average conditions. Solar is moderate, carbon is average. The AI (or Random Fallback in absence of ONNX) will decide.

**Request Body:**
```json
{
    "mode": "allocate",
    "solar": 150.0,
    "carbon": 250.0,
    "queue": 100,
    "battery": 60
}
```

**Expected Response:**
*(Varies: Could be Eco, Boost, or Defer depending on the Random Exploration or ONNX model)*
```json
{
    "source": "Cloud AI Allocator",
    "action_id": 1,
    "action_label": "🌱 Eco (Green Only)",
    "reasoning": "Carbon: 250.0, Solar: 150.0"
}
```
