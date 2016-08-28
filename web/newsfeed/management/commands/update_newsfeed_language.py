from django.core.management import BaseCommand
from declarations.models import Resolution, Declaration
from newsfeed.models import Entry
from newsfeed.constants import (
    NEWS_TYPE_RESOLUTION, NEWS_TYPE_DECLARATION,
    NEWS_TYPE_FALLACY, NEWS_TYPE_FOLLOWING)

RELATED_MODELS = {
    NEWS_TYPE_RESOLUTION: Resolution,
    NEWS_TYPE_DECLARATION: Declaration,
}


class Command(BaseCommand):

    def handle(self, *args, **options):
		entries = Entry.objects.collection.find({
		    "news_type": {
		        "$in": [NEWS_TYPE_RESOLUTION,
		                NEWS_TYPE_DECLARATION]
		    }
		})

		for entry in entries:
   			model = RELATED_MODELS[entry['news_type']]
			try:
				instance = model.objects.get(id=entry['object_id'])
			except model.DoesNotExist:
				continue

			Entry.objects.collection.update({
				'_id': entry['_id']
			}, {
				"$set": {
					"related_object": instance.get_newsfeed_bundle()
				}
			}, multi=True)



