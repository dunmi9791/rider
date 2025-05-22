# Rider Odoo Module

## Summary
A comprehensive Odoo module for managing vehicle operations, including vehicle information, workshop activities (job cards, fund requests), and financial tracking (cash requisitions, expense requests).

## Description
The Rider module provides a robust solution for businesses managing a fleet of vehicles or workshop operations. Key functionalities include:
- Detailed vehicle information management (make, model, year, chassis number, registration, mileage history).
- Vehicle check-in and check-out processes.
- Workshop job card integration.
- Management of fund requests for workshop parts and services.
- Cash requisition and expense request workflows with multi-level approvals.
- Tracking of parts, expenses, and financial reconciliation.
This module integrates with core Odoo modules like Sales, Accounting, and HR to streamline operations and provide a centralized system for all vehicle-related activities.

## Key Features

The Rider module offers a range of features to streamline vehicle and workshop management:

### Vehicle Management
*   **Comprehensive Vehicle Information:** Store and manage detailed information for each vehicle, including type, make, model, registration number, manufacturing year, and chassis number.
*   **Client Association:** Link vehicles to specific clients (res.partner).
*   **Mileage Tracking:** Maintain a history of vehicle mileage with dates.
*   **Vehicle Check-in/Check-out:** Record vehicle check-ins and check-outs, noting items like jack, spare tyre, and reasons for check-out.
*   **Automated Vehicle Naming:** Generates a full vehicle name from make, model, and year.

### Workshop Operations
*   **Job Card Integration:** Designed to work with job cards (`servicerequest.rider`) for vehicle servicing.
*   **Fund Requests for Workshop:** Manage fund requests specifically for workshop activities, including parts and services.
*   **Parts Management:** Define parts (`parts.rider`) with descriptions and costs.
*   **Parts Requests:** Create and manage requests for parts needed for workshop jobs, including supplier information and cost comparison for multiple suppliers.
*   **Programme Association:** Link fund requests and parts requests to specific programmes (`programme.rider`).

### Financial Management
*   **Cash Requisitions:** Create and manage cash requisitions with details like payable to, reference document, and amount. Includes an approval workflow (Requested, Authorised, Processed, Received, Canceled).
*   **Expense Requests:** Manage staff expense requests and reconciliation. This includes:
    *   Detailed expense lines with items, descriptions, quantities, and costs.
    *   Approval workflows involving unit heads, finance, and potentially a CD (Country Director/CEO).
    *   Tracking of total requested/approved amounts, total spent, and balance.
    *   Departmental association and expense classification.
    *   Mode of disbursement (cash, transfer).
    *   Vendor association for payments.
    *   Integration with accounting for debit accounts and invoice creation.
*   **Fund Classification:** Categorize funds and expenses.
*   **Sequential Numbering:** Automatic generation of numbers for cash requisitions, expense requests, and fund requests.
*   **Email Notifications:** Utilizes Odoo's mail thread and activity mixin for notifications and tracking.

## Main Data Models

The module introduces several key data models to support its functionality:

*   **`vehicles.rider`:** Stores all information related to vehicles, including make, model, registration, mileage, and associations with clients and job cards.
*   **`vehicle.checkin`:** Manages the check-in and check-out process for vehicles.
*   **`cashrequisition.rider`:** Handles requests for cash, including approval states and linkage to fund requests or expense requests.
*   **`expense.rider`:** Manages staff expense claims, detailing requested amounts, actual expenditure, and the reconciliation process. Includes lines for individual expense items (`exprequest.expline` and `expended.expline`).
*   **`fundrequestw.rider`:** Specifically for fund requests originating from the workshop, often for parts or services related to a job card. Includes lines for parts (`fundrequest.partsline`).
*   **`partsrequest.rider`:** Manages requests for vehicle parts, allowing for comparison between different suppliers. Includes lines for requested parts (`partsrequest.partsline`).
*   **`parts.rider`:** Defines the parts that can be requested or used in workshop operations.
*   **`programme.rider`:** Represents programmes or projects that fund requests or parts requests can be associated with.
*   **`vehicletype.rider`, `vehiclemake.rider`, `vehiclemodel.rider`:** Supporting models for classifying and detailing vehicles.
*   **`fund.classification`:** Used to classify different types of funds and expenses.
*   **`expense.item`:** Defines individual items that can be claimed in expense requests.

These models are interconnected to provide a cohesive system for managing vehicle-related operations and finances.

## Installation

To install the Rider module in your Odoo instance:

1.  **Download the Module:** Obtain the `rider` module files. If you have a ZIP file, extract it.
2.  **Locate Addons Path:** Identify the `addons` directory in your Odoo installation. This is the directory where custom modules are stored.
3.  **Copy Module:** Copy the entire `rider` module folder into the `addons` directory.
4.  **Restart Odoo Server:** Restart your Odoo server for it to recognize the new module. You might need to include the `--update all` or `-u all` flag if you are running Odoo from the command line, or simply restart the Odoo service.
5.  **Activate Developer Mode:** In your Odoo interface, go to `Settings` and activate the `Developer Mode` (usually found at the bottom of the settings page or under `General Settings -> Developer Tools`).
6.  **Update Apps List:** Once in Developer Mode, go to `Apps` in the main Odoo menu. Click on `Update Apps List` (you might find this in the Apps menu itself or under a submenu). Confirm the update when prompted.
7.  **Install Module:** After the apps list has been updated, search for "Rider" or "rider" in the Apps list. You should see the module. Click the "Install" button.

The module should now be installed and its features available in your Odoo instance.

## Dependencies

This module depends on the following standard Odoo modules. Ensure these are installed in your Odoo instance before installing the Rider module:

*   `base`
*   `mail`
*   `sale_management`
*   `account`
*   `hr`

## Author and Website

This module was developed by:

*   **Author:** Secteur Network Solutions
*   **Website:** [http://www.secteurnetworks.com](http://www.secteurnetworks.com)

## Licensing

Odoo modules are typically licensed under the LGPL-3 (GNU Lesser General Public License v3).

It is recommended to include a `LICENSE` file in the root of the module directory detailing the specific license terms. For more information on Odoo licensing, please refer to the official Odoo documentation or the license text itself.
