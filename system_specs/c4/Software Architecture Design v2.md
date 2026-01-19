# Thermal Grace — Software Architecture Design

> **VHUB Comfort-as-a-Service IoT System**

**Author:** Artur Kraskov  
**Semester:** 7  
**Course:** ICT & OL, Delta — Fontys 2025-2026

---

## Table of Contents

1. [Introduction](#introduction)
2. [Software Architecture](#software-architecture)
   - [Requirements Summary](#requirements-summary)
   - [Stakeholders and Needs](#stakeholders-and-needs)
   - [C4 Diagrams](#c4-diagrams)
   - [System Inventory](#system-inventory)
3. [Quality Attributes](#quality-attributes)
   - [Security](#security)
   - [Scalability](#scalability)
4. [Constraints & Assumptions](#constraints--assumptions)
5. [Technology Choices](#technology-choices)
6. [Conclusion](#conclusion)
7. [References](#references)

---

# Introduction

This document describes the software architecture for the Thermal Grace prototype — a Comfort-as-a-Service IoT system developed for Vitality HUB.

## Background

The software design satisfies requirements derived from user stories. Related documents:
- Project plan and requirements [1-2]
- Hardware architecture [3]

---

# Software Architecture

## Requirements Summary

The system must:

| Requirement | Description |
|-------------|-------------|
| **Sensor integration** | Accumulate data from multiple wireless sensors via MQTT |
| **User feedback** | Collect occupant comfort feedback through a simple form |
| **Weather context** | Fetch outdoor conditions via external API (Buienradar) |
| **Comfort calculation** | Compute PMV/PPD values using ISO 7730 model |
| **AI recommendations** | Query LLM for analysis and actionable advice |
| **Modularity** | Add/remove sensors without breaking core functionality |

---

## Stakeholders and Needs

### Researchers (Primary)

| Need | Implementation |
|------|----------------|
| Valid/traceable measurements | All sensor data logged with timestamps to CSV |
| Reproducible computations | PyThermalComfort library with ISO 7730 model |
| Export/logging | CSV files easily exported for analysis |
| Modularity | MQTT topics decouple sensors from processing |

### Office Users (Secondary)

| Need | Implementation |
|------|----------------|
| Easy feedback input | Simple Streamlit form with dropdown selections |
| Understandable guidance | LLM provides natural language recommendations |
| Privacy | Minimal PII; anonymous UID tracking |

---

## C4 Diagrams

### Level 1 — Context

![C4 Context Diagram][image1]

*High resolution: [Google Drive](https://drive.google.com/file/d/1KD9IUZkiTKQc9INoakWdf351lLHdJIYY)*

Shows the Thermal Grace system in context with external actors: sensor nodes, weather API, LLM API, and users.

### Level 2 — Containers

![C4 Container Diagram][image2]

*High resolution: [Google Drive](https://drive.google.com/file/d/1ZVjtGnIlWeJ-tD-7tcnDyWlDyyZe6cdQ)*

Shows the main containers: MQTT broker, Streamlit dashboard, feedback app, and data storage.

### Level 3 — Components

![C4 Component Diagram][image3]

*High resolution: [Google Drive](https://drive.google.com/file/d/1mlP2k4rSQP9jo3I0DwF56UoDrmGmeA2P)*

Shows internal components of the Streamlit dashboard: MQTT receiver, comfort calculator, LLM integration, and UI modules.

### Key Implementation Details

| Feature | How It Works |
|---------|--------------|
| **Sensor onboarding** | New sensors publish to MQTT topics; dashboard subscribes and parses automatically |
| **Comfort metrics** | PyThermalComfort computes PMV/PPD and UTCI from sensor + user inputs |
| **Data logging** | All readings saved to `.csv` files for long-term analytics |
| **Multi-user tracking** | Each feedback entry has a UID; system aggregates today's responses for group-level insights |

---

## System Inventory

### Existing Systems (External Dependencies)

| System | Role | Protocol |
|--------|------|----------|
| **Mosquitto MQTT Broker** | Message transport for sensor data | MQTT |
| **Buienradar API** | Dutch weather data provider | REST/HTTP |
| **GitHub Models API** | LLM for comfort analysis | REST/HTTP |
| **PyThermalComfort** | ISO 7730 PMV/PPD calculation | Python library |

### Custom-Built Components

| Component | Description |
|-----------|-------------|
| **Thermal Grace Dashboard** | Streamlit app with live metrics, comfort display, LLM chat |
| **MQTT Ingest Logic** | Topic parsing, JSON validation, state snapshot updates |
| **User Feedback App** | Streamlit survey form with CSV storage |
| **Sensor Firmware** | MicroPython/C++ code for Pico 2 W nodes |

---

# Quality Attributes

## Security

### Threat Model

| Threat | Risk | Mitigation |
|--------|------|------------|
| **Spoofed sensor data** | Attacker publishes fake MQTT messages | Client ID enforcement; LAN-only broker; JSON validation |
| **API token leakage** | Exposed credentials for LLM/weather APIs | Tokens in `secrets.toml` (git-ignored); never logged |
| **User data exposure** | Feedback CSV contains personal context | Minimal PII; file permissions; local storage only |
| **Dashboard hijacking** | Unauthorized UI access | LAN-only; optional reverse proxy with auth |

### Security Controls

| Area | Implementation |
|------|----------------|
| **MQTT** | Broker binds to `192.168.50.x`; unique client IDs per sensor; payload validation |
| **Credentials** | Stored in `.streamlit/secrets.toml`; loaded via `st.secrets` |
| **Rate Limiting** | LLM calls gated by "Ask Assistant" button |
| **Logging** | Secrets redacted; provenance (topic + timestamp) recorded |

> ⚠️ **Production note:** TLS is disabled on the MQTT broker. Enable TLS and authentication for deployments outside trusted networks.

---

## Scalability

### Growth Scenarios

| Growth Vector | Current State | Scaling Path |
|---------------|---------------|--------------|
| **More sensors** | 3 nodes, 3 topics | Add MQTT topics — no code changes needed |
| **Higher frequency** | ~10 Hz radar, 0.4 Hz CO₂ | MQTT handles thousands of msg/sec |
| **More users** | Single dashboard | Multiple Streamlit instances + load balancer |
| **Larger datasets** | CSV files (KB–MB) | Migrate to InfluxDB/TimescaleDB |

### Current Optimizations

| Optimization | Benefit |
|--------------|---------|
| **Last-N row fetching** | Dashboard reads only recent rows, avoiding full-file scans |
| **LLM response caching** | Avoids redundant API calls for same context |
| **UID-based aggregation** | Filters unique users before building LLM prompt |

### Evolution Path

```
Prototype                    →    Production
────────────────────────────────────────────
CSV files                    →    InfluxDB / TimescaleDB
Single Streamlit instance    →    Multiple instances + shared DB
Local MQTT broker            →    Managed broker (HiveMQ Cloud)
Manual deployment            →    Docker Compose / Kubernetes
```

---

# Constraints & Assumptions

| Constraint | Impact | Workaround |
|------------|--------|------------|
| **Single-host deployment** | All services on one Raspberry Pi 5 | Sufficient for MVP; scale-out needs DB separation |
| **Internet dependency** | Weather + LLM APIs require connectivity | Graceful degradation; comfort calc works offline |
| **Wi-Fi reliability** | Data lost if network drops | Sensors auto-reconnect; no local buffering yet |
| **Hardcoded assumptions** | Air speed = 0.1 m/s; met/clo fallbacks | Acceptable for office; user feedback overrides |

---

# Technology Choices

| Technology | Choice | Why |
|------------|--------|-----|
| **Messaging** | MQTT (Mosquitto) | Lightweight pub/sub; perfect for IoT; decouples sensors from consumers |
| **Dashboard** | Streamlit | Python-native; fast iteration; great for research prototypes |
| **Storage** | CSV files | Human-readable; easy export; transparent debugging |
| **Comfort Model** | PyThermalComfort | ISO 7730 compliant; open-source; well-documented |
| **LLM** | GitHub Models API | Free tier; no GPU needed; simple REST integration |
| **Weather** | Buienradar API | Free; Dutch data; simple JSON responses |

### Trade-offs

| Decision | ✅ Benefit | ⚠️ Trade-off |
|----------|-----------|--------------|
| CSV over database | Simple, portable | Not for high-frequency queries |
| External LLM | No infrastructure | Requires internet; rate limits |
| Streamlit over React | Faster development | Less UI flexibility |
| No MQTT TLS | Simpler setup | Must stay on trusted LAN |

---

# Conclusion

The software architecture delivers a functional Comfort-as-a-Service prototype:

| Goal | Achievement |
|------|-------------|
| **Real-time monitoring** | MQTT streams data; dashboard shows live metrics |
| **Thermal comfort** | PMV/PPD computed from sensors + user input |
| **AI recommendations** | LLM analyzes conditions and provides advice |
| **Multi-user support** | UID-based feedback enables group insights |
| **Modularity** | New sensors integrate via MQTT — no core changes |
| **Research-friendly** | CSV logging enables data export and analysis |

### Future Directions

- 📊 **Personalized models:** Train comfort predictions from historical feedback
- 🗄️ **Database migration:** Move to InfluxDB for time-series performance
- 📱 **Mobile app:** Replace desktop form with mobile-friendly feedback
- 🔮 **Predictive comfort:** Forecast conditions based on weather trends

---

# References

1. Kraskov A., Kaszuba B., (2025), *Vitality HUB Perceived Thermal Comfort | Project Plan*, FHICT Delta. [Online](https://drive.google.com/file/d/1BXHXlD4_SPatpJrU1mDwF0ZKnESl2W_U)

2. Kraskov A., Kaszuba B., (2025), *Vitality HUB Perceived Thermal Comfort | Requirements*, FHICT Delta. [Online](https://drive.google.com/file/d/1NooyuNM97BFz3jYOX2aPSRkbFZ7f5yJF)

3. Kraskov A., (2025), *Thermal Grace — Hardware Architecture Design*, FHICT Delta. [Online](https://drive.google.com/file/d/1sWcylxS85DdrUbDKQ6F5CqS8aSHxkFRN)
