# Master of Orion 2 - UPV/EHU

Reimplementation of **Master of Orion 2**, developed as a university project at **UPV/EHU**. The project recreates the core experience of the classic turn-based 4X strategy game while incorporating a modern web-based architecture and an AI service.

## Features

* Turn-based 4X strategy gameplay
* Galaxy and empire management
* Fleet and combat management
* Resource and planet management
* AI-assisted game functionality
* Separate frontend, backend and AI service
* Docker-based development environment
* Modular architecture designed for future expansion

## Screenshots

Screenshots of the application will be added here.

## Tech Stack

* **Frontend:** Web-based frontend
* **Backend:** Backend API and game logic
* **AI Service:** Dedicated service for AI-related functionality
* **Docker:** Containerized development environment
* **JSON:** Game and fleet data management

## How to Run

Clone the repository:

```bash
git clone https://github.com/Ivangb-626/Master-of-Orion-2---UPV-EHU.git
cd Master-of-Orion-2---UPV-EHU
```

Make sure Docker and Docker Compose are installed, then start the project with:

```bash
docker compose up --build
```

For more detailed execution instructions, check `Ejecutar.txt` in the repository.

## Architecture

The project is divided into several independent components:

```text
Master-of-Orion-2---UPV-EHU/
│
├── frontend/        # User interface
├── backend/         # Backend and game logic
├── ai-service/      # AI-related functionality
│
├── MDs/             # Project documentation
├── fleets.json      # Fleet data
├── docker-compose.yml
│
├── SPECS.md
├── REGRESSION_AUDIT_REPORT.md
└── TODO_IMPROVEMENTS.md
```

This separation allows the frontend, backend and AI functionality to evolve independently while communicating through defined interfaces.

## Future Improvements

* Expand and refine gameplay mechanics
* Improve AI decision-making
* Add more advanced strategic behaviors
* Improve the user interface and overall UX
* Expand fleet and combat systems
* Add more comprehensive testing
* Improve performance and scalability
* Add additional documentation
* Introduce new gameplay features inspired by the original Master of Orion 2
