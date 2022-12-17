from django.db import models


class Table(models.Model):
    table_name = models.CharField(max_length=190)
    scan = models.BooleanField(default=False)
    def __str__(self):
        return self.table_name.__str__()
