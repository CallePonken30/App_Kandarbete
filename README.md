# Workflow Automation for Bio-Analytical Data (Bachelor Thesis)

This repository contains a simplified and sanitized version of the software developed as part of my bachelor thesis in collaboration with Mercodia AB.

The project focused on automating manual data-handling workflows in a regulated bio-analytical environment, with an emphasis on data integrity, validation, and usability for non-technical users.

## Project Overview

Bio-analytical laboratories often receive customer data in heterogeneous spreadsheet formats that must be converted into strict templates before being imported into Laboratory Information Management Systems (LIMS). These steps are typically manual, time-consuming, and error-prone.

To address this, I designed and implemented a desktop application that:
- Ingests CSV and Excel files from external sources
- Validates structure and required fields
- Transforms data into LIMS-compatible formats
- Performs automated quality control checks

The application was developed as a local tool to avoid storage of sensitive data and to comply with regulatory and data integrity requirements.

## Key Features

- Flexible ingestion of CSV and Excel files
- Configurable column mapping to a fixed target schema
- Automated validation and quality control checks
- Clear error reporting for missing or inconsistent data
- JavaScript-based frontend enabling use by non-technical staff

## Technologies Used

- Python (data processing and backend logic)
- Pandas / NumPy (data handling)
- JavaScript (React-based frontend)
- Flask (local backend API)
- Electron (desktop application wrapper)


## Author

Carl Humborg  
Bachelor Thesis, Uppsala University
