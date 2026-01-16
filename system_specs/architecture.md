# Thermal Grace - System Architecture

This document describes the architecture of the **Thermal Grace** Perceived Thermal Comfort system using the [C4 model](https://c4model.com/).

## Level 1: System Context Diagram
This diagram shows the high-level system boundary and its interactions with users and external entities.

```mermaid
C4Context
    title System Context Diagram for Thermal Grace

    Person(researcher, "Researcher", "Analyzes thermal comfort data and insights")
    Person(occupant, "Occupant", "Provides feedback and receives comfort advice")

    System(thermal_grace, "Thermal Grace System", "Collects sensor data, calculates comfort metrics, and provides adaptive recommendations")

    System_Ext(sensor_nodes, "Sensor Nodes", "RPi Pico/Zero nodes streaming Environment, CO2, and Radar data via MQTT")
    System_Ext(buienradar, "Buienradar API", "Provides external weather conditions")
    System_Ext(github_llm, "GitHub Models API", "Provides LLM inference for personalized advice")

    Rel(occupant, thermal_grace, "Provides feedback & Views dashboard")
    Rel(researcher, thermal_grace, "Monitors metrics")
    
    Rel(sensor_nodes, thermal_grace, "Publishes sensor data", "MQTT")
    Rel(thermal_grace, buienradar, "Polls weather data", "HTTPS")
    Rel(thermal_grace, github_llm, "Sends prompts / Receives advice", "HTTPS")
```

## Level 2: Container Diagram
This diagram zooms into the **Thermal Grace System** to show its high-level executable units and data stores.

```mermaid
C4Container
    title Container Diagram for Thermal Grace

    Person(occupant, "Occupant", "Visitor or building user")
    
    System_Ext(sensor_nodes, "Sensor Nodes", "MQTT Publishers")
    System_Ext(buienradar, "Buienradar API", "Weather Data")
    System_Ext(github_llm, "GitHub Models API", "LLM Intelligence")

    Boundary(c1, "Thermal Grace System") {
        Container(dashboard, "Data Handler Dashboard", "Python, Streamlit", "Main application: aggregates data, computes PMV/PPD, visualizes metrics, and runs background services.")
        Container(feedback_app, "User Feedback App", "Python, Streamlit", "Standalone survey app for capturing occupant activity, clothing, and thermal sensation.")
        
        ContainerDb(filesystem, "File Storage", "CSV Files", "Persists sensor logs (live_metrics.csv) and user feedback (responses.csv).")
    }

    Rel(occupant, feedback_app, "Submits comfort details")
    Rel(occupant, dashboard, "Views personalized insights")

    Rel(feedback_app, filesystem, "Writes user context", "CSV")
    Rel(dashboard, filesystem, "Reads user context / Writes sensor history", "CSV")

    Rel(sensor_nodes, dashboard, "Streams telemetry", "MQTT")
    Rel(dashboard, buienradar, "Fetches weather", "HTTPS")
    Rel(dashboard, github_llm, "Generates recommendations", "HTTPS")
```

## Level 3: Component Diagram (Dashboard)
This diagram details the internal components of the **Data Handler Dashboard** container.

```mermaid
C4Component
    title Component Diagram - Data Handler Dashboard

    Container(feedback_csv, "responses.csv", "File", "User feedback source")
    Container(metrics_csv, "live_metrics.csv", "File", "Sensor history log")
    System_Ext(mqtt_broker, "MQTT Broker", "Message Bus")
    System_Ext(buienradar, "Buienradar API", "Weather Service")
    System_Ext(github_llm, "GitHub Models API", "LLM Service")

    Container_Boundary(dashboard_boundary, "Dashboard Application") {
        Component(app_entry, "Streamlit App Controller", "streamlit_app.py", "Main entry point. Handles navigation, UI rendering loops, and thread startup.")
        
        Component(mqtt_service, "MQTT Service", "mqtt_service.py", "Background thread. Subscribes to topics, parses payloads, and updates state.")
        Component(weather_service, "Weather Service", "weather_service.py", "Background thread. Polls external API periodically and updates state.")
        
        Component(state_manager, "State Manager", "state.py", "Thread-safe singleton. Manages current snapshot and handles CSV persistence logic.")
        Component(comfort_calc, "Comfort Model", "comfort_calc.py", "Domain Logic. Calculates PMV, PPD, UTCI, and aggregates multi-user results.")
        Component(llm_utils, "LLM Client", "llm_utils.py", "Facade. Builds prompts from context and communicates with AI provider.")
        
        Component(ui_pages, "UI Components", "uicomponents/*.py", "Renderers for specific views: Live Metrics, Multi-User, LLM Assistant.")
    }

    Rel(app_entry, mqtt_service, "Starts thread")
    Rel(app_entry, weather_service, "Starts thread")
    Rel(app_entry, state_manager, "Reads latest snapshot")
    Rel(app_entry, ui_pages, "Renders")

    Rel(mqtt_service, mqtt_broker, "Subscribes to sensors")
    Rel(mqtt_service, comfort_calc, "Calculates metrics for new data")
    Rel(mqtt_service, state_manager, "Updates shared state")

    Rel(weather_service, buienradar, "Polls JSON")
    Rel(weather_service, state_manager, "Updates weather state")

    Rel(state_manager, metrics_csv, "Appends row")

    Rel(ui_pages, state_manager, "Gets snapshot data")
    Rel(ui_pages, comfort_calc, "Calculates view-specific metrics")
    Rel(ui_pages, llm_utils, "Invokes AI assistant")

    Rel(comfort_calc, feedback_csv, "Reads user context")
    Rel(llm_utils, github_llm, "POST prompt")
```
