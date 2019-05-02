from django.core.management import BaseCommand

from declarations.models import Resolution, Declaration, Report


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        reports = Report.objects.filter(resolution__language="en")

        fallacies = []

        for report in reports:
            if report.report_type and report.declaration:
                fallacies.append(
                    {
                        "declaration": report.declaration.text,
                        "declaration_type": report.declaration.declaration_class(),
                        "fallacy_type": report.fallacy_type,
                    }
                )

        json.dump(open("fallacies.json", "w"))
