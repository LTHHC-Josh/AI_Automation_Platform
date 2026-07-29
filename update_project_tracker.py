from src.services.project_status_service import ProjectStatusService


service = ProjectStatusService()
tasks = service.tasks


updates = [

    (
        "Design Solution Architecture",
        "Completed",
        "Completed provider-based AI Automation Platform architecture including ProviderLoader, registries, factories, OCR, LLM, Business Rules, Office365 connector design, and Smartsheet synchronization.",
    ),

    (
        "Define Integration Architecture",
        "Completed",
        "Completed architecture for OCR → LLM → Business Rules → Workflow with Microsoft Graph, Office365 connector, and Smartsheet integration.",
    ),

    (
        "Design AI Pipeline",
        "Completed",
        "Implemented interchangeable provider architecture using automatic provider discovery, registries, and factories.",
    ),

    (
        "Configure Branch Strategy",
        "Completed",
        "Git repository connected to GitHub and development workflow validated.",
    ),

    (
        "Validate Development Environment",
        "Completed",
        "Python virtual environment, VS Code, GitHub integration, AI platform architecture, and testing environment validated.",
    ),

    (
        "Create OCR Service",
        "Completed",
        "Completed OCR provider framework with ProviderLoader, OCRRegistry, OCRFactory, provider registration, and mock OCR implementation.",
    ),

    (
        "Extract PDF Text",
        "In Progress",
        "OCR pipeline complete. Awaiting production PaddleOCR implementation.",
    ),

    (
        "Unit Test OCR",
        "Completed",
        "OCR provider framework successfully validated using mock provider.",
    ),

    (
        "Create Prompt Templates",
        "In Progress",
        "LLM provider framework complete. Prompt engineering continues with production providers.",
    ),

    (
        "Implement Classification",
        "Completed",
        "Implemented document classification using interchangeable LLM provider architecture.",
    ),

    (
        "Implement Data Extraction",
        "Completed",
        "Implemented structured extraction framework using interchangeable LLM providers.",
    ),

    (
        "Validate AI Output",
        "Completed",
        "Validated complete AI processing pipeline using mock OCR and LLM providers.",
    ),

    (
        "Implement Business Rules",
        "Completed",
        "Implemented Rule abstraction, RuleRegistry, RuleFactory, ProviderLoader registration, RuleService, and AuthorizationRule.",
    ),

    (
        "Validate Business Rules",
        "Completed",
        "Successfully validated OCR → LLM → Classification → Business Rules pipeline using end-to-end testing.",
    ),

    (
        "Integration Testing",
        "Completed",
        "Validated complete AI Automation Platform pipeline and verified Smartsheet synchronization.",
    ),

    (
        "Configure Microsoft Entra",
        "Completed",
        "Created Microsoft Entra App Registration, Client Secret, Microsoft Graph Application permissions, and granted tenant admin consent.",
    ),

    (
        "Create Shared Mailbox",
        "Completed",
        "Created ai@lthhc.com shared mailbox dedicated to the AI Automation Platform.",
    ),

    (
        "Configure Mailbox Security",
        "Completed",
        "Configured shared mailbox to require authenticated senders during development.",
    ),

    (
        "Validate Email Delivery",
        "Completed",
        "Successfully delivered internal test email with Excel attachment to ai@lthhc.com shared mailbox.",
    ),

    (
        "Design Office365 Connector",
        "Completed",
        "Completed connector architecture under src/connectors/office365 including authentication, Graph client, email service, attachment service, and configuration modules.",
    ),

    (
        "Implement Office365 Connector",
        "In Progress",
        "Next milestone: authenticate to Microsoft Graph, read ai@lthhc.com shared mailbox, enumerate unread messages, download attachments, and integrate with DocumentProcessor.",
    ),

]


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