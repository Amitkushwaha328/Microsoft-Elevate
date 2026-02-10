CityWatch AI – Intelligent Public Infrastructure Complaint System

PROJECT OVERVIEW
CityWatch AI is an AI-powered, cloud-based civic complaint intelligence system built using Streamlit and Microsoft Azure. The system allows citizens to submit public infrastructure complaints with optional image evidence and enables authorities to analyze, prioritize, and monitor issues through an intelligent admin command center. The project focuses on decision support and early issue detection rather than direct complaint resolution.

KEY FEATURES
• Citizen complaint submission with image upload
• Auto-generated tracking ID for each complaint
• Complaint status tracking for users
• Secure admin login with role-based access
• Automatic problem type detection (Water, Road, Electricity, Sanitation, Internet)
• Latest-first and priority-based complaint listing
• State-wise and city-wise complaint analysis
• Image evidence viewing from private cloud storage
• AI-assisted severity scoring and issue prioritization
• Human-readable AI explanations for administrators

AI & INTELLIGENCE
The system uses AI-driven text analysis and rule-based NLP logic to automatically understand the type of problem reported by citizens. Similar complaints are grouped together, abnormal spikes are detected based on time and location, and priority levels are assigned using severity, frequency, and recency. The AI layer assists administrators in identifying urgent and recurring issues while keeping humans in control of final decisions.

CLOUD & SECURITY
• Microsoft Azure Blob Storage is used for complaint data and image evidence
• Structured data and images are stored in separate private containers
• Account key authentication is used for secure read/write operations
• SAS tokens are used for read-only image access in the admin panel
• Sensitive credentials are managed using environment variables and Streamlit Cloud secrets
• No secrets or real data are stored in the GitHub repository

TECH STACK
• Python
• Streamlit
• Pandas, NumPy
• Plotly
• Microsoft Azure Blob Storage
• Azure SDK for Python

PROJECT STRUCTURE

CityWatch-AI/
├── App.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│ └── complaints_master_sample.csv
└── notebooks/
└── Index.ipynb

DEPLOYMENT
The application is designed to run locally and on Streamlit Cloud. Deployment requires setting Azure credentials and admin password using Streamlit Cloud secrets. The main application file is App.py, and all dependencies are listed in requirements.txt.

INTERNSHIP CONTEXT
This project was developed as an advanced AI and cloud internship project aligned with Microsoft Elevate and AICTE-style requirements. It demonstrates real-world system architecture, secure cloud integration, explainable AI usage, and role-based application design.

AUTHOR
Amit Kushwaha
B.Tech – Artificial Intelligence & Machine Learning
