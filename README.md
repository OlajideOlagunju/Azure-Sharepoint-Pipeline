# Secure Multi-Tenant Data Pipeline | Microsoft Azure, Entra ID & DevOps

An end-to-end data pipeline solution to securely and automatically ingest data from external sources (SharePoint Online, Azure Blob Storage) into a central application. This project features a robust integration of Microsoft Azure services, emphasizing a security-first approach using Microsoft Entra ID for multi-tenant access and Azure DevOps for CI/CD orchestration.


# Business Case
Our application, requires regular data feeds from various external sources, including automated exports from SAP that are deposited into a SharePoint site. The key challenge is to create a single, automated pipeline that can securely access data from multiple, isolated tenant environments without hardcoding credentials or granting overly broad permissions. The solution must be auditable, reliable, and scalable to onboard new data sources with minimal friction.


# Technical Requirements

| Functional 🟢 | Non-Functional 🔵|
| ------------- | ------------- |
| The system shall automatically ingest CSV and Excel files from a designated SharePoint Online folder on a daily schedule. | The system shall use certificate-based authentication (no client secrets) for accessing SharePoint to adhere to security best practices. |
| The system shall be able to ingest files from Azure Blob Storage using a secure, time-bound access method. | Access to SharePoint shall be granted on a per-site basis (least-privilege), not tenant-wide, using Resource-Specific Consent. |
| The system shall provide a mechanism for file rotation, automatically deleting the oldest files to manage disk space on the agent machine. | All sensitive credentials (SAS tokens, certificate passwords) shall be stored securely and not exposed in logs or source code. |
| The pipeline shall be orchestrated and monitored through a centralized CI/CD platform (Azure DevOps). | The system shall be easily extensible to add new SharePoint sites or Blob Storage containers without major re-architecture. |
| The pipeline shall log its execution status, including successful downloads and any errors encountered during the process. | The setup process for a new tenant shall be well-documented to allow for repeatable and consistent onboarding. |


# Tools Used
Cloud Infrastructure - [Microsoft Azure](https://azure.microsoft.com/) ![Azure](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/Azure%20(1)%20(Custom).png)

CI/CD & Orchestration - [Azure DevOps](https://azure.microsoft.com/services/devops/) ![Azure DevOps](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/Azure%20Devops%20(Custom).png)

Identity & Access Management - [Microsoft Entra ID](https://www.microsoft.com/en-us/security/business/microsoft-entra) ![Entra ID](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/microsoft-entra-id-seeklogo%20(Custom).png)

Collaboration & Storage - [SharePoint Online](https://www.microsoft.com/en-us/microsoft-365/sharepoint/collaboration) ![SharePoint](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/Sharepoint%20(Custom).png)

Bulk Storage - [Azure Blob Storage](https://azure.microsoft.com/en-us/services/storage/blobs/) ![Blob Storage](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/icons8-azure-storage-blob-48%20(Custom).png)

Scripting - [Python](https://www.python.org/) ![Python](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/Python%20(Custom).png) & [PowerShell](https://learn.microsoft.com/en-us/powershell/) ![PowerShell](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/Powershell%20(Custom).png)


# High-Level Architecture
The solution is comprised of two distinct but complementary data ingestion workflows, both orchestrated by a central Azure DevOps pipeline.

![architecture](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/architecture.png)

### Architecture Choices

- **Azure DevOps** was chosen for its native integration with the Azure ecosystem and its robust CI/CD capabilities, allowing for both orchestration and version control in a single platform. It provides excellent tools for managing secret variables, ensuring credentials are not exposed.
- **Microsoft Entra ID** is the cornerstone of the security model. By using App Registrations and certificate-based authentication, we eliminate long-lived secrets and create a secure, auditable access trail.
- **Python** was selected for scripting due to its powerful libraries for making API requests (`requests`) and handling cryptographic operations (`cryptography`), making it ideal for interacting with the Microsoft Graph API.
- **PowerShell** (specifically the PnP module) is used for the one-time setup of SharePoint permissions, as it provides the necessary cmdlets to grant site-level access to an Entra ID application, which is a critical security feature.
- **Azure VM with a Self-Hosted Agent** provides a stable, controlled environment to execute the scripts, manage file storage, and ensure consistent network access to the required resources.


# The Source Datasets
The pipeline is designed to ingest data from two primary sources:

1.  **SharePoint Online:** CSV or XLSX files automatically exported from a source system like SAP and deposited into a specific document library folder (e.g., `/sites/ClientSite/Shared Documents/SAP_Exports`).
2.  **Azure Blob Storage:** A single, consolidated CSV file stored in an Azure Blob container, accessible via a URL and a secure SAS token.


# Authentication & Security Model

Instead of a traditional database schema, this project's core complexity lies in its security model.
- **For SharePoint (Certificate-Based Auth):** This is the most secure method.
    1.  An **Entra ID App Registration** acts as the service principal (the "identity") for the pipeline.
    2.  A **self-signed x.509 certificate** is used for authentication. The public key is uploaded to Entra ID, while the private key is securely stored (e.g., in Azure Key Vault or accessible to the agent) and used by the Python script to sign a JWT assertion.
    3.  **Microsoft Graph API** permissions are set to `Sites.Selected`, which means the app has no access by default. Access must be explicitly granted to each SharePoint site via a PowerShell script. This enforces the **principle of least privilege**.

- **For Azure Blob (SAS Token Auth):** This method is used for simpler, direct access.
    1.  A **Shared Access Signature (SAS) token** is generated for the specific blob.
    2.  This token grants temporary, read-only access and has a defined expiry date.
    3.  The SAS token is stored as a **secret variable** in Azure DevOps and passed to the script at runtime, avoiding any exposure in the source code.


# Azure Configuration & Pipeline Setup

## Step 1: Configure Entra ID for SharePoint Access

This one-time setup grants the pipeline secure, site-specific access.

1. **Register an App in Entra ID:**
    - In the Entra portal, create a new **App Registration**.
    - Note the `Application (client) ID` and `Directory (tenant) ID`.

2. **Assign API Permissions:**
    - In the app, go to **API permissions** and grant `Application` permissions for `Sites.Selected` under both **Microsoft Graph** and **SharePoint**.
    - Grant admin consent for the permissions.

3. **Create and Upload a Certificate:**
    Microsoft Entra ID supports two types of authentication for service principals: password-based authentication (app secret) and certificate-based authentication. While app secrets can easily be created in the Azure portal or using a Microsoft API like Microsoft Graph, they're long-lived, and not as secure as certificates. It's therefore recommended that applications use certificates rather than secrets. To create a certificate, first make sure to install the latest PowerShell version from Microsoft. Run PowerShell as an Admin User on your local machine, then run the code below in PowerShell to create a Public Certificate and Private Key that will be stored on your local machine. Note the Password you have set for the Certificate. 
    - Use PowerShell to generate a `.cer` (public key) and `.pfx` (private key) file.

                $certname = "SharePoint_Cert" ## Choose a Certificate Name 
                $cert = New-SelfSignedCertificate -Subject "CN=$certname" -CertStoreLocation 
                "Cert:\CurrentUser\My" -KeyExportPolicy Exportable -KeySpec Signature -KeyLength 2048 -KeyAlgorithm RSA -HashAlgorithm SHA256

                Export-Certificate -Cert $cert -FilePath "C:\$certname.cer" ## Specify your preferred location to export certificate to
                $mypwd = ConvertTo-SecureString -String "DummyPassword" -Force -AsPlainText ## Replace 'DummyPassword' with a secure Certificate Password of your choice

                Export-PfxCertificate -Cert $cert -FilePath "C:\$certname.pfx" -Password $mypwd  ## Specify your preferred location        
    
    - Upload the `.cer` file to the **Certificates & secrets** section of your Entra app.
    - Securely store the `.pfx` file and its password, as they will be needed by the Python script.

5. **Grant Site-Level Permissions:**
    - Using the `PnP.PowerShell` module, connect to your SharePoint site and run the `Grant-PnPAzureADAppSitePermission` cmdlet to give your app `Read` access to that specific site only. First install the SharePoint and PnP.PowerShell modules in PowerShell using the code below:
  
                Install-Module SharePointPnPPowerShellOnline
                Install-Module -Name PnP.PowerShell -Scope CurrentUser -AllowClobber -Force 

    - Run the code to register a new App. Make sure to change the tenant to your SharePoint Tenant. This also runs in interactive mode, so you‘ll need to sign in as seen in the next step. Afterwards, we’ll use the temporary app (which by default has ‘FullControl’ rights to all SharePoint Sites) to connect to the specified SharePoint site using the ClientID we just created. You’ll be required to sign in like the previous step; once signed in, you will be connected to the SharePoint site. `

                Register-PnPEntraIDAppForInteractiveLogin -ApplicationName "PnP_PowerShell" -Tenant workplace.onmicrosoft.com -Interactive ## Replace 'workplace' with relevant tenant and 'PnP_PowerShell' with preferred name for Temporary App.

                Connect-PnPOnline -Url "https://workplace.sharepoint.com/sites/TargetSite" -Interactive -ClientId cd33e75f-dummy-client-id-80fwe4b41a4f ## Replace ClientID value with ClientID from the previous step. 

                 Grant-PnPAzureADAppSitePermission -AppId "another-dummy-client-id-80fwe4b41a4e" DisplayName "SharePoint_Permissions" -Permissions Read -Site "https://workplace.sharepoint.com/sites/TargetSite"

                $siteUrl = "https://workplace.sharepoint.com/sites/TargetSite"
                $clientId = "another-dummy-client-id-80fwe4b41a4e" ## Replace ClientID value with 'Application (client) ID' of SharePoint App 
                $tenant = "workplace.onmicrosoft.com"
                
                Connect-PnPOnline -Url $siteUrl -ClientId $clientId -Tenant $tenant -CertificatePath "C:\SharePoint_Cert.pfx" -CertificatePassword (ConvertTo-SecureString "DummyPassword" -AsPlainText -Force) ## Replace CertificatePath value with path to the certificate (.cer file) on your local machine. Also replace the 'DummyPassword' with the password of the certificate

    - Check the connection is good using:
                Get-PnPConnection 
![pnp1](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/pnp.png)


    - You can also check that you can access the documents using this app in the Site you specified:
                Get-PnPListItem -List "Documents"
![pnp2](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/pnp1.png)

    
   
## Step 2: Configure Azure Blob Storage Access

1. **Identify Blob Details:** Note your storage account URL, container name, and blob name.
2. **Generate SAS Token:** In the storage account settings, generate a SAS token with `Read` permissions and an appropriate expiry date.

## Step 3: Set up the Azure DevOps Pipeline

The pipeline orchestrates the entire process.

1. **Create a Self-Hosted Agent Pool:** Set up a VM in Azure and install the Azure DevOps self-hosted agent on it. This agent will run the scripts.
2. **Create the Pipeline from YAML:** Use the provided `SharePoint_Blob_File_Download_Pipeline.yml` YAML file. This file defines the steps to install dependencies and run the Python scripts.
3. **Configure Secret Variables:**
- In the pipeline settings in Azure DevOps, create a variable group or add secret variables directly.
- Store the `SAS_TOKEN` and the `SP_CERT_PASSWORD` here. Check the "Keep this value secret" box.


# Pipeline Execution & Scripts
The Azure DevOps pipeline runs the core logic contained in the Python scripts.

### Azure Blob Storage Workflow
The pipeline triggers the `blob_download_and_rotate_files.py` script.

- **Extraction:** The script receives the Blob URL, name, and SAS token as environment variables. It makes a `requests.get()` call to the blob URL to download the file content.
- **Loading:** The file is saved to a local directory on the agent machine (e.g., `C:\VM_Folder`).
- **File Rotation (Transformation):** The script then scans the directory, counts the number of existing files, and deletes the oldest ones if the count exceeds a defined maximum (`MAX_FILES`), preventing disk space from filling up.

### SharePoint Workflow
The pipeline can be adapted to trigger the `sharepoint_downloader.py` script.

- **Authentication:** The script first loads the `.pfx` private key. It uses this key to create and sign a JSON Web Token (JWT).
- **Token Exchange:** It sends this JWT to the Microsoft identity platform token endpoint to request an OAuth2 access token for the Microsoft Graph API.
- **Extraction:** Using the access token, the script makes authenticated calls to the Graph API to list the files in the designated SharePoint folder and then downloads each file.
- **Loading:** The files are saved to a local directory on the agent machine for downstream processing.


# Scheduling Pipeline Runs
The pipeline can be configured to run automatically on a schedule.

1.  In the Azure DevOps portal, navigate to your pipeline and select **Edit**.
2.  Click the three dots and select **Triggers**.
3.  Go to the **Scheduled** tab and create a new trigger to run daily at a specified time.

![scheduled](https://github.com/OlajideOlagunju/Azure-Sharepoint-Pipeline/blob/main/images/scheduled.png)


# Conclusion
This project successfully establishes a secure, robust, and automated data pipeline within the Microsoft Azure ecosystem. By leveraging best practices for authentication and access control with Entra ID, the solution meets the client's critical need for multi-tenant data ingestion without compromising on security. The orchestration via Azure DevOps ensures the entire process is reliable, repeatable, and easy to monitor, providing a solid foundation for future data integration needs.
