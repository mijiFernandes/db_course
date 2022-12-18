from django.db import models


class Table(models.Model):
    table_name = models.CharField(max_length=200)
    scan = models.BooleanField(default=False)
    key_list = models.TextField(null=True)
    records = models.IntegerField(null=True)
    attributes = models.TextField(null=True)

    def __str__(self):
        return self.table_name.__str__()
