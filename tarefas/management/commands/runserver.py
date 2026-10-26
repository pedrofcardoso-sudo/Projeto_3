from django.contrib.staticfiles.management.commands.runserver import (
    Command as StaticFilesRunserverCommand,
)


class Command(StaticFilesRunserverCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(addrport="127.0.0.1:8002")
