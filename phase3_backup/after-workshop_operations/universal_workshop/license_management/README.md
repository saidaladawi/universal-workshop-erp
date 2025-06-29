# Universal Workshop ERP - Licensing System

## 1. Overview

This document provides a detailed explanation of the advanced, multi-layered licensing and security system implemented in the Universal Workshop ERP. The system is designed to be robust, secure, and flexible, protecting the software's intellectual property while providing a seamless experience for legitimate clients in the Omani market.

The core philosophy is to bind each software license to both the legal business entity and the specific hardware it runs on, creating a strong, verifiable link that prevents unauthorized use and distribution.

---

## 2. Core Concepts: Multi-Layered Security Architecture

The system's strength lies in its three-tiered security approach:

### 🔹 Layer 1: Business Binding

This is the foundational layer that legally ties the license to the client's business identity. It uses official Omani business credentials for verification.

-   **Business Registration:** The license is linked to the workshop's official commercial name (both Arabic and English).
-   **Commercial License Number:** Validates against the 7-digit Omani Commercial Registration number (this is now optional but recommended).
-   **Owner's Civil ID:** Binds the license to the business owner's 8-digit Civil ID.
-   **Government Verification:** The system is designed to integrate with Omani government APIs to verify the authenticity of the provided business and owner details.

### 🔹 Layer 2: Hardware Fingerprinting

This layer technically locks the activated license to specific machines, preventing simple copy-paste piracy.

-   **Unique Identifiers:** A unique hardware "fingerprint" is generated using a combination of system components, including:
    -   CPU ID & Serial Number
    -   Motherboard Serial Number
    -   MAC Addresses of network interfaces
    -   Operating System unique identifiers
-   **Binding:** During activation, this fingerprint is permanently associated with the license key. The system will only run on hardware that matches this fingerprint.
-   **Multi-Device Support:** Licenses can be configured to allow activation on a predefined number of computers (e.g., 1 server and 5 client machines). Each machine will have its unique fingerprint registered against the license.

### 🔹 Layer 3: Cryptographic Security

This layer ensures the integrity and authenticity of the license data itself, making it tamper-proof.

-   **Signed License Keys (JWT):** The license key is a JSON Web Token (JWT) containing all the license claims (expiry, features, etc.). It is cryptographically signed using a private key held only by the developer.
-   **SHA-256 Hashing:** All sensitive data, such as the license key and hardware fingerprints, are stored as SHA-256 hashes in the database, never in plain text.
-   **Asymmetric Key Verification:** The ERP system deployed at the client's site holds a public key, which it uses to verify the signature of the license file. It cannot be used to generate or re-sign a license.

---

## 3. How It Works: The License Lifecycle

### Step 1: License Generation (Developer-Side)

This process is handled **exclusively by the development team** and is completely invisible to the end client.

1.  **Gather Client Info:** The developer collects the necessary business and owner information (see below).
2.  **Run Generation Script:** The `scripts/client_deployment/generate_license.sh` script is executed.
3.  **Create `license.json`:** The script generates a unique, signed `license.json` file. This file contains all the terms of the license (type, expiry date, allowed features, max users).
4.  **Deliver to Client:** This `license.json` file is the only artifact delivered to the client for activation.

**Required Information for Generation:**
-   **Mandatory:** Business Name (Arabic & English), Owner's Name (Arabic & English), Owner's Civil ID, Phone Number, Registration Date, Business Type.
-   **Optional:** Commercial License Number, Email Address.

### Step 2: Activation (Client-Side)

1.  **Installation:** During the initial setup of the Universal Workshop ERP, the system prompts for the `license.json` file.
2.  **Hardware Scan:** The system scans the host machine and generates its unique hardware fingerprint.
3.  **Binding:** The system validates the `license.json` signature with its public key. It then creates a `Business-Workshop-Binding` record, permanently linking the license, the business details, and the hardware fingerprint hash.

### Step 3: Validation (Continuous)

-   **Periodic Checks:** The system automatically re-validates the license integrity at regular intervals (e.g., every 24 hours) and upon certain critical actions.
-   **Verification Process:** The validation check confirms:
    1.  The `license.json` file has a valid, untampered signature.
    2.  The current machine's hardware fingerprint matches the one stored during activation.
    3.  The business details stored in the database have not been altered.
-   **Failure Protocol:** If validation fails, the system can be configured to enter a restricted, read-only mode or display persistent warnings until a valid license is restored.

---

## 4. License Types and Portability

The system supports various license models to fit different client needs.

-   **License Tiers (e.g., Basic, Professional, Enterprise):** Each tier unlocks a different set of features and has a different maximum user limit.
-   **Trial Licenses:** Can be issued with a specific time limit (e.g., 30 days) and a restricted feature set.
-   **Perpetual Licenses:** The standard license is perpetual (`is_permanent: true`) but is bound to specific hardware.

**License File (`license.json`):**
The client **must keep this file safe**. It is required for:
-   Re-installing the software on the same machine after a system wipe.
-   Activating the software on additional machines if the license permits it.

---

## 5. Key System Components

-   **DocTypes:**
    -   `Business Registration`: Stores the legal and contact information of the client's business.
    -   `Business Workshop Binding`: The core DocType that links a `Business Registration` to a specific workshop instance, license key hash, and hardware fingerprint hash.
-   **Utilities & Services:**
    -   `hardware_fingerprint.py`: Contains the logic for generating the unique hardware ID.
    -   `license_manager.py`: The central class for handling license validation, activation, and checks.
    -   `security_api.py`: Exposes secure API endpoints for license-related operations.
    -   `GovernmentVerificationService`: A utility designed to connect to external government APIs for data validation.

---

## 6. Security & Integrity

-   **Separation of Concerns:** The license **generation** system is completely separate from the **validation** system. The client-side ERP has no capability to create or alter licenses.
-   **Client Visibility:** The client **cannot** view or access the license generation mechanism. Their interaction is limited to providing the `license.json` file during setup.
-   **Data Hashing:** At no point are raw license keys or unencrypted hardware details stored permanently. Only secure hashes are used for comparison and validation. 