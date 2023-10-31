from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=200)
    alpha2code = models.CharField(max_length=100)
    alpha3code = models.CharField(max_length=100, null=True)
    currency_name = models.CharField(max_length=200, null=True, blank=True)
    currency_code = models.CharField(max_length=200, null=True, blank=True)
    currency_symbol = models.CharField(max_length=200, null=True, blank=True)
    calling_code = models.CharField(max_length=200, null=True,)
    flag_link = models.CharField(max_length=300, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    def __str__(self):
        return str("{}").format(self.name)

    class Meta:
        verbose_name_plural = 'Countries'
        ordering = ('name',)


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200, null=True, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return str("{} - {}").format(self.name, self.country)

    class Meta:
        verbose_name_plural = 'States'
        ordering = ('name',)


class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=200, null=True, blank=True)
    image = models.ImageField(upload_to='location-images/cities', blank=True, null=True)
    longitude = models.CharField(max_length=300, blank=True, null=True)
    latitude = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return str("{} - {}").format(self.name, self.state)

    class Meta:
        verbose_name_plural = 'Cities'
        ordering = ('name',)
