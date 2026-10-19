"""Verified candidate facts, including links and project technology stacks."""

from job_finder.models.personal_info import (
    CVHeader,
    PersonalEntry,
    PersonalInfo,
    PersonalProject,
)

PERSONAL_INFO = PersonalInfo(
    header=CVHeader(
        name="Abel Haro Armero",
        email="abelh2003@gmail.com",
        linkedin="https://www.linkedin.com/in/abel-haro-armero-54bb6518a",
        portfolio="https://abelharo.me",
        github="https://github.com/AbelHaro",
    ),
    summary="Computer Engineer with a background in software development, computer vision, embedded systems and IoT.",
    location="Altea / Valencia, Spain (for job ranking only; omit residence from the CV)",
    ranking_constraints=(
        (
            "For job ranking only: I have completed my degree and cannot undertake internships, "
            "becas de prácticas, or placements requiring student status or a university agreement. "
            "Exclude internship offers even if paid or advertised to graduates. Regular employment "
            "contracts and graduate programmes without these requirements remain eligible."
        ),
        "For job ranking only: my documented work experience consists of the internships listed "
        "below (less than one year in total). Academic and personal projects demonstrate skills, "
        "but must not be counted as additional years of professional employment. Do not infer "
        "continued employment after the listed end dates.",
    ),
    experience=(
        PersonalEntry(
            title="DISCA Department — Universitat Politècnica de València",
            dates="Oct. 2024 – Jul. 2025",
            subtitle="Software Development and Computer Vision Intern",
            description="Developed an academic prototype to detect defects in moving industrial objects. "
            "Prepared datasets, trained and validated models with Python, YOLO and Ultralytics. "
            "Compared architectures and datasets, optimized inference with TensorRT and deployed on "
            "NVIDIA Jetson under Linux. Evaluated accuracy, runtime performance and energy consumption.",
            technologies=(
                "Python",
                "YOLO",
                "Ultralytics",
                "TensorRT",
                "NVIDIA Jetson",
                "Linux",
            ),
        ),
        PersonalEntry(
            title="SOLTECSIS S.L.",
            dates="Jul. 2024",
            subtitle="Software Development Intern",
            description="Contributed to the open-source FWCloud project. Debugged and fixed issues "
            "during its migration from JavaScript to TypeScript, reviewing behavior affected by typing. "
            "Collaborated on refactoring to improve readability, maintainability and type safety, "
            "following project structure and team reviews.",
            technologies=("JavaScript", "TypeScript", "FWCloud"),
        ),
    ),
    education=(
        PersonalEntry(
            title="Master’s Degree in Computer and Network Engineering",
            dates="Sep. 2025 – Jul. 2026",
            subtitle="Universitat Politècnica de València",
            description="Industry 4.0 orientation. Coursework: Design of Computing Solutions with RISC-V; "
            "Optimization of Software Environments for Artificial Intelligence; Advanced Computing Systems for Industry.",
        ),
        PersonalEntry(
            title="Bachelor’s Degree in Informatics Engineering",
            dates="Sep. 2021 – Jul. 2025",
            subtitle="Universitat Politècnica de València | Average grade: 8.6/10",
            description="Coursework: Deep Learning for Industry; Automation and Robotics for Digital Industry; "
            "Embedded Systems Programming using Ada (academic experience). "
            "Bachelor’s thesis: 10/10, Matrícula de Honor.",
        ),
    ),
    projects=(
        PersonalProject(
            id="tracker",
            title="Tracker — Object Tracking Library",
            dates="In development",
            subtitle="Personal project",
            url="https://github.com/AbelHaro/tracker",
            description="Developing a C++ object tracking library with Python bindings. Implements "
            "ByteTrack and SORT to associate detections across frames and maintain object identities. "
            "Includes YOLO and OpenCV video detection/tracking integration, a NumPy interface, "
            "and unit tests for tracking algorithms and the Kalman filter.",
            technologies=(
                "C++",
                "Python",
                "ByteTrack",
                "SORT",
                "YOLO",
                "OpenCV",
                "NumPy",
            ),
        ),
        PersonalProject(
            id="url-shortener",
            title="URL Shortener",
            dates="Mar. 2026",
            subtitle="Personal full-stack project",
            url="https://github.com/AbelHaro/url-shortener",
            description="Developed an application to create, store and manage shortened URLs. "
            "Designed the user flow and communication between frontend, API and database. "
            "Implemented the frontend in React, backend in Go and persistence in PostgreSQL; "
            "containerized with Docker and deployed on Google Cloud, prioritizing maintainable architecture. "
            "Live application: https://url-shortener.abelharo.me/.",
            technologies=("React", "Go", "PostgreSQL", "Docker", "Google Cloud"),
        ),
        PersonalProject(
            id="tfg",
            title="Defect Detection with Convolutional Neural Networks",
            dates="Jul. 2025",
            subtitle="Bachelor’s thesis | Grade: 10/10, Matrícula de Honor",
            url="https://github.com/AbelHaro/TFG",
            description="Developed real-time defect detection for industrial product images. "
            "Compared YOLO models and datasets, trained and validated CNN-based detectors, "
            "optimized inference with TensorRT on NVIDIA Jetson and analyzed energy consumption "
            "to assess low-power industrial quality control applications.",
            technologies=(
                "Python",
                "CNN",
                "YOLO",
                "Ultralytics",
                "TensorRT",
                "NVIDIA Jetson",
            ),
        ),
        PersonalProject(
            id="safe-art",
            title="Safe Art — IoT Sensing and Monitoring",
            dates="Jan. 2026",
            subtitle="Academic project",
            url="https://github.com/AbelHaro/safe-art",
            description="Implemented sensor data acquisition in C++ and transmission over MQTT. "
            "Integrated devices with a web platform for real-time monitoring and alerts to protect artworks.",
            technologies=("C++", "MQTT"),
        ),
        PersonalProject(
            id="mqtt-lora",
            title="MQTT Gateway over LPWAN Networks",
            dates="Jul. 2026",
            subtitle="Master’s project",
            description="Designed and implemented an MQTT–AlLoRa–MQTT gateway with a custom "
            "MicroPython broker. Used ESP32 LilyGo T3-S3 hardware, evaluated performance through "
            "stress tests and validated end-to-end integration, exposing an LPWAN network as "
            "transparent MQTT transport.",
            technologies=(
                "MicroPython",
                "MQTT 3.1.1",
                "AlLoRa",
                "LoRa",
                "ESP32 LilyGo T3-S3",
                "Docker",
            ),
        ),
    ),
    languages=("Spanish: native", "English: B2, university-certified"),
    interests=(
        "Backend development",
        "Cloud infrastructure",
        "Maintainable software architecture",
        "Computer vision",
        "Embedded computing",
    ),
)
