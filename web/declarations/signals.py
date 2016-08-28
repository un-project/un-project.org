from django.dispatch import Signal

added_declaration_for_resolution = Signal(providing_args=["declaration"])
added_declaration_for_declaration = Signal(providing_args=["declaration"])
reported_as_fallacy = Signal(providing_args=["report"])
supported_a_declaration = Signal(providing_args=["declaration", "user"])
