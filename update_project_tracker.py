from src.services.project_status_service import ProjectStatusService


PROJECT_JOURNAL = """
============================================================
LTHHC AI AUTOMATION PLATFORM — DEVELOPMENT JOURNAL
============================================================

Last updated: 2026-07-31

Repository:
LTHHC-Josh/AI_Automation_Platform

Local project:
C:\\Projects\\LTHHC-AI-Automation-Platform

Development workflow:
1. Review repository files first.
2. Trace dependencies.
3. Understand the existing architecture.
4. Implement the feature.
5. Test the feature.
6. Update this project tracker.
7. Commit and push completed work to GitHub.

IMPORTANT DEVELOPMENT PREFERENCE:
Always provide complete file contents when code must be pasted.
Do not provide partial snippets that require indentation-sensitive edits.

------------------------------------------------------------
CURRENT ARCHITECTURE
------------------------------------------------------------

The platform currently contains:

- Provider-based OCR framework
- Provider-based LLM framework
- Document classification
- Structured data extraction
- Business-rules framework
- DocumentProcessor pipeline
- Smartsheet synchronization
- Microsoft Entra app registration
- Microsoft Graph shared-mailbox integration
- Microsoft Graph email attachment downloading

Current document-processing flow:

File
  -> OCR
  -> Classification
  -> Structured Extraction
  -> Business Rules
  -> Document Result

Current email-ingestion flow:

Microsoft Graph
  -> ai@lthhc.com shared mailbox
  -> Unread inbox messages
  -> Non-inline file attachments
  -> data/incoming

The next integration step is:

Downloaded attachment
  -> DocumentProcessor
  -> OCR
  -> Classification
  -> Extraction
  -> Business Rules

------------------------------------------------------------
MICROSOFT ENTRA AND GRAPH CONFIGURATION
------------------------------------------------------------

Microsoft Entra app registration has been created.

Shared mailbox:
ai@lthhc.com

Authentication method:
OAuth 2.0 client-credentials flow through MSAL.

Microsoft Graph scope:
https://graph.microsoft.com/.default

The following values are stored locally in the root .env file:

- GRAPH_TENANT_ID
- GRAPH_CLIENT_ID
- GRAPH_CLIENT_SECRET
- GRAPH_MAILBOX

GRAPH_MAILBOX is:

ai@lthhc.com

Secrets must never be committed to GitHub.

The root .gitignore must contain:

.env

The client secret must be the Entra client-secret VALUE, not the
client-secret ID.

------------------------------------------------------------
PYTHON DEPENDENCIES
------------------------------------------------------------

A requirements.txt file was created in the project root.

Required packages currently include:

- msal
- requests
- python-dotenv

Installation command:

python -m pip install -r requirements.txt

------------------------------------------------------------
MICROSOFT GRAPH FILES IMPLEMENTED
------------------------------------------------------------

src/graph/config.py

Responsibilities:

- Load .env with override=True
- Read Graph environment variables
- Strip surrounding whitespace
- Validate required Graph settings
- Raise a clear error when configuration is missing

src/graph/auth.py

Responsibilities:

- Create an MSAL ConfidentialClientApplication
- Use the Microsoft Entra tenant
- Use the registered application client ID
- Use the client-secret credential
- Acquire an application access token
- Raise a clear authentication error when token acquisition fails

src/graph/client.py

Responsibilities:

- Provide a reusable Microsoft Graph HTTP client
- Add the bearer token to requests
- Use Microsoft Graph v1.0
- Support GET requests
- Support POST requests
- Apply a 30-second timeout
- Raise errors for unsuccessful HTTP responses

src/graph/email_service.py

Responsibilities:

- Access the ai@lthhc.com inbox
- Retrieve unread messages
- Return message ID
- Return subject
- Return sender
- Return received date and time
- Return attachment status

src/graph/attachment_service.py

Responsibilities:

- Enumerate message attachments
- Accept Microsoft Graph fileAttachment objects
- Skip inline attachments such as email-signature images
- Sanitize filenames
- Decode Base64 attachment content
- Save files under data/incoming
- Return the downloaded file paths

------------------------------------------------------------
TEST SCRIPTS IMPLEMENTED
------------------------------------------------------------

scripts/test_graph_connection.py

Purpose:

- Authenticate with Microsoft Graph
- Read unread messages from ai@lthhc.com
- Print basic message information

Successful result:

Connecting to Microsoft Graph...
Connection successful. Found 0 unread message(s).

This confirmed:

- The .env file loaded correctly
- MSAL authentication succeeded
- The Entra client secret was valid
- Microsoft Graph permissions were valid
- The shared mailbox was accessible
- Unread messages could be enumerated

scripts/test_graph_attachments.py

Purpose:

- Retrieve unread messages
- Detect messages containing attachments
- Download valid file attachments
- Print downloaded paths

Initial test result:

- CAS-R6.pdf downloaded
- image001.png downloaded

The PNG was determined to be an inline image from the email signature.

attachment_service.py was updated to skip attachments when:

isInline is True

Retest result:

- CAS-R6.pdf downloaded
- image001.png skipped
- Total attachments downloaded: 1

This confirmed that normal file attachments download successfully while
inline signature graphics are ignored.

------------------------------------------------------------
DATA DIRECTORIES
------------------------------------------------------------

Downloaded mailbox attachments are saved under:

data/incoming

Successful test file:

data/incoming/CAS-R6.pdf

------------------------------------------------------------
CURRENT VERIFIED STATUS
------------------------------------------------------------

Completed and tested:

- Microsoft Entra app registration
- Client-secret authentication
- Shared mailbox creation
- Graph environment configuration
- Access-token acquisition
- Graph HTTP client
- Unread-message retrieval
- Attachment enumeration
- Attachment downloading
- Base64 decoding
- Filename sanitization
- Inline signature-image filtering
- Saving attachments under data/incoming

Current Office365 connector status:

Microsoft Graph authentication, mailbox access, unread-email retrieval,
and attachment downloading are operational.

------------------------------------------------------------
NEXT DEVELOPMENT STEP
------------------------------------------------------------

Integrate downloaded files with the existing DocumentProcessor.

The next implementation should:

1. Inspect the current DocumentProcessor interface.
2. Confirm which file types it supports.
3. Pass each downloaded supported attachment into DocumentProcessor.
4. Capture OCR, classification, extraction, and business-rule results.
5. Handle unsupported file types safely.
6. Avoid processing inline attachments.
7. Decide when a successfully processed email should be marked as read.
8. Prevent the same message or attachment from being processed repeatedly.
9. Add an end-to-end mailbox-processing test.
10. Update this tracker after testing succeeds.

Do not mark messages as read until document processing succeeds.

============================================================
"""


service = ProjectStatusService()
tasks = service.tasks


updates = [

    (
        "Design Solution Architecture",
        "Completed",
        (
            "Completed provider-based AI Automation Platform architecture "
            "including ProviderLoader, registries, factories, OCR, LLM, "
            "Business Rules, Microsoft Graph integration design, and "
            "Smartsheet synchronization."
        ),
    ),

    (
        "Define Integration Architecture",
        "Completed",
        (
            "Completed integration architecture for Microsoft Graph email "
            "ingestion followed by OCR, LLM classification, structured "
            "extraction, Business Rules, workflow processing, and Smartsheet "
            "synchronization."
        ),
    ),

    (
        "Design AI Pipeline",
        "Completed",
        (
            "Implemented interchangeable provider architecture using automatic "
            "provider discovery, registries, and factories."
        ),
    ),

    (
        "Configure Branch Strategy",
        "Completed",
        (
            "Git repository connected to GitHub and development workflow "
            "validated."
        ),
    ),

    (
        "Validate Development Environment",
        "Completed",
        (
            "Python virtual environment, VS Code, GitHub integration, "
            "requirements management, AI platform architecture, and testing "
            "environment validated."
        ),
    ),

    (
        "Create OCR Service",
        "Completed",
        (
            "Completed OCR provider framework with ProviderLoader, OCRRegistry, "
            "OCRFactory, provider registration, and mock OCR implementation."
        ),
    ),

    (
        "Extract PDF Text",
        "In Progress",
        (
            "OCR framework is complete. Microsoft Graph can now download PDF "
            "attachments into data/incoming. Production PDF OCR implementation "
            "and live document processing remain pending."
        ),
    ),

    (
        "Unit Test OCR",
        "Completed",
        (
            "OCR provider framework successfully validated using the mock "
            "provider."
        ),
    ),

    (
        "Create Prompt Templates",
        "In Progress",
        (
            "LLM provider framework is complete. Prompt engineering continues "
            "with production providers and real documents."
        ),
    ),

    (
        "Implement Classification",
        "Completed",
        (
            "Implemented document classification using the interchangeable LLM "
            "provider architecture."
        ),
    ),

    (
        "Implement Data Extraction",
        "Completed",
        (
            "Implemented structured extraction using the interchangeable LLM "
            "provider architecture."
        ),
    ),

    (
        "Validate AI Output",
        "Completed",
        (
            "Validated the complete AI processing pipeline using mock OCR and "
            "LLM providers."
        ),
    ),

    (
        "Implement Business Rules",
        "Completed",
        (
            "Implemented Rule abstraction, RuleRegistry, RuleFactory, "
            "ProviderLoader registration, RuleService, and AuthorizationRule."
        ),
    ),

    (
        "Validate Business Rules",
        "Completed",
        (
            "Successfully validated the OCR, LLM, classification, extraction, "
            "and Business Rules pipeline using end-to-end testing."
        ),
    ),

    (
        "Integration Testing",
        "In Progress",
        (
            "Validated the internal AI pipeline and Smartsheet synchronization. "
            "Microsoft Graph mailbox authentication and attachment downloading "
            "are also validated. Final email-to-DocumentProcessor integration "
            "testing remains pending."
        ),
    ),

    (
        "Configure Microsoft Entra",
        "Completed",
        (
            "Created the Microsoft Entra app registration, client secret, "
            "Microsoft Graph application permissions, and tenant admin consent. "
            "Live client-credentials authentication was successfully tested."
        ),
    ),

    (
        "Create Shared Mailbox",
        "Completed",
        (
            "Created ai@lthhc.com as the shared mailbox dedicated to the AI "
            "Automation Platform."
        ),
    ),

    (
        "Configure Mailbox Security",
        "Completed",
        (
            "Configured the shared mailbox to require authenticated senders "
            "during development."
        ),
    ),

    (
        "Validate Email Delivery",
        "Completed",
        (
            "Successfully delivered internal test email attachments to "
            "ai@lthhc.com and retrieved the test message through Microsoft Graph."
        ),
    ),

    (
        "Design Office365 Connector",
        "Completed",
        (
            "Completed the Microsoft Graph connector architecture under "
            "src/graph, including configuration, authentication, reusable Graph "
            "client, email service, and attachment service."
        ),
    ),

    (
        "Authenticate Microsoft Graph",
        "Completed",
        (
            "Successfully authenticated to Microsoft Graph using the Microsoft "
            "Entra app registration and OAuth client-credentials flow. Confirmed "
            "access to ai@lthhc.com and successfully enumerated unread inbox "
            "messages."
        ),
    ),

    (
        "Implement Office365 Connector",
        "In Progress",
        (
            "Implemented and tested Graph configuration loading, MSAL "
            "client-credentials authentication, reusable GraphClient requests, "
            "unread-message retrieval from ai@lthhc.com, file-attachment "
            "enumeration, Base64 decoding, secure filename handling, saving "
            "attachments under data/incoming, and filtering inline signature "
            "images through the isInline property. Live testing successfully "
            "downloaded CAS-R6.pdf while skipping image001.png. Next milestone: "
            "integrate downloaded supported attachments with DocumentProcessor, "
            "add successful-processing safeguards, and mark messages as read only "
            "after processing succeeds."
        ),
    ),

]


def print_project_journal() -> None:
    print(PROJECT_JOURNAL)


def synchronize_project_tracker() -> None:
    print()
    print("=" * 60)
    print("Synchronizing Project Tracker")
    print("=" * 60)
    print()

    updated = 0
    unchanged = 0
    not_found = 0
    failed = 0

    for task_name, status, comment in updates:

        try:

            task = tasks.find_task(task_name)

            if task is None:
                print(f"✗ Task not found: {task_name}")
                not_found += 1
                continue

            changed = tasks.sync_task(
                task=task,
                status=status,
                comment=comment,
            )

            if changed:
                updated += 1
                print(f"✓ Updated: {task_name}")

            else:
                unchanged += 1
                print(f"- No change: {task_name}")

        except Exception as ex:

            failed += 1

            print(f"✗ Failed: {task_name}")
            print(f"  {ex}")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Updated   : {updated}")
    print(f"Unchanged : {unchanged}")
    print(f"Not Found : {not_found}")
    print(f"Failed    : {failed}")
    print("=" * 60)


if __name__ == "__main__":
    print_project_journal()
    synchronize_project_tracker()