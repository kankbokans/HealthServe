**Key Problem Statement**

***“Develop an intelligent healthcare platform that streamlines medical service discovery and booking by analyzing hospital data, reviews, and healthcare metrics.***
***The system will extract and compare key parameters to help users make informed healthcare decisions.***
***The solution will feature a comprehensive comparison engine for hospitals and diagnostic centers, an automated slot booking system, and detailed information about medical tests and procedures. The platform will incorporate a user-friendly chat interface to hospital comparisons, explore healthcare metrics, and facilitate seamless appointment scheduling.”***

**Functional requirements**

1) As a user, I want to be able to compare hospitals
2) As a user, I need to be able to find doctors specialized in certain conditions
3) As a user, I need to be able to create appointments
4) As a user I need to be able to update appointments
5) As a user, I need to be able to cancel appointments
6) As a user, I need to be able to find diagnostics tests and the hospital providers for the same
7) As a user I need to be able to get accurate medical information about diseases and conditions
8) As a user, I need to be able to streamline medical service discovery by analyzing hospital data, reviews, and healthcare metrics and display it on the dashboard
9) As a user I should be able to chat in a user friendly way- to do hospital comparisions, explore healthcare metrics, and facilitate seamless appointment scheduliing

**System Features**

1) Data Processing and Analysis
   Use Cloud SQL data and check correct relationships.
2) Healthcare Provider Comparision and Recommendation
   Generate comprehensive comparison metrics across healthcare facilities
   Develop presonalized recommendation system based on user preferences and requirements
3) Appointment Management System- Real time slot availability tracking
4) Diagnostics Services Information- Maintain comprehensive test catalog with detailed descriptions

	Provide preparation guidelines for various tests

5) Interactive UI and Dashboards- Develop user-friendly interface for healthcare service exploration

**Core Objectives**

* **Implement Natural Language Processing (NLP)** – Accurately interpret and process medical terminology.
* **Develop Context-Aware Responses** – Maintain dialogue history for better interaction continuity.
* **Enable Multi-Source Integration** – Pull data from reliable medical knowledge bases.
* **Provide Real-Time Doctor and Hospital Recommendations** – Offer users relevant medical support.
* **Ensure Compliance and Ethical AI Usage** – Maintain HIPAA and GDPR compliance.

**Technical Success:**


* **Accurate Healthcare Query Processing** – Ensures correct interpretation and response generation for patient queries, including symptom checks, doctor recommendations, hospital comparisons and using MCP servers for retrieving credible medical information from sites such as NIH, PubMed, Mayo Clinic, WebMD, WHO guidelines
* **Effective Multi-Agent System Integration** – Proper implementation of ADK 2.0 new **graph workflow**  for routing between multiple agents like hospital comparison, doctor availability, and diagnostics.
* **Effective Database & SQL Query Execution** – Use Cloud SQL MCP server to connect with the database instance. Ensure correct table relationships and data validation. Also should be able to handle complex queries
* **Context Retention & Conversational Memory** – AI maintains **session history** for follow-up questions and contextual understanding in patient interactions.
* **Reliable Emergency & Diagnostics Handling** – The system should effectively provide **emergency response recommendations** and diagnostics-based insights.
* **Working Frontend for User Interaction** – **User-friendly and intuitive UI**, ensuring smooth navigation for patients and healthcare professionals.
* **System Optimization and Enhancements** – Implement **security protocols** to comply with healthcare regulations (HIPAA and GDPR). AI should be able to use tools from the MCP server to retrieve and process data.Optimize query execution speed and ensure model accuracy

**Deployment Success:**

* **Fully Functional Healthcare AI System** – End-to-end integration of AI agents, database, and UI with seamless interaction.
* **Scalability & Performance Optimization** – System should support multiple concurrent users with efficient response times.
* **Production-Ready Deployment** – Successfully containerized **and deployed on Google Agent Runtime**
* **Comprehensive Documentation** – Well-structured documentation covering **setup, API usage, agent interactions, and troubleshooting** for both **end-users and developers**.


**UI Feasibility**
**HealthSense AI follows a modular UI approach, ensuring each functionality**
**operates independently rather than being confined to a single chat window.**
**Key Features:**
**○ Sidebar Navigation: Separate modules for Hospital Comparison,**
**Patient Reviews, AI Chat Assistant, and Appointment Booking, each**
**with its own UI.**
**○ Independent Interfaces:**
**i. Comparison & Reviews: Uses structured tables and visual**
**insights.**
**ii. Booking System: Form-based with slot selection.**
**iii. AI Chat Assistant: Standalone for real-time queries.**
**○ User Experience:**
**i. Multi-Window Design: Ensures smooth navigation and better**
**usability.**
**ii. Scalable & Responsive: Supports future integrations like video**
**consultations and insurance checks**

**Frontend**
![][image1]

**Example Queries and Outputs**

| User query | System Response |
| :---- | :---- |
| Find available doctors for a dermatology consultation this week. | Returns doctor availability schedules and booking links. |
| What hospitals specialize in cardiology near me? | Displays a list of nearby hospitals with cardiology departments. |
| Where is the nearest 24/7 emergency hospital? | Provides emergency hospital locations with estimated response times. |
| What tests should I take for persistent headaches? | Suggests relevant lab tests and possible causes. |
| Which hospital has good medical imaging? | Lists hospitals with top-rated medical imaging services. |
| "Show slots for Dr. Lee."  | Displays available appointment slots for Dr.Lee. |
| Any ambulance available at 94404? | Provides real-time ambulance availability in the given zip code |
| "What would be the preparation instructions for cancer screening?" | Returns standard preparation guidelines for cancer screening procedures |
