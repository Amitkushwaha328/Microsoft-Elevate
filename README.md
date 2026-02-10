CityWatch AI – Intelligent Public Infrastructure Complaint System

CityWatch AI is an AI-powered, cloud-based civic complaint intelligence system that allows citizens to submit infrastructure complaints with image evidence and enables authorities to automatically analyze, prioritize, and monitor issues through an intelligent admin command center.

The project focuses on decision support, not complaint resolution, and demonstrates real-world system design using AI, cloud storage, and role-based dashboards.

🚀 Key Features
👤 Citizen Portal

Submit civic complaints with detailed descriptions

Upload photo evidence (optional but supported)

Auto-generated tracking ID for every complaint

Track complaint status using the tracking ID

Secure cloud storage of complaint data and images

🛡️ Authority (Admin) Command Center

Secure admin login with session-based access control

View all complaints in real time

Automatic AI-based issue classification (Water, Road, Electricity, Sanitation, etc.)

AI-assisted severity and priority scoring

Latest-first and priority-based sorting

State-wise and city-wise filtering

Visual evidence viewing from private Azure Blob Storage

Admin remarks and status updates (Open / In Progress / Resolved)

🧠 AI & Intelligence Layer

CityWatch AI uses an explainable AI approach:

Automatic problem classification using keyword-based NLP logic

Severity escalation based on complaint content and risk keywords

Burst detection to identify abnormal complaint spikes in a city or category

Priority scoring based on severity, frequency, and recency

Human-readable AI reasoning to support administrative decisions

The AI assists administrators in understanding patterns and urgency but does not replace human decision-making.

☁️ Cloud Architecture

Microsoft Azure Blob Storage

Private container for structured complaint data (CSV)

Private container for image evidence

Secure access

Account key–based authentication for data read/write

SAS tokens for read-only image visualization in the UI

This design follows real-world cloud security practices.

🧰 Tech Stack

Frontend & App Framework: Streamlit

Backend & Data Handling: Python, Pandas, NumPy

Visualization: Plotly

Cloud Storage: Microsoft Azure Blob Storage

AI Logic: Rule-based NLP, clustering & burst detection

Security: Environment variables & Streamlit Cloud Secrets

📂 Project Structure
