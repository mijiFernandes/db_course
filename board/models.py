from django.db import models


class Entity(models.Model):
    table = models.FileField()

    def __str__(self):
        return self.table.__str__()
