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

    Rel_D(occupant, thermal_grace, "Provides feedback & Views dashboard")
    Rel_U(researcher, thermal_grace, "Monitors metrics")
    
    Rel_Right(sensor_nodes, thermal_grace, "Publishes sensor data", "MQTT")
    Rel_Left(buienradar, thermal_grace, "Polls weather data", "HTTPS")
    Rel_Left(github_llm, thermal_grace, "Sends prompts / Receives advice", "HTTPS")

    Lay_R(buienradar, github_llm)
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
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

    Rel_D(occupant, feedback_app, "Submits comfort details")
    Rel_D(occupant, dashboard, "Views personalized insights")

    Rel_L(feedback_app, filesystem, "Writes user context", "CSV")
    Rel_R(dashboard, filesystem, "Reads user context / Writes sensor history", "CSV")

    Rel_R(sensor_nodes, dashboard, "Streams telemetry", "MQTT")
    Rel_L(buienradar, dashboard, "Weather data", "HTTPS")
    Rel_R(github_llm, dashboard, "AI advice", "HTTPS")

    Lay_D(filesystem, sensor_nodes)
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

    Rel_D(app_entry, mqtt_service, "Starts thread")
    Rel_D(app_entry, weather_service, "Starts thread")
    Rel_L(app_entry, state_manager, "Reads latest snapshot")
    Rel_R(app_entry, ui_pages, "Renders UI")

    Rel_D(mqtt_service, state_manager, "Updates shared state")
    Rel_L(mqtt_service, mqtt_broker, "Subscribes to sensors")
    Rel_R(mqtt_service, comfort_calc, "Calculates metrics for new data")

    Rel_D(weather_service, state_manager, "Updates weather state")
    Rel_L(weather_service, buienradar, "Polls JSON")

    Rel_D(state_manager, metrics_csv, "Appends row")

    Rel_D(ui_pages, state_manager, "Gets snapshot data")
    Rel_R(ui_pages, comfort_calc, "Calculates view-specific metrics")
    Rel_D(ui_pages, llm_utils, "Invokes AI assistant")

    Rel_U(comfort_calc, feedback_csv, "Reads user context")
    Rel_R(llm_utils, github_llm, "POST prompt")

    Lay_R(mqtt_broker, app_entry)
    Lay_R(app_entry, buienradar)
    Lay_D(metrics_csv, llm_utils)
    
    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```
