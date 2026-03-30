# QDTMOV — Barcelona Mobility Control Room

Aplicación Streamlit para simulación y visualización de un control room de movilidad urbana en Barcelona, con arquitectura modular, escenarios sintéticos, gemelos digitales simplificados y lógica híbrida de decisión.

## Qué hace

La aplicación permite:

- visualizar hotspots urbanos y capas operativas
- ejecutar escenarios sintéticos de movilidad
- analizar señales y alertas
- explorar un storyboard del escenario
- revisar el estado de distintos mobility twins
- lanzar simulaciones what-if
- auditar decisiones y evolución temporal

## Estructura del proyecto

```text
.
├── .streamlit/
│   └── config.toml
├── app.py
├── requirements.txt
├── pyproject.toml
├── README.md
├── data/
│   ├── barcelona_mobility_hotspots.csv
│   ├── scenario_library.json
│   └── scenario_library_high_complexity_v2.json
├── src/
│   └── mobility_os/
│       ├── api/
│       ├── domain/
│       ├── io/
│       ├── orchestration/
│       ├── runtime/
│       ├── scenarios/
│       ├── solvers/
│       └── ui/
│           ├── app.py
│           ├── components.py
│           └── tabs/
└── tests/
