from django.core.management import BaseCommand
from unidecode import unidecode

from declarations.models import Report, get_fallacy_types, Declaration, Resolution

import networkx as nx

graph = nx.Graph()


class Command(BaseCommand):
    def normalize(self, value):
        return value.replace('"', "").rstrip(",")

    def handle(self, *args, **kwargs):
        self.create_conjunction_graph()

    def create_conjunction_graph(self):
        fallacy_map = {unidecode(key): value for (key, value) in get_fallacy_types()}
        for resolution in Resolution.objects.all():
            for declaration in resolution.declarations.all():
                fallacies = filter(
                    None, declaration.reports.values_list("fallacy_type", flat=True)
                )
                fallacies = [fallacy_map[unidecode(_f)] for _f in fallacies]
                fallacies_set = set(fallacies)
                for fallacy in fallacies_set:
                    graph.add_edges_from(
                        [
                            (
                                unidecode(self.normalize(fallacy)),
                                unidecode(self.normalize(_f)),
                            )
                            for _f in fallacies_set
                            if _f != fallacy
                        ]
                    )

        nx.write_gml(graph, "conjunction.gml")

    def create_report_graph(self):
        for (fallacy_type, localized) in get_fallacy_types():
            node = unidecode(self.normalize(localized))

            graph.add_node(node, type="fallacy", Weight=10)

            for declaration in Declaration.objects.filter(
                reports__fallacy_type=fallacy_type
            ):

                # graph.add_node(declaration.resolution.pk, type="resolution")

                # graph.add_edge(declaration.resolution.pk, node, type="reported")

                if declaration.resolution.channel:
                    channel_node = unidecode(declaration.resolution.channel.title)

                    graph.add_node(
                        channel_node,
                        type="channel",
                        Weight=declaration.resolution.channel.resolutions.count() * 30,
                    )
                    graph.add_edge(channel_node, node, type="reported")

        nx.write_gml(graph, "reports.gml")
