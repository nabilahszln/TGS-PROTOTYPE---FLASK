Troubleshooting Guide System (TGS) Prototype

📌 Project Overview:

This project focuses on developing a digital Troubleshooting Guide System (TGS) prototype to improve railway maintenance efficiency for Prasarana Malaysia Berhad. The system was improvised from the Streamlit version to align with the teams'goals.

🚨 Problem Statement:

The current railway troubleshooting process relies heavily on manual documents and experienced personnel. This often causes:

slow response times
inconsistent fault handling
delays during critical incidents
reduced operational efficiency
A digital troubleshooting system is needed to support faster and more standardised fault resolution.

🎯 Project Objectives:

To evelop an in-house Troubleshooting Guide System (TGS)
To support fault identification and resolve issues within five minutes
Create a user-friendly and interactive GUI for maintenance staff
🛠️ Technologies Used:

Python
Streamlit
CSS
Excel / CSV
⚙️ Methodology

Data Preparation (ETL Process)
The Minimum Operating Requirement (MOR) data was originally provided in PDF format and converted into CSV format for processing.

The data cleaning process included:

handling missing values
converting text to lowercase
removing special characters
trimming unnecessary spaces
extracting relevant text descriptions
The cleaned data was then stored in a new CSV file for further analysis and model development.

Agile Development
The system was developed using the Agile approach:

Plan
Design
Develop
Test
Deploy
Review
Continuous feedback from engineers and maintenance staff was used to improve the prototype.

🖥️ System Features:

🔐 Login & User Authentication

Ensures only authorised personnel can access the system for secure troubleshooting management.

⚙️ Equipment Selection

Users select affected equipment before troubleshooting. The system limits selection to three equipment types to maintain troubleshooting accuracy.

⚠️ Failure Scenario Selection

Users choose failure symptoms to receive targeted troubleshooting recommendations.

⏱️ Auto Start Timer & Guidelines

The system automatically starts a timer and displays step-by-step troubleshooting instructions to support faster issue resolution.

🚨 Alarm & Notification System

Notifications are triggered when troubleshooting time exceeds predefined limits to support early action.

📊 Automatic Data Logging

All troubleshooting activities are automatically recorded in Excel format for maintenance tracking and future analysis.
