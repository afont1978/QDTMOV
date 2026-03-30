from __future__ import annotations

DOMAIN_TEMPLATES = {
    "none": {
        "label": "None",
        "mode": None,
        "complexity": None,
        "trigger_events": [],
        "disturbances": {},
        "expected_subproblems": [],
        "recommended_interventions": [],
        "kpis": [],
    },
    "traffic_corridor": {
        "label": "Traffic corridor",
        "mode": "traffic",
        "complexity": "high",
        "trigger_events": ["demand_spike", "bus_bunching"],
        "disturbances": {"corridor_flow_multiplier": 1.18, "bus_headway_pressure_add": 0.12},
        "expected_subproblems": ["signal_coordination_problem", "bus_priority_problem"],
        "recommended_interventions": ["activate coordinated signal plan", "increase bus priority level"],
        "kpis": ["network_speed_index", "corridor_reliability_index", "bus_bunching_index"],
    },
    "safety_school": {
        "label": "Safety / school area",
        "mode": "safety",
        "complexity": "high",
        "trigger_events": ["school_peak", "rain_event"],
        "disturbances": {"ped_flow_multiplier": 1.30, "visibility": 0.75},
        "expected_subproblems": ["pedestrian_protection_problem", "risk_mitigation_problem"],
        "recommended_interventions": ["activate pedestrian protection mode", "speed mitigation around hotspot"],
        "kpis": ["risk_score", "near_miss_index", "pedestrian_exposure"],
    },
    "logistics_curb": {
        "label": "Logistics / curb",
        "mode": "logistics",
        "complexity": "high",
        "trigger_events": ["delivery_wave", "illegal_curb_occupation"],
        "disturbances": {"delivery_pressure_add": 0.30, "illegal_parking_pressure_add": 0.20},
        "expected_subproblems": ["curb_allocation_problem", "delivery_slot_problem"],
        "recommended_interventions": ["increase enforcement level", "reallocate curb slots"],
        "kpis": ["delivery_queue", "curb_occupancy_rate", "illegal_curb_occupancy_rate"],
    },
    "gateway_access": {
        "label": "Gateway access",
        "mode": "gateway",
        "complexity": "high",
        "trigger_events": ["gateway_surge", "incident"],
        "disturbances": {"gateway_surge_add": 0.35, "corridor_flow_multiplier": 1.10},
        "expected_subproblems": ["gateway_resource_problem", "multimodal_redispatch_problem"],
        "recommended_interventions": ["activate metering", "taxi/VTC staging", "gateway diversion plan"],
        "kpis": ["gateway_delay_index", "network_speed_index", "curb_occupancy_rate"],
    },
    "event_release": {
        "label": "Event release",
        "mode": "event",
        "complexity": "very_high",
        "trigger_events": ["event_release", "bus_bunching", "rain_event"],
        "disturbances": {"corridor_flow_multiplier": 1.22, "ped_flow_multiplier": 1.35, "bus_headway_pressure_add": 0.18},
        "expected_subproblems": ["event_release_rebalancing_problem", "bus_priority_problem"],
        "recommended_interventions": ["activate post-event dispersal plan", "increase bus priority", "temporary diversion on saturated approaches"],
        "kpis": ["network_speed_index", "bus_bunching_index", "gateway_delay_index"],
    },
}

SHOCK_LIBRARY = {
    "rain_shock": {
        "label": "Rain shock",
        "events": ["rain_event"],
        "disturbances": {"rain_intensity": 0.45, "visibility": 0.70},
        "note_suffix": "Includes wet-weather stress and reduced visibility.",
    },
    "incident_chain": {
        "label": "Incident chain",
        "events": ["incident"],
        "disturbances": {"corridor_flow_multiplier": 1.10},
        "note_suffix": "Includes local incident pressure and corridor degradation.",
    },
    "delivery_wave": {
        "label": "Delivery wave",
        "events": ["delivery_wave"],
        "disturbances": {"delivery_pressure_add": 0.35},
        "note_suffix": "Includes delivery surge and curbside saturation.",
    },
    "gateway_surge": {
        "label": "Gateway surge",
        "events": ["gateway_surge"],
        "disturbances": {"gateway_surge_add": 0.40},
        "note_suffix": "Includes strategic access overload at gateway nodes.",
    },
    "school_peak": {
        "label": "School peak",
        "events": ["school_peak"],
        "disturbances": {"ped_flow_multiplier": 1.35},
        "note_suffix": "Includes vulnerable-user peak pressure around access crossings.",
    },
    "event_release": {
        "label": "Event release",
        "events": ["event_release"],
        "disturbances": {"ped_flow_multiplier": 1.25, "corridor_flow_multiplier": 1.15},
        "note_suffix": "Includes synchronized multimodal release after a major event.",
    },
}

DEMO_PRESETS = {
    "none": {
        "label": "None",
        "template": "none",
        "shocks": [],
    },
    "traffic_peak_demo": {
        "label": "Traffic peak demo",
        "template": "traffic_corridor",
        "shocks": ["incident_chain"],
    },
    "wet_school_safety_demo": {
        "label": "Wet school safety demo",
        "template": "safety_school",
        "shocks": ["rain_shock", "school_peak"],
    },
    "logistics_overload_demo": {
        "label": "Logistics overload demo",
        "template": "logistics_curb",
        "shocks": ["delivery_wave"],
    },
    "gateway_departure_demo": {
        "label": "Gateway departure demo",
        "template": "gateway_access",
        "shocks": ["gateway_surge"],
    },
    "event_release_demo": {
        "label": "Event release demo",
        "template": "event_release",
        "shocks": ["event_release", "rain_shock"],
    },
}
