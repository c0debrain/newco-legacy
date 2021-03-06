from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet

from affiliation import CURRENCIES

# Static data. Probably shouldn't be in the DB
STORES = {
    "Amazon": {
        "name": "Amazon",
        "url": "http://www.amazon.fr",
        "affiliated_url": "http://www.amazon.fr/?_encoding=UTF8&"
                          "tag=ne002-21&linkCode=ur2&camp=1642&"
                          "creative=6746"},
    "Decathlon": {
        "name": "Decathlon",
        "url": "http://www.decathlon.fr",
        "affiliated_url": "http://action.metaffiliation.com/suivi.php?"
                          "mclic=S3CE1545AF917&"
                          "redir=http://www.decathlon.fr/"},
}


class StoreManager(models.Manager):
    def get_store(self, store_name):
        if store_name not in STORES:
            return None
        store_entry = STORES.get(store_name)
        try:
            store = self.get(name=store_name)
            if store.url != store_entry["url"] or \
                    store.affiliated_url != store_entry["affiliated_url"]:
                store.url = store_entry["url"]
                store.affiliated_url = store_entry["affiliated_url"]
                store.save()
        except ObjectDoesNotExist:
            store, created = self.get_or_create(**store_entry)
        return store


class AffiliationItemQuerySet(QuerySet):
    def get_cheapest(self, currency):
        if currency not in CURRENCIES._choice_dict.values():
            return None
        cheapest_product = None
        products = self.values("currency").annotate(price=models.Min("price"))
        for product in products:
            if product["currency"] == currency:
                cheapest_product = product
                break
        return cheapest_product


class AffiliationItemManager(models.Manager):
    def get_query_set(self):
        return AffiliationItemQuerySet(self.model)

    def get_cheapest(self, currency):
        return self.get_query_set().get_cheapest(currency)
